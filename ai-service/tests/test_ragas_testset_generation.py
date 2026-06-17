from app.rag.evaluators.testset_generation import (
    chunks_from_json,
    generate_case_drafts,
    write_import_json,
    write_review_csv,
)
from app.schemas.ingest import ChunkRecord


def test_generate_case_drafts_from_document_chunks() -> None:
    chunks = [
        _chunk(
            "chunk-a",
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
            "chunk-b",
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
            "chunk-parent",
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
    assert primary.required_chunk_ids == ["chunk-a"]
    assert primary.citation_chunk_ids == ["chunk-a"]
    assert primary.relevant_document_ids == ["doc-support"]
    assert "网络故障排查" in primary.question
    assert "设备无法联网" in primary.expected_answer
    assert "人工确认" in primary.notes


def test_write_import_json_and_review_csv(tmp_path) -> None:
    drafts = generate_case_drafts([
            _chunk(
                "chunk-a",
                index=1,
                title="售后 SLA",
                content=(
                    "P1 故障需要 15 分钟内响应，30 分钟内给出临时绕行方案，并持续同步处理进度。"
                    "如果故障影响核心生产链路，值班工程师需要同步客户成功经理和二线专家，"
                    "在工单中记录影响范围、当前恢复动作、下一次更新时间和风险说明。"
                ),
            )
        ])
    output_json = tmp_path / "draft-cases.json"
    review_csv = tmp_path / "draft-review.csv"

    write_import_json(drafts, output_json)
    write_review_csv(drafts, review_csv)

    json_text = output_json.read_text(encoding="utf-8")
    csv_text = review_csv.read_text(encoding="utf-8-sig")
    assert '"caseId"' in json_text
    assert '"status": "DRAFT"' in json_text
    assert "人工确认" in json_text
    assert "humanDecision" in csv_text
    assert "P1 故障" in csv_text


def test_chunks_from_json_supports_camel_case(tmp_path) -> None:
    chunk_file = tmp_path / "chunks.json"
    chunk_file.write_text(
        """
        {
          "items": [
            {
              "chunkId": "chunk-json",
              "documentId": "doc-json",
              "knowledgeBaseId": "kb-json",
              "chunkIndex": 7,
              "title": "JSON Chunk",
              "content": "这是一段足够长的 JSON chunk 内容，用于生成自动测评草稿，并保留原始 evidence id。",
              "metadata": {"quality_score": 0.75}
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    chunks = chunks_from_json(chunk_file)

    assert chunks[0].chunk_id == "chunk-json"
    assert chunks[0].document_id == "doc-json"
    assert chunks[0].chunk_index == 7
    assert chunks[0].metadata["quality_score"] == 0.75


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
        document_id="doc-support",
        knowledge_base_id="kb-support",
        title=title,
        chunk_index=index,
        content=content,
        metadata=metadata or {},
    )
