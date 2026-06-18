import csv
import json

import pytest

from app.rag.evaluators.testset_generation import (
    ReviewImportValidationError,
    TestsetGenerationError,
    build_reviewed_import_payload,
    chunks_from_json,
    chunks_to_internal_documents,
    generate_case_drafts,
    generate_case_drafts_by_mode,
    write_import_json,
    write_review_csv,
)
from app.schemas.ingest import ChunkRecord


DOC_ID = "33333333-3333-3333-3333-333333333333"
KB_ID = "44444444-4444-4444-4444-444444444444"
EXPERIMENT_ID = "55555555-5555-5555-5555-555555555555"
CHUNK_A = "11111111-1111-1111-1111-111111111111"
CHUNK_B = "22222222-2222-2222-2222-222222222222"


def test_generate_case_drafts_from_document_chunks() -> None:
    chunks = [
        _chunk(
            CHUNK_A,
            index=1,
            title="售后故障排查",
            content=(
                "设备无法联网时，先确认电源、网线和指示灯状态。"
                "如果链路正常，再检查 DHCP 获取地址和 DNS 配置。"
                "仍失败时需要收集日志并升级到二线支持。"
                "现场工程师还应记录客户网络拓扑、交换机端口、固件版本和最近一次配置变更，"
                "避免只凭单一错误码判断根因。"
            ),
            metadata={"quality_score": 0.9, "section_title": "网络故障排查"},
        ),
        _chunk(
            CHUNK_B,
            index=2,
            title="售后故障排查",
            content=(
                "补充证据：升级工单需要包含客户编号、设备序列号、错误码和最近一次操作时间。"
                "如果客户现场已经尝试重启或更换网线，也需要记录操作人、操作时间和结果，"
                "方便二线支持复盘链路状态。"
            ),
            metadata={"quality_score": 0.8},
        ),
        _chunk(
            "66666666-6666-6666-6666-666666666666",
            index=0,
            title="父块",
            content="父块不应该进入自动测评样本。",
            metadata={"chunk_level": "parent"},
        ),
    ]

    drafts = generate_case_drafts(chunks, cases_per_document=2)

    assert len(drafts) == 2
    primary = drafts[0]
    assert primary.status == "DRAFT"
    assert primary.review_status == "待审核"
    assert primary.required_chunk_ids == [CHUNK_A]
    assert primary.citation_chunk_ids == [CHUNK_A]
    assert primary.relevant_document_ids == [DOC_ID]
    assert "网络故障排查" in primary.question
    assert "设备无法联网" in primary.expected_answer
    assert "人工确认" in primary.notes
    assert primary.evidence_preview.startswith("设备无法联网")


def test_write_import_json_and_review_csv(tmp_path) -> None:
    drafts = generate_case_drafts(
        [
            _chunk(
                CHUNK_A,
                index=1,
                title="售后 SLA",
                content=(
                    "P1 故障需要 15 分钟内响应，30 分钟内给出临时绕行方案，并持续同步处理进度。"
                    "如果故障影响核心生产链路，值班工程师需要同步客户成功经理和二线专家，"
                    "在工单中记录影响范围、当前恢复动作、下一次更新时间和风险说明。"
                ),
            )
        ]
    )
    output_json = tmp_path / "draft-cases.json"
    review_csv = tmp_path / "draft-review.csv"

    write_import_json(drafts, output_json, experiment_id=EXPERIMENT_ID)
    write_review_csv(drafts, review_csv)

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    csv_text = review_csv.read_text(encoding="utf-8-sig")
    assert payload["experimentId"] == EXPERIMENT_ID
    assert payload["items"][0]["status"] == "DRAFT"
    assert "reviewStatus" not in payload["items"][0]
    assert "confidence" not in payload["items"][0]
    assert "humanDecision" in csv_text
    assert "evidencePreview" in csv_text
    assert "P1 故障" in csv_text


def test_chunks_to_internal_documents_preserves_chunk_metadata() -> None:
    chunks = [
        _chunk(
            CHUNK_A,
            index=3,
            title="升级证据",
            content=(
                "升级到二线前必须记录客户编号、设备序列号、错误码、影响范围和已执行的排查动作。"
                "如果现场已经尝试重启或更换网线，也要写入操作时间、操作人和结果。"
                "这些信息可以帮助二线支持快速复盘链路状态，减少重复追问，并确认是否存在批量影响。"
            ),
            metadata={"section_title": "升级条件", "quality_score": 0.86},
        ),
        _chunk(
            "66666666-6666-6666-6666-666666666666",
            content="父块不进入 Testset 文档对象。",
            metadata={"chunk_level": "parent"},
        ),
    ]

    documents = chunks_to_internal_documents(chunks)

    assert len(documents) == 1
    assert documents[0].page_content.startswith("升级到二线前")
    assert documents[0].metadata["chunk_id"] == CHUNK_A
    assert documents[0].metadata["document_id"] == DOC_ID
    assert documents[0].metadata["title"] == "升级条件"


def test_ragas_mode_falls_back_when_optional_dependency_missing(monkeypatch) -> None:
    def _missing_ragas(*args, **kwargs):
        raise TestsetGenerationError("RAGAS TestsetGenerator requires an isolated environment.")

    monkeypatch.setattr(
        "app.rag.evaluators.testset_generation.generate_case_drafts_with_ragas",
        _missing_ragas,
    )

    result = generate_case_drafts_by_mode(
        [
            _chunk(
                CHUNK_A,
                content=(
                    "客户设备无法联网时，售后工程师先确认物理链路，再检查 DHCP、DNS 和网关配置。"
                    "如果仍无法恢复，需要收集日志、错误码、设备序列号和现场操作记录后升级二线。"
                    "同时要记录客户网络拓扑、交换机端口、固件版本和最近配置变更，避免遗漏环境因素。"
                ),
            )
        ],
        mode="ragas",
        fallback_to_rules=True,
    )

    assert result.fallback_used is True
    assert result.mode == "rule"
    assert "RAGAS TestsetGenerator" in result.warnings[0]
    assert result.drafts[0].generator_mode == "rule"


def test_ragas_mode_reports_error_without_fallback(monkeypatch) -> None:
    def _missing_ragas(*args, **kwargs):
        raise TestsetGenerationError("RAGAS TestsetGenerator requires an isolated environment.")

    monkeypatch.setattr(
        "app.rag.evaluators.testset_generation.generate_case_drafts_with_ragas",
        _missing_ragas,
    )

    with pytest.raises(TestsetGenerationError) as exc_info:
        generate_case_drafts_by_mode(
            [
                _chunk(
                    CHUNK_A,
                    content=(
                        "关闭工单前需要确认客户业务恢复、风险说明已经同步，并记录关键日志、处理过程和后续预防建议。"
                        "如果仍有未完成动作，应保留下一次更新时间和责任人。"
                    ),
                )
            ],
            mode="ragas",
            fallback_to_rules=False,
        )

    assert "RAGAS TestsetGenerator" in str(exc_info.value)


def test_llm_generation_maps_output_to_import_schema_and_review_metadata() -> None:
    llm = _FakeLLM(
        [
            {
                "caseId": "llm-network-escalation",
                "question": "客户设备无法联网且 DHCP 正常时，下一步应如何排查并升级？",
                "expectedAnswer": "应继续检查 DNS 和网关配置；仍失败时收集日志、错误码、设备序列号和现场操作记录后升级二线。",
                "requiredChunkIds": [CHUNK_A],
                "supportingChunkIds": [CHUNK_B],
                "citationChunkIds": [CHUNK_A],
                "questionType": "reasoning",
                "difficulty": "hard",
                "metadata": {"confidence": 0.88, "scenario": "售后网络排障"},
            }
        ]
    )

    result = generate_case_drafts_by_mode(
        _llm_chunks(),
        mode="llm",
        llm=llm,
        model_name="fake-llm",
        cases_per_document=1,
        top_k=7,
    )

    assert result.mode == "llm"
    assert result.fallback_used is False
    assert len(result.drafts) == 1
    draft = result.drafts[0]
    assert draft.case_id == "llm-network-escalation"
    assert draft.required_chunk_ids == [CHUNK_A]
    assert draft.supporting_chunk_ids == [CHUNK_B]
    assert draft.relevant_chunk_ids == [CHUNK_A, CHUNK_B]
    assert draft.evaluation_top_k == 7
    assert draft.question_type == "reasoning"
    assert draft.generator_mode == "llm"
    assert draft.metadata["scenario"] == "售后网络排障"
    assert draft.confidence == 0.88

    import_item = draft.to_import_item()
    assert "questionType" not in import_item
    assert "metadata" not in import_item
    assert import_item["requiredChunkIds"] == [CHUNK_A]

    review_row = draft.to_review_row()
    assert review_row["questionType"] == "reasoning"
    assert review_row["generatorMode"] == "llm"
    assert "售后网络排障" in review_row["metadata"]


def test_llm_generation_preserves_multiple_question_type_metadata() -> None:
    llm = _FakeLLM(
        [
            {
                "question": "售后工程师为什么不能只凭单一错误码判断网络故障根因？",
                "expectedAnswer": "因为还需要结合网络拓扑、交换机端口、固件版本和最近配置变更，避免遗漏环境因素。",
                "requiredChunkIds": [CHUNK_A],
                "metadata": {"question_type": "reasoning", "confidence": 0.81},
            },
            {
                "question": "升级工单时哪些现场信息和客户操作记录需要一起提交？",
                "expectedAnswer": "需要提交客户编号、设备序列号、错误码、最近一次操作时间，以及重启或更换网线的操作人、时间和结果。",
                "metadata": {
                    "question_type": "multi_context",
                    "required_chunk_ids": [CHUNK_A],
                    "supporting_chunk_ids": [CHUNK_B],
                    "confidence": 0.9,
                },
            },
        ]
    )

    result = generate_case_drafts_by_mode(
        _llm_chunks(),
        mode="llm",
        llm=llm,
        model_name="fake-llm",
        cases_per_document=2,
    )

    assert [draft.question_type for draft in result.drafts] == ["reasoning", "multi_context"]
    assert result.drafts[1].required_chunk_ids == [CHUNK_A]
    assert result.drafts[1].supporting_chunk_ids == [CHUNK_B]
    assert result.drafts[1].metadata["question_type"] == "multi_context"


def test_finalize_review_csv_builds_backend_import_payload(tmp_path) -> None:
    drafts = generate_case_drafts(
        [
            _chunk(
                CHUNK_A,
                index=1,
                title="网络故障处理",
                content=(
                    "设备无法联网时，售后工程师应先确认物理链路，再检查 DHCP、DNS 和网关配置。"
                    "如果仍无法恢复，需要收集日志、错误码、设备序列号和现场操作记录，"
                    "并将工单升级到二线支持。"
                ),
            ),
            _chunk(
                CHUNK_B,
                index=2,
                title="网络故障处理",
                content=(
                    "当客户反馈 intermittent 断连时，应记录故障发生时间、影响范围和最近配置变更。"
                    "如果问题具有批量影响，需要同步客户成功经理，并在下一次更新前给出临时规避建议。"
                ),
            ),
        ]
    )
    draft_json = tmp_path / "draft.json"
    review_csv = tmp_path / "review.csv"
    output_json = tmp_path / "final.json"
    write_import_json(drafts, draft_json)
    write_review_csv(drafts, review_csv)

    rows = _read_csv(review_csv)
    rows[0]["humanDecision"] = "通过"
    rows[0]["question"] = "客户设备无法联网时，售后工程师应如何处理？"
    rows[0]["expectedAnswer"] = "先确认物理链路，再检查 DHCP、DNS 和网关配置；仍无法恢复时收集日志并升级二线。"
    rows[0]["supportingChunkIds"] = ""
    rows[0]["humanNotes"] = "已核对证据，适合作为售后技术支持基准题。"
    rows[1]["humanDecision"] = "拒绝"
    rows[1]["humanNotes"] = "问题过宽，暂不启用。"
    _write_csv(review_csv, rows)

    result = build_reviewed_import_payload(
        draft_json_path=draft_json,
        review_csv_path=review_csv,
        experiment_id=EXPERIMENT_ID,
    )
    output_json.write_text(json.dumps(result.payload, ensure_ascii=False), encoding="utf-8")

    assert result.counts["ACTIVE"] == 1
    assert result.counts["REJECTED"] == 1
    assert result.payload["experimentId"] == EXPERIMENT_ID
    assert len(result.payload["items"]) == 2
    active_item = result.payload["items"][0]
    assert active_item["status"] == "ACTIVE"
    assert active_item["question"] == "客户设备无法联网时，售后工程师应如何处理？"
    assert active_item["expectedAnswer"].startswith("先确认物理链路")
    assert active_item["requiredChunkIds"] == [CHUNK_A]
    assert active_item["supportingChunkIds"] == []
    assert "人工审核备注" in active_item["notes"]
    assert "reviewStatus" not in active_item
    assert "confidence" not in active_item


def test_finalize_review_csv_can_export_active_only(tmp_path) -> None:
    drafts = generate_case_drafts(
        [
            _chunk(
                CHUNK_A,
                content=(
                    "工单升级前需要确认客户编号、设备序列号、错误码、影响范围和已执行的排查动作。"
                    "这些信息可以帮助二线支持快速复现问题，并减少重复沟通成本。"
                    "如果客户已经尝试重启、替换线缆或回滚配置，也要记录操作人、操作时间、"
                    "现场结果和仍然存在的异常现象，避免二线重复追问。"
                ),
            ),
            _chunk(
                CHUNK_B,
                index=1,
                content=(
                    "待补充内容只描述背景，不包含可验证的处理步骤，因此审核时应保持草稿状态。"
                    "后续需要人工补全问题、标准答案和证据片段后再启用，并补充故障现象、"
                    "临时规避方案、责任边界和升级条件，确保它能作为可执行的售后支持样本。"
                ),
            ),
        ],
        cases_per_document=2,
    )
    assert len(drafts) == 2
    draft_json = tmp_path / "draft.json"
    review_csv = tmp_path / "review.csv"
    write_import_json(drafts, draft_json)
    write_review_csv(drafts, review_csv)
    rows = _read_csv(review_csv)
    rows[0]["reviewStatus"] = "通过"
    rows[1]["humanDecision"] = "待审"
    _write_csv(review_csv, rows)

    result = build_reviewed_import_payload(
        draft_json_path=draft_json,
        review_csv_path=review_csv,
        experiment_id=EXPERIMENT_ID,
        active_only=True,
    )

    assert len(result.payload["items"]) == 1
    assert result.payload["items"][0]["status"] == "ACTIVE"
    assert result.counts["ACTIVE"] == 1
    assert result.counts["SKIPPED"] == 1
    assert result.skipped_case_ids == [rows[1]["caseId"]]


def test_finalize_review_csv_warns_about_unknown_human_decision(tmp_path) -> None:
    drafts = generate_case_drafts(
        [
            _chunk(
                CHUNK_A,
                content=(
                    "审核人员可能填写非标准决策词，例如确认、暂缓或人工判断。"
                    "脚本需要保留样本但给出警告，提示该决策词没有被识别，并回退到状态列处理。"
                    "这样审核人可以重新打开 CSV，把决策词改成通过、拒绝、待审或跳过。"
                ),
            )
        ]
    )
    draft_json = tmp_path / "draft.json"
    review_csv = tmp_path / "review.csv"
    write_import_json(drafts, draft_json)
    write_review_csv(drafts, review_csv)
    rows = _read_csv(review_csv)
    rows[0]["humanDecision"] = "确认"
    _write_csv(review_csv, rows)

    result = build_reviewed_import_payload(
        draft_json_path=draft_json,
        review_csv_path=review_csv,
        experiment_id=EXPERIMENT_ID,
    )

    assert result.payload["items"][0]["status"] == "DRAFT"
    assert any("humanDecision" in warning for warning in result.warnings)


def test_finalize_review_csv_rejects_non_uuid_ids(tmp_path) -> None:
    draft_json = tmp_path / "draft.json"
    review_csv = tmp_path / "review.csv"
    draft_json.write_text(
        json.dumps(
            [
                {
                    "caseId": "case-non-uuid",
                    "question": "导入前如何发现非法证据编号？",
                    "expectedAnswer": "finalize 阶段应提示非 UUID 证据编号。",
                    "requiredChunkIds": ["chunk-a"],
                    "citationChunkIds": ["chunk-a"],
                    "relevantChunkIds": ["chunk-a"],
                    "evaluationTopK": 5,
                    "status": "DRAFT",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _write_csv(
        review_csv,
        [
            {
                "caseId": "case-non-uuid",
                "status": "DRAFT",
                "reviewStatus": "",
                "humanDecision": "通过",
                "question": "导入前如何发现非法证据编号？",
                "expectedAnswer": "finalize 阶段应提示非 UUID 证据编号。",
                "requiredChunkIds": "chunk-a",
                "supportingChunkIds": "",
                "acceptableChunkIds": "",
                "citationChunkIds": "chunk-a",
                "relevantChunkIds": "chunk-a",
                "relevantDocumentIds": "",
                "expectedCitationChunkIds": "",
                "evaluationTopK": "5",
                "confidence": "0.8",
                "sourceTitle": "非法编号示例",
                "evidencePreview": "非 UUID 示例",
                "reviewSuggestion": "",
                "humanNotes": "",
            }
        ],
    )

    with pytest.raises(ReviewImportValidationError) as exc_info:
        build_reviewed_import_payload(
            draft_json_path=draft_json,
            review_csv_path=review_csv,
            experiment_id=EXPERIMENT_ID,
        )

    assert any("UUID" in error and "requiredChunkIds" in error for error in exc_info.value.errors)


def test_finalize_review_csv_rejects_invalid_experiment_id(tmp_path) -> None:
    draft_json = tmp_path / "draft.json"
    review_csv = tmp_path / "review.csv"
    drafts = generate_case_drafts(
        [
            _chunk(
                CHUNK_A,
                content=(
                    "售后工程师在关闭工单前，需要确认客户已经恢复业务、风险说明已经同步、"
                    "关键日志和处理过程已经沉淀到知识库，并记录后续预防建议。"
                    "如果仍有未完成动作，需要在工单中保留下一次更新时间和责任人，避免提前归档。"
                ),
            )
        ]
    )
    write_import_json(drafts, draft_json)
    write_review_csv(drafts, review_csv)
    rows = _read_csv(review_csv)
    rows[0]["humanDecision"] = "通过"
    _write_csv(review_csv, rows)

    with pytest.raises(ReviewImportValidationError) as exc_info:
        build_reviewed_import_payload(
            draft_json_path=draft_json,
            review_csv_path=review_csv,
            experiment_id="not-a-uuid",
        )

    assert any("experimentId" in error and "UUID" in error for error in exc_info.value.errors)


def test_chunks_from_json_supports_camel_case(tmp_path) -> None:
    chunk_file = tmp_path / "chunks.json"
    chunk_file.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "chunkId": CHUNK_A,
                        "documentId": DOC_ID,
                        "knowledgeBaseId": KB_ID,
                        "chunkIndex": 7,
                        "title": "JSON Chunk",
                        "content": (
                            "这是一段足够长的 JSON chunk 内容，用于生成自动测评草稿，"
                            "并保留原始 evidence id。"
                        ),
                        "metadata": {"quality_score": 0.75},
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    chunks = chunks_from_json(chunk_file)

    assert chunks[0].chunk_id == CHUNK_A
    assert chunks[0].document_id == DOC_ID
    assert chunks[0].chunk_index == 7
    assert chunks[0].metadata["quality_score"] == 0.75


class _FakeLLM:
    def __init__(self, items: list[dict[str, object]]) -> None:
        self.items = items
        self.prompts: list[str] = []

    async def generate(self, *, prompt: str, context) -> str:
        self.prompts.append(prompt)
        return json.dumps(self.items, ensure_ascii=False)


def _llm_chunks() -> list[ChunkRecord]:
    return [
        _chunk(
            CHUNK_A,
            index=1,
            title="售后故障排查",
            content=(
                "客户设备无法联网时，售后工程师先确认电源、网线、指示灯和物理链路状态。"
                "如果链路正常，再检查 DHCP 获取地址、DNS 和网关配置。"
                "仍失败时需要收集日志、错误码、设备序列号和现场操作记录，并升级到二线支持。"
                "现场工程师还应记录客户网络拓扑、交换机端口、固件版本和最近一次配置变更，"
                "避免只凭单一错误码判断根因。"
            ),
            metadata={"quality_score": 0.9, "section_title": "网络故障排查"},
        ),
        _chunk(
            CHUNK_B,
            index=2,
            title="售后故障排查",
            content=(
                "升级工单需要包含客户编号、设备序列号、错误码和最近一次操作时间。"
                "如果客户现场已经尝试重启或更换网线，也需要记录操作人、操作时间和结果，"
                "方便二线支持复盘链路状态并减少重复沟通。"
            ),
            metadata={"quality_score": 0.82},
        ),
    ]


def _chunk(
    chunk_id: str,
    *,
    index: int = 0,
    title: str = "Support Note",
    content: str,
    metadata: dict[str, object] | None = None,
) -> ChunkRecord:
    return ChunkRecord(
        chunk_id=chunk_id,
        document_id=DOC_ID,
        knowledge_base_id=KB_ID,
        title=title,
        chunk_index=index,
        content=content,
        metadata=metadata or {},
    )


def _read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
