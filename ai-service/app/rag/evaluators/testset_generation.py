from __future__ import annotations

import asyncio
import csv
import hashlib
import inspect
import json
import re
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Protocol, Sequence

from app.schemas.ingest import ChunkRecord
from app.services.adapters.base import AdapterCallContext


DEFAULT_CASES_PER_DOCUMENT = 3
DEFAULT_TOP_K = 5
DEFAULT_COMPLEX_QUESTION_TYPES = ("fact", "reasoning", "multi_context", "troubleshooting")
GENERATION_MODES = {"rule", "llm", "ragas", "auto"}

BACKEND_IMPORT_FIELDS = [
    "caseId",
    "question",
    "expectedAnswer",
    "requiredChunkIds",
    "supportingChunkIds",
    "acceptableChunkIds",
    "citationChunkIds",
    "relevantChunkIds",
    "relevantDocumentIds",
    "expectedCitationChunkIds",
    "evaluationTopK",
    "notes",
    "status",
]

REVIEW_FIELDNAMES = [
    "caseId",
    "status",
    "reviewStatus",
    "humanDecision",
    "question",
    "expectedAnswer",
    "requiredChunkIds",
    "supportingChunkIds",
    "acceptableChunkIds",
    "citationChunkIds",
    "relevantChunkIds",
    "relevantDocumentIds",
    "expectedCitationChunkIds",
    "evaluationTopK",
    "questionType",
    "generatorMode",
    "metadata",
    "confidence",
    "sourceTitle",
    "evidencePreview",
    "reviewSuggestion",
    "humanNotes",
]

LIST_FIELDS = {
    "requiredChunkIds",
    "supportingChunkIds",
    "acceptableChunkIds",
    "citationChunkIds",
    "relevantChunkIds",
    "relevantDocumentIds",
    "expectedCitationChunkIds",
}

APPROVED_DECISIONS = {"approve", "approved", "active", "pass", "passed", "ok", "y", "yes", "通过", "已通过", "同意", "启用", "采纳", "保留"}
REJECTED_DECISIONS = {"reject", "rejected", "drop", "dropped", "discard", "discarded", "n", "no", "拒绝", "不通过", "驳回", "剔除", "删除", "作废", "停用"}
DRAFT_DECISIONS = {"draft", "pending", "review", "revise", "needs_revision", "待审", "待审核", "草稿", "需修改", "修改后再审"}
SKIP_DECISIONS = {"skip", "ignore", "ignored", "跳过", "忽略", "不导入"}


@dataclass(frozen=True)
class EvaluationCaseDraft:
    case_id: str
    question: str
    expected_answer: str
    required_chunk_ids: list[str]
    supporting_chunk_ids: list[str] = field(default_factory=list)
    acceptable_chunk_ids: list[str] = field(default_factory=list)
    citation_chunk_ids: list[str] = field(default_factory=list)
    relevant_chunk_ids: list[str] = field(default_factory=list)
    relevant_document_ids: list[str] = field(default_factory=list)
    expected_citation_chunk_ids: list[str] = field(default_factory=list)
    evaluation_top_k: int = DEFAULT_TOP_K
    notes: str = ""
    status: str = "DRAFT"
    review_status: str = "待审核"
    review_suggestion: str = ""
    confidence: float = 0.5
    source_title: str = ""
    evidence_preview: str = ""
    question_type: str = "fact"
    generator_mode: str = "rule"
    metadata: dict[str, object] = field(default_factory=dict)

    def to_import_item(self) -> dict[str, object]:
        return {
            "caseId": self.case_id,
            "question": self.question,
            "expectedAnswer": self.expected_answer,
            "requiredChunkIds": self.required_chunk_ids,
            "supportingChunkIds": self.supporting_chunk_ids,
            "acceptableChunkIds": self.acceptable_chunk_ids,
            "citationChunkIds": self.citation_chunk_ids,
            "relevantChunkIds": self.relevant_chunk_ids,
            "relevantDocumentIds": self.relevant_document_ids,
            "expectedCitationChunkIds": self.expected_citation_chunk_ids,
            "evaluationTopK": self.evaluation_top_k,
            "notes": self.notes,
            "status": self.status,
        }

    def to_review_row(self) -> dict[str, object]:
        return {
            "caseId": self.case_id,
            "status": self.status,
            "reviewStatus": self.review_status,
            "humanDecision": "",
            "question": self.question,
            "expectedAnswer": self.expected_answer,
            "requiredChunkIds": _join_ids(self.required_chunk_ids),
            "supportingChunkIds": _join_ids(self.supporting_chunk_ids),
            "acceptableChunkIds": _join_ids(self.acceptable_chunk_ids),
            "citationChunkIds": _join_ids(self.citation_chunk_ids),
            "relevantChunkIds": _join_ids(self.relevant_chunk_ids),
            "relevantDocumentIds": _join_ids(self.relevant_document_ids),
            "expectedCitationChunkIds": _join_ids(self.expected_citation_chunk_ids),
            "evaluationTopK": self.evaluation_top_k,
            "questionType": self.question_type,
            "generatorMode": self.generator_mode,
            "metadata": _metadata_json(self.metadata),
            "confidence": self.confidence,
            "sourceTitle": self.source_title,
            "evidencePreview": self.evidence_preview,
            "reviewSuggestion": self.review_suggestion,
            "humanNotes": "",
        }


@dataclass(frozen=True)
class ReviewImportBuildResult:
    payload: dict[str, object]
    counts: dict[str, int]
    skipped_case_ids: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class TestsetGenerationResult:
    drafts: list[EvaluationCaseDraft]
    mode: str
    fallback_used: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TestsetSourceDocument:
    page_content: str
    metadata: dict[str, object]


class ReviewImportValidationError(ValueError):
    def __init__(self, errors: list[str], warnings: list[str] | None = None) -> None:
        super().__init__("\n".join(errors))
        self.errors = errors
        self.warnings = warnings or []


class TestsetGenerationError(RuntimeError):
    """Raised when an optional LLM/RAGAS testset generator cannot run."""

    __test__ = False


class AsyncLLMGenerator(Protocol):
    async def generate(self, *, prompt: str, context: AdapterCallContext) -> str:
        ...


def generate_case_drafts(
    chunks: Sequence[ChunkRecord],
    *,
    cases_per_document: int = DEFAULT_CASES_PER_DOCUMENT,
    top_k: int = DEFAULT_TOP_K,
) -> list[EvaluationCaseDraft]:
    grouped = _group_chunks(chunks)
    drafts: list[EvaluationCaseDraft] = []
    for document_chunks in grouped.values():
        candidates = _rank_candidates(document_chunks)
        for index, chunk in enumerate(candidates[: max(1, cases_per_document)], start=1):
            siblings = _supporting_siblings(chunk, candidates)
            drafts.append(_draft_from_chunk(chunk, siblings=siblings, ordinal=index, top_k=top_k))
    return drafts


def generate_case_drafts_by_mode(
    chunks: Sequence[ChunkRecord],
    *,
    mode: str = "rule",
    cases_per_document: int = DEFAULT_CASES_PER_DOCUMENT,
    top_k: int = DEFAULT_TOP_K,
    llm: AsyncLLMGenerator | None = None,
    model_name: str = "llm",
    question_types: Sequence[str] = DEFAULT_COMPLEX_QUESTION_TYPES,
    ragas_testset_size: int | None = None,
    fallback_to_rules: bool = True,
) -> TestsetGenerationResult:
    normalized_mode = mode.strip().lower()
    if normalized_mode not in GENERATION_MODES:
        raise ValueError(f"Unsupported testset generation mode: {mode}")
    if normalized_mode == "rule":
        return TestsetGenerationResult(
            drafts=generate_case_drafts(chunks, cases_per_document=cases_per_document, top_k=top_k),
            mode="rule",
        )

    try:
        if normalized_mode == "llm":
            return TestsetGenerationResult(
                drafts=_run_llm_generation(
                    chunks,
                    llm=llm,
                    model_name=model_name,
                    cases_per_document=cases_per_document,
                    top_k=top_k,
                    question_types=question_types,
                ),
                mode="llm",
            )

        testset_size = ragas_testset_size or _default_ragas_testset_size(chunks, cases_per_document)
        if normalized_mode == "ragas":
            drafts = generate_case_drafts_with_ragas(chunks, testset_size=testset_size, top_k=top_k)
            return TestsetGenerationResult(drafts=drafts, mode="ragas")

        warnings: list[str] = []
        try:
            drafts = generate_case_drafts_with_ragas(chunks, testset_size=testset_size, top_k=top_k)
            if drafts:
                return TestsetGenerationResult(drafts=drafts, mode="ragas", warnings=warnings)
            warnings.append("RAGAS returned no drafts.")
        except Exception as exc:
            warnings.append(f"RAGAS failed: {exc}")

        if llm is not None:
            try:
                drafts = _run_llm_generation(
                    chunks,
                    llm=llm,
                    model_name=model_name,
                    cases_per_document=cases_per_document,
                    top_k=top_k,
                    question_types=question_types,
                )
                if drafts:
                    return TestsetGenerationResult(drafts=drafts, mode="llm", warnings=warnings)
                warnings.append("LLM returned no drafts.")
            except Exception as exc:
                warnings.append(f"LLM failed: {exc}")

        raise TestsetGenerationError("; ".join(warnings) or "AUTO mode found no available generator.")
    except TestsetGenerationError as exc:
        if not fallback_to_rules:
            raise
        drafts = generate_case_drafts(chunks, cases_per_document=cases_per_document, top_k=top_k)
        return TestsetGenerationResult(
            drafts=drafts,
            mode="rule",
            fallback_used=True,
            warnings=[f"{normalized_mode.upper()} testset generation failed: {exc} Falling back to rule-based drafts."],
        )
    except Exception as exc:
        if not fallback_to_rules:
            raise TestsetGenerationError(f"{normalized_mode.upper()} testset generation failed: {exc}") from exc
        drafts = generate_case_drafts(chunks, cases_per_document=cases_per_document, top_k=top_k)
        return TestsetGenerationResult(
            drafts=drafts,
            mode="rule",
            fallback_used=True,
            warnings=[f"{normalized_mode.upper()} testset generation failed: {exc} Falling back to rule-based drafts."],
        )


def chunks_to_internal_documents(chunks: Sequence[ChunkRecord]) -> list[TestsetSourceDocument]:
    return [
        TestsetSourceDocument(page_content=_clean_content(chunk.content), metadata=_chunk_document_metadata(chunk))
        for chunk in _usable_chunks(chunks)
    ]


def chunks_to_langchain_documents(chunks: Sequence[ChunkRecord]) -> list[object]:
    try:
        from langchain_core.documents import Document
    except Exception as exc:  # pragma: no cover - optional isolated runtime
        raise TestsetGenerationError(
            "LangChain Document conversion requires langchain-core in the isolated RAGAS/LLM environment."
        ) from exc

    return [
        Document(page_content=document.page_content, metadata=document.metadata)
        for document in chunks_to_internal_documents(chunks)
    ]


def _run_llm_generation(
    chunks: Sequence[ChunkRecord],
    *,
    llm: AsyncLLMGenerator | None,
    model_name: str,
    cases_per_document: int,
    top_k: int,
    question_types: Sequence[str],
) -> list[EvaluationCaseDraft]:
    if llm is None:
        raise TestsetGenerationError("LLM mode requires a configured llm adapter.")
    return asyncio.run(
        generate_case_drafts_with_llm(
            chunks,
            llm=llm,
            model_name=model_name,
            cases_per_document=cases_per_document,
            top_k=top_k,
            question_types=question_types,
        )
    )


async def generate_case_drafts_with_llm(
    chunks: Sequence[ChunkRecord],
    *,
    llm: AsyncLLMGenerator,
    model_name: str,
    cases_per_document: int = DEFAULT_CASES_PER_DOCUMENT,
    top_k: int = DEFAULT_TOP_K,
    question_types: Sequence[str] = DEFAULT_COMPLEX_QUESTION_TYPES,
) -> list[EvaluationCaseDraft]:
    grouped = _group_chunks(chunks)
    drafts: list[EvaluationCaseDraft] = []
    for document_chunks in grouped.values():
        candidates = _rank_candidates(document_chunks)[: max(1, cases_per_document * 3)]
        if not candidates:
            continue
        prompt = _llm_testset_prompt(candidates, cases_per_document=cases_per_document, question_types=question_types)
        response = await llm.generate(
            prompt=prompt,
            context=AdapterCallContext(
                trace_id=str(uuid.uuid4()),
                run_id=str(uuid.uuid4()),
                operation="ragas_testset_generation",
                model_name=model_name,
                prompt_name="ragas_testset_generation",
                prompt_version="v1",
                strategy_name="llm-testset-generation",
                metadata={"chunk_count": len(candidates), "cases_per_document": cases_per_document},
            ),
        )
        generated_items = _extract_generated_items(response)
        chunk_by_id = {chunk.chunk_id: chunk for chunk in candidates}
        for index, item in enumerate(generated_items[: max(1, cases_per_document)], start=1):
            drafts.append(
                _draft_from_generated_item(
                    item,
                    chunk_by_id=chunk_by_id,
                    fallback_chunk=candidates[min(index - 1, len(candidates) - 1)],
                    ordinal=index,
                    top_k=top_k,
                    source="LLM",
                )
            )
    return drafts


def generate_case_drafts_with_ragas(
    chunks: Sequence[ChunkRecord],
    *,
    testset_size: int,
    top_k: int = DEFAULT_TOP_K,
    llm: object | None = None,
    embedding_model: object | None = None,
) -> list[EvaluationCaseDraft]:
    """Generate drafts through RAGAS TestsetGenerator when optional deps exist.

    This function intentionally imports RAGAS/LangChain lazily so the main
    ai-service runtime can stay on Pydantic v1.
    """

    usable_chunks = _usable_chunks(chunks)
    if not usable_chunks:
        return []
    try:
        from ragas.testset import TestsetGenerator
    except Exception as exc:  # pragma: no cover - optional isolated runtime
        raise TestsetGenerationError(
            "RAGAS TestsetGenerator requires an isolated environment with ragas and langchain-core installed."
        ) from exc

    if llm is None or embedding_model is None:
        try:
            from app.rag.evaluators.ragas_runtime import build_langchain_generation_models
        except Exception as exc:  # pragma: no cover - optional isolated runtime
            raise TestsetGenerationError(
                "RAGAS mode requires langchain-openai compatible generation models. "
                "Install optional RAGAS dependencies in a separate venv."
            ) from exc
        llm, embedding_model = build_langchain_generation_models()

    docs = chunks_to_langchain_documents(usable_chunks)
    generator = TestsetGenerator.from_langchain(llm, embedding_model)
    testset = _generate_with_ragas_generator(generator, docs, testset_size=max(1, testset_size))
    rows = _ragas_testset_rows(testset)
    chunk_by_id = {chunk.chunk_id: chunk for chunk in usable_chunks}
    return [
        _draft_from_generated_item(
            row,
            chunk_by_id=chunk_by_id,
            fallback_chunk=_ragas_fallback_chunk(row, chunk_by_id) or usable_chunks[min(index, len(usable_chunks) - 1)],
            ordinal=index + 1,
            top_k=top_k,
            source="RAGAS TestsetGenerator",
            allow_fallback_evidence=False,
        )
        for index, row in enumerate(rows)
    ]


def write_import_json(
    drafts: Iterable[EvaluationCaseDraft],
    path: str | Path,
    *,
    experiment_id: str | None = None,
) -> None:
    items = [draft.to_import_item() for draft in drafts]
    payload: object = {"experimentId": experiment_id, "items": items} if experiment_id else items
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_review_csv(drafts: Iterable[EvaluationCaseDraft], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [draft.to_review_row() for draft in drafts]
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def write_reviewed_import_json(result: ReviewImportBuildResult, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_reviewed_import_payload(
    *,
    draft_json_path: str | Path,
    review_csv_path: str | Path,
    experiment_id: str,
    active_only: bool = False,
    include_rejected: bool = True,
) -> ReviewImportBuildResult:
    errors: list[str] = []
    if not _is_uuid(experiment_id):
        errors.append(f"experimentId={experiment_id} 不是合法 UUID。")

    draft_items = load_import_items(draft_json_path)
    draft_by_case_id = {str(item.get("caseId") or ""): item for item in draft_items}
    review_rows = _read_review_rows(review_csv_path)
    items: list[dict[str, object]] = []
    skipped_case_ids: list[str] = []
    warnings: list[str] = []
    counts = {"ACTIVE": 0, "DRAFT": 0, "REJECTED": 0, "ARCHIVED": 0, "OTHER": 0, "SKIPPED": 0}

    for row_index, row in enumerate(review_rows, start=2):
        case_id = _stripped(row.get("caseId"))
        if not case_id:
            warnings.append(f"第 {row_index} 行缺少 caseId，已跳过。")
            counts["SKIPPED"] += 1
            continue

        base = dict(draft_by_case_id.get(case_id) or {"caseId": case_id})
        if case_id not in draft_by_case_id:
            warnings.append(f"第 {row_index} 行 caseId={case_id} 不在草稿 JSON 中，将按新增用例处理。")

        item = _merge_review_row(base, row)
        decision_warning = _review_decision_warning(case_id, row)
        if decision_warning:
            warnings.append(f"第 {row_index} 行 {decision_warning}")

        status = _status_from_review(row, item)
        if status == "SKIP":
            skipped_case_ids.append(case_id)
            counts["SKIPPED"] += 1
            continue

        item["status"] = status
        if active_only and status != "ACTIVE":
            skipped_case_ids.append(case_id)
            counts["SKIPPED"] += 1
            continue
        if not include_rejected and status == "REJECTED":
            skipped_case_ids.append(case_id)
            counts["SKIPPED"] += 1
            continue

        item_errors = _validate_import_item(case_id, item)
        errors.extend(f"第 {row_index} 行 {error}" for error in item_errors)

        items.append(_prune_import_item(item))
        counts[status if status in counts else "OTHER"] += 1

    if not items:
        errors.append("没有生成可导入的评测用例，后端 import 接口会拒绝空 items。")

    if errors:
        raise ReviewImportValidationError(errors, warnings)

    payload = {"experimentId": experiment_id, "items": items}
    return ReviewImportBuildResult(payload=payload, counts=counts, skipped_case_ids=skipped_case_ids, warnings=warnings)


def load_import_items(path: str | Path) -> list[dict[str, object]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    if not isinstance(data, list):
        raise ValueError("draft JSON must be an array or an object with an items array")
    return [dict(item) for item in data]


def chunks_from_json(path: str | Path) -> list[ChunkRecord]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    if not isinstance(data, list):
        raise ValueError("chunk JSON must be an array or an object with an items array")
    return [_chunk_from_mapping(item) for item in data]


def _draft_from_chunk(
    chunk: ChunkRecord,
    *,
    siblings: list[ChunkRecord],
    ordinal: int,
    top_k: int,
) -> EvaluationCaseDraft:
    title = _title(chunk)
    clean_text = _clean_content(chunk.content)
    answer = _expected_answer(clean_text)
    topic = _topic(title, clean_text)
    required_ids = [chunk.chunk_id]
    supporting_ids = [sibling.chunk_id for sibling in siblings]
    relevant_ids = _dedupe([*required_ids, *supporting_ids])
    case_id = _case_id(chunk, ordinal)
    confidence = _confidence(chunk, answer, supporting_ids)
    return EvaluationCaseDraft(
        case_id=case_id,
        question=f"根据《{title}》，{topic}的关键处理方式是什么？",
        expected_answer=answer,
        required_chunk_ids=required_ids,
        supporting_chunk_ids=supporting_ids,
        citation_chunk_ids=required_ids,
        relevant_chunk_ids=relevant_ids,
        relevant_document_ids=[chunk.document_id],
        expected_citation_chunk_ids=required_ids,
        evaluation_top_k=top_k,
        notes=(
            "RAGAS 草稿自动生成：请人工确认问题是否自然、标准答案是否完全由证据支持，"
            "并检查 required/supporting/citation chunk 是否准确。"
        ),
        review_suggestion=(
            "建议先核对 requiredChunkIds 对应内容，再决定是否补充 supportingChunkIds 或改写问题。"
        ),
        confidence=confidence,
        source_title=title,
        evidence_preview=clean_text[:360],
        question_type="fact",
        generator_mode="rule",
        metadata={"generator_mode": "rule", "question_type": "fact", "source_chunk_count": 1 + len(supporting_ids)},
    )


def _draft_from_generated_item(
    item: dict[str, object],
    *,
    chunk_by_id: dict[str, ChunkRecord],
    fallback_chunk: ChunkRecord,
    ordinal: int,
    top_k: int,
    source: str,
    allow_fallback_evidence: bool = True,
) -> EvaluationCaseDraft:
    item = _normalize_generated_item(item)
    item_metadata = _item_metadata(item)
    question = _first_text(item, "question", "user_input", "query")
    expected_answer = _first_text(item, "expectedAnswer", "expected_answer", "reference", "ground_truth", "answer")
    question_type = (
        _first_text(item, "questionType", "question_type", "synthesizer_name", "type")
        or _first_text(item_metadata, "questionType", "question_type", "synthesizer_name", "type")
        or "generated"
    )
    difficulty = _first_text(item, "difficulty") or _first_text(item_metadata, "difficulty") or "medium"
    required_ids = _known_chunk_ids(
        _first_list(item, "requiredChunkIds", "required_chunk_ids", "reference_context_ids", "source_chunk_ids")
        or _first_list(item_metadata, "requiredChunkIds", "required_chunk_ids", "reference_context_ids", "source_chunk_ids"),
        chunk_by_id,
    )
    supporting_ids = _known_chunk_ids(
        _first_list(item, "supportingChunkIds", "supporting_chunk_ids")
        or _first_list(item_metadata, "supportingChunkIds", "supporting_chunk_ids"),
        chunk_by_id,
    )
    acceptable_ids = _known_chunk_ids(
        _first_list(item, "acceptableChunkIds", "acceptable_chunk_ids")
        or _first_list(item_metadata, "acceptableChunkIds", "acceptable_chunk_ids"),
        chunk_by_id,
    )
    citation_ids = _known_chunk_ids(
        _first_list(item, "citationChunkIds", "citation_chunk_ids", "expectedCitationChunkIds")
        or _first_list(item_metadata, "citationChunkIds", "citation_chunk_ids", "expectedCitationChunkIds"),
        chunk_by_id,
    )
    evidence_needs_review = False
    if not required_ids and allow_fallback_evidence:
        required_ids = [fallback_chunk.chunk_id]
    elif not required_ids:
        evidence_needs_review = True
    if not citation_ids:
        citation_ids = required_ids
    relevant_ids = _dedupe([*required_ids, *supporting_ids, *acceptable_ids])
    evidence_chunk = chunk_by_id.get(required_ids[0], fallback_chunk) if required_ids else fallback_chunk
    if not expected_answer:
        expected_answer = _expected_answer(_clean_content(evidence_chunk.content))
    title = _title(evidence_chunk)
    case_id = _first_text(item, "caseId", "case_id") or _generated_case_id(evidence_chunk, question, ordinal)
    generator_mode = "ragas" if source.lower().startswith("ragas") else "llm"
    confidence = _float_from_item(item, item_metadata, "confidence") or (0.72 if generator_mode == "llm" else 0.78)
    metadata = _metadata_payload(
        item_metadata,
        question_type=question_type,
        generator_mode=generator_mode,
        source=source,
        difficulty=difficulty,
    )
    notes = (
        f"{source} 自动生成：题型={question_type}，难度={difficulty}。"
        "请人工确认问题、标准答案和证据 chunk 是否匹配。"
    )
    if evidence_needs_review:
        notes += "\nRAGAS output did not include project chunk IDs; fill required/citation chunk IDs during review."
        metadata["evidence_needs_review"] = True
        confidence = min(confidence, 0.4)
    return EvaluationCaseDraft(
        case_id=case_id[:120],
        question=question or f"根据《{title}》，需要如何理解该知识片段？",
        expected_answer=expected_answer,
        required_chunk_ids=required_ids,
        supporting_chunk_ids=supporting_ids,
        acceptable_chunk_ids=acceptable_ids,
        citation_chunk_ids=citation_ids,
        relevant_chunk_ids=relevant_ids,
        relevant_document_ids=_dedupe([chunk_by_id.get(chunk_id, fallback_chunk).document_id for chunk_id in relevant_ids]),
        expected_citation_chunk_ids=citation_ids,
        evaluation_top_k=top_k,
        notes=notes,
        review_suggestion="重点核对复杂题是否真的需要多片段证据，并确认标准答案没有引入证据外信息。",
        confidence=confidence,
        source_title=title,
        evidence_preview=_clean_content(evidence_chunk.content)[:360],
        question_type=question_type,
        generator_mode=generator_mode,
        metadata=metadata,
    )


def _group_chunks(chunks: Sequence[ChunkRecord]) -> dict[str, list[ChunkRecord]]:
    grouped: dict[str, list[ChunkRecord]] = {}
    for chunk in chunks:
        if _is_usable_chunk(chunk):
            grouped.setdefault(chunk.document_id, []).append(chunk)
    for values in grouped.values():
        values.sort(key=lambda item: item.chunk_index)
    return grouped


def _rank_candidates(chunks: list[ChunkRecord]) -> list[ChunkRecord]:
    return sorted(chunks, key=lambda chunk: (-_candidate_score(chunk), chunk.chunk_index))


def _candidate_score(chunk: ChunkRecord) -> float:
    metadata = chunk.metadata or {}
    score = float(metadata.get("quality_score") or 1.0)
    text = _clean_content(chunk.content)
    if len(text) >= 180:
        score += 0.2
    if any(marker in text for marker in ("步骤", "原因", "方案", "风险", "对比", "排查", "实现", "处理", "升级", "故障", "SLA")):
        score += 0.2
    if metadata.get("heading_path") or metadata.get("section_title"):
        score += 0.1
    return score


def _supporting_siblings(chunk: ChunkRecord, candidates: list[ChunkRecord]) -> list[ChunkRecord]:
    siblings: list[ChunkRecord] = []
    for candidate in candidates:
        if candidate.chunk_id == chunk.chunk_id:
            continue
        if candidate.document_id != chunk.document_id:
            continue
        same_parent = chunk.parent_chunk_id and candidate.parent_chunk_id == chunk.parent_chunk_id
        near = abs(candidate.chunk_index - chunk.chunk_index) <= 1
        if same_parent or near:
            siblings.append(candidate)
        if len(siblings) >= 2:
            break
    return siblings


def _usable_chunks(chunks: Sequence[ChunkRecord]) -> list[ChunkRecord]:
    results: list[ChunkRecord] = []
    for document_chunks in _group_chunks(chunks).values():
        results.extend(document_chunks)
    return results


def _chunk_document_metadata(chunk: ChunkRecord) -> dict[str, object]:
    metadata = dict(chunk.metadata or {})
    metadata.update(
        {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "knowledge_base_id": chunk.knowledge_base_id or "",
            "parent_chunk_id": chunk.parent_chunk_id or "",
            "title": _title(chunk),
            "chunk_index": chunk.chunk_index,
        }
    )
    return metadata


def _default_ragas_testset_size(chunks: Sequence[ChunkRecord], cases_per_document: int) -> int:
    document_count = len(_group_chunks(chunks))
    return max(1, document_count * max(1, cases_per_document))


def _is_usable_chunk(chunk: ChunkRecord) -> bool:
    metadata = chunk.metadata or {}
    if metadata.get("chunk_level") == "parent":
        return False
    if str(metadata.get("block_type") or "").lower() in {"image", "page_marker", "toc"}:
        return False
    if metadata.get("low_quality_reasons"):
        return False
    return len(_clean_content(chunk.content)) >= 80


def _chunk_from_mapping(item: dict[str, object]) -> ChunkRecord:
    metadata = item.get("metadata") or {}
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    return ChunkRecord(
        chunk_id=str(item.get("chunk_id") or item.get("chunkId") or item.get("id")),
        document_id=str(item.get("document_id") or item.get("documentId")),
        knowledge_base_id=str(item.get("knowledge_base_id") or item.get("knowledgeBaseId") or ""),
        parent_chunk_id=_optional_str(item.get("parent_chunk_id") or item.get("parentChunkId")),
        title=_optional_str(item.get("title")),
        chunk_index=int(item.get("chunk_index") or item.get("chunkIndex") or 0),
        content=str(item.get("content") or item.get("text") or ""),
        metadata=dict(metadata),
    )


def _expected_answer(text: str) -> str:
    sentences = _split_sentences(text)
    answer = " ".join(sentences[:3]).strip()
    if not answer:
        answer = text[:420].strip()
    if len(answer) > 520:
        answer = answer[:520].rstrip(" ，,；;。") + "..."
    return answer


def _topic(title: str, text: str) -> str:
    if title and title != "未命名文档":
        return title[:40]
    heading = next((line.strip("# ").strip() for line in text.splitlines() if line.strip().startswith("#")), "")
    if heading:
        return heading[:40]
    tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9_.-]+", text)
    return "".join(tokens[:6])[:40] or "该知识片段"


def _title(chunk: ChunkRecord) -> str:
    metadata = chunk.metadata or {}
    for key in ("section_title", "parent_heading", "document_title"):
        value = metadata.get(key)
        if value:
            return str(value)[:60]
    if chunk.title:
        return chunk.title[:60]
    return "未命名文档"


def _case_id(chunk: ChunkRecord, ordinal: int) -> str:
    title_slug = re.sub(r"[^a-z0-9]+", "-", _title(chunk).lower()).strip("-")[:36]
    digest = hashlib.sha1(f"{chunk.document_id}:{chunk.chunk_id}".encode("utf-8")).hexdigest()[:8]
    base = title_slug or "auto-case"
    return f"{base}-{ordinal}-{digest}"[:120]


def _generated_case_id(chunk: ChunkRecord, question: str, ordinal: int) -> str:
    digest = hashlib.sha1(f"{chunk.document_id}:{chunk.chunk_id}:{question}".encode("utf-8")).hexdigest()[:10]
    return f"generated-{ordinal}-{digest}"


def _confidence(chunk: ChunkRecord, answer: str, supporting_ids: list[str]) -> float:
    metadata = chunk.metadata or {}
    quality = float(metadata.get("quality_score") or 1.0)
    length_bonus = 0.1 if len(answer) >= 120 else 0.0
    support_bonus = 0.1 if supporting_ids else 0.0
    return round(min(0.95, max(0.25, (quality * 0.65) + length_bonus + support_bonus)), 2)


def _clean_content(text: str) -> str:
    text = re.sub(r"```.*?```", "[代码片段略]", text, flags=re.S)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[。！？!?])\s*", text) if part.strip()]


def _llm_testset_prompt(
    chunks: Sequence[ChunkRecord],
    *,
    cases_per_document: int,
    question_types: Sequence[str],
) -> str:
    chunk_blocks = []
    for chunk in chunks:
        chunk_blocks.append(
            "\n".join(
                [
                    f"chunk_id: {chunk.chunk_id}",
                    f"document_id: {chunk.document_id}",
                    f"title: {_title(chunk)}",
                    f"content: {_clean_content(chunk.content)[:1200]}",
                ]
            )
        )
    return (
        "你是企业售后技术支持知识库的 RAG 测评集设计师。"
        "请基于给定证据 chunk 生成中文评测样本，覆盖事实题、推理题、多证据题、故障排查题。"
        "必须只使用证据中的信息，不要编造。"
        f"最多生成 {cases_per_document} 条，题型候选：{', '.join(question_types)}。\n"
        "只输出 JSON 数组，每个对象字段如下："
        "caseId, question, expectedAnswer, requiredChunkIds, supportingChunkIds, "
        "acceptableChunkIds, citationChunkIds, questionType, difficulty。\n"
        "requiredChunkIds 必须包含直接支撑标准答案的 chunk_id；多证据题可使用 supportingChunkIds。\n\n"
        "证据 chunk：\n"
        + "\n\n---\n\n".join(chunk_blocks)
    )


def _extract_generated_items(text: str) -> list[dict[str, object]]:
    stripped = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", stripped, flags=re.S | re.I)
    if fenced:
        stripped = fenced.group(1).strip()
    if not stripped.startswith("["):
        array_match = re.search(r"\[.*\]", stripped, flags=re.S)
        if array_match:
            stripped = array_match.group(0)
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise TestsetGenerationError(f"LLM did not return valid JSON array: {exc}") from exc
    if not isinstance(data, list):
        raise TestsetGenerationError("LLM testset output must be a JSON array.")
    return [dict(item) for item in data if isinstance(item, dict)]


def _generate_with_ragas_generator(generator: object, docs: list[object], *, testset_size: int) -> object:
    method = getattr(generator, "generate_with_langchain_docs", None)
    if method is None:
        raise TestsetGenerationError("RAGAS TestsetGenerator has no generate_with_langchain_docs method.")
    signature = inspect.signature(method)
    params = signature.parameters
    if "testset_size" in params:
        return method(docs, testset_size=testset_size)
    if "test_size" in params:
        return method(docs, test_size=testset_size)
    return method(docs, testset_size)


def _ragas_testset_rows(testset: object) -> list[dict[str, object]]:
    if hasattr(testset, "to_pandas"):
        dataframe = testset.to_pandas()
        return json.loads(dataframe.to_json(orient="records", force_ascii=False))
    if hasattr(testset, "to_list"):
        data = testset.to_list()
        return [_object_to_mapping(item) for item in data]
    if isinstance(testset, list):
        return [_object_to_mapping(item) for item in testset]
    raise TestsetGenerationError("Unsupported RAGAS Testset result shape.")


def _normalize_generated_item(item: dict[str, object]) -> dict[str, object]:
    normalized = dict(item)
    for nested_key in ("eval_sample", "sample", "test_sample"):
        nested = normalized.get(nested_key)
        if nested is None:
            continue
        nested_mapping = _object_to_mapping(nested)
        for key, value in nested_mapping.items():
            normalized.setdefault(key, value)
    return normalized


def _item_metadata(item: dict[str, object]) -> dict[str, object]:
    metadata = item.get("metadata")
    if isinstance(metadata, Mapping):
        return dict(metadata)
    return {}


def _object_to_mapping(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "model_dump"):
        data = value.model_dump()
        if isinstance(data, Mapping):
            return dict(data)
    if hasattr(value, "dict"):
        data = value.dict()
        if isinstance(data, Mapping):
            return dict(data)
    mapping: dict[str, object] = {}
    for key in (
        "question",
        "user_input",
        "query",
        "reference",
        "ground_truth",
        "answer",
        "metadata",
        "synthesizer_name",
        "reference_context_ids",
    ):
        if hasattr(value, key):
            mapping[key] = getattr(value, key)
    return mapping


def _first_text(item: dict[str, object], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        if isinstance(value, str) and value.strip():
            return value.strip()
        if not isinstance(value, (list, dict)):
            return str(value).strip()
    return ""


def _first_list(item: dict[str, object], *keys: str) -> list[str]:
    for key in keys:
        value = item.get(key)
        if isinstance(value, list):
            return [str(part).strip() for part in value if str(part).strip()]
        if isinstance(value, str) and value.strip():
            return _split_ids(value)
    return []


def _known_chunk_ids(values: Iterable[str], chunk_by_id: dict[str, ChunkRecord]) -> list[str]:
    return _dedupe([value for value in values if value in chunk_by_id])


def _ragas_fallback_chunk(item: dict[str, object], chunk_by_id: dict[str, ChunkRecord]) -> ChunkRecord | None:
    item = _normalize_generated_item(item)
    metadata = _item_metadata(item)
    explicit_ids = _known_chunk_ids(
        _first_list(item, "requiredChunkIds", "required_chunk_ids", "reference_context_ids", "source_chunk_ids")
        or _first_list(metadata, "requiredChunkIds", "required_chunk_ids", "reference_context_ids", "source_chunk_ids"),
        chunk_by_id,
    )
    if explicit_ids:
        return chunk_by_id[explicit_ids[0]]

    contexts = _first_list(item, "reference_contexts", "contexts", "retrieved_contexts")
    if not contexts:
        return None
    normalized_contexts = [_clean_content(context) for context in contexts if context.strip()]
    for chunk in chunk_by_id.values():
        chunk_text = _clean_content(chunk.content)
        if any(context and (context in chunk_text or chunk_text in context) for context in normalized_contexts):
            return chunk
    return None


def _float_from_item(item: dict[str, object], metadata: dict[str, object], key: str) -> float | None:
    for source in (item, metadata):
        value = source.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _metadata_payload(
    metadata: dict[str, object],
    *,
    question_type: str,
    generator_mode: str,
    source: str,
    difficulty: str,
) -> dict[str, object]:
    payload = dict(metadata)
    payload.update(
        {
            "question_type": question_type,
            "generator_mode": generator_mode,
            "source": source,
            "difficulty": difficulty,
        }
    )
    return {key: _json_safe(value) for key, value in payload.items()}


def _metadata_json(metadata: dict[str, object]) -> str:
    if not metadata:
        return ""
    return json.dumps(_json_safe(metadata), ensure_ascii=False, sort_keys=True)


def _json_safe(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


def _read_review_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _merge_review_row(base: dict[str, object], row: dict[str, str]) -> dict[str, object]:
    item = dict(base)
    item["caseId"] = _stripped(row.get("caseId")) or str(item.get("caseId") or "")
    item["question"] = _stripped(row.get("question")) or str(item.get("question") or "")
    item["expectedAnswer"] = _stripped(row.get("expectedAnswer")) or str(item.get("expectedAnswer") or "")

    for field_name in LIST_FIELDS:
        if field_name in row:
            item[field_name] = _split_ids(row.get(field_name) or "")

    top_k = _stripped(row.get("evaluationTopK"))
    if top_k:
        item["evaluationTopK"] = max(1, int(top_k))

    base_notes = _stripped(row.get("notes")) or str(item.get("notes") or "")
    human_notes = _stripped(row.get("humanNotes"))
    if human_notes:
        item["notes"] = f"{base_notes}\n人工审核备注：{human_notes}".strip()
    else:
        item["notes"] = base_notes
    return item


def _status_from_review(row: dict[str, str], item: dict[str, object]) -> str:
    decision = _normalize_token(row.get("humanDecision"))
    if not decision:
        decision = _normalize_token(row.get("reviewStatus"))
    if decision in APPROVED_DECISIONS:
        return "ACTIVE"
    if decision in REJECTED_DECISIONS:
        return "REJECTED"
    if decision in DRAFT_DECISIONS:
        return "DRAFT"
    if decision in SKIP_DECISIONS:
        return "SKIP"

    status = _stripped(row.get("status")) or str(item.get("status") or "DRAFT")
    return _normalize_case_status(status)


def _review_decision_warning(case_id: str, row: dict[str, str]) -> str:
    decision = _normalize_token(row.get("humanDecision"))
    if not decision:
        return ""
    known_decisions = APPROVED_DECISIONS | REJECTED_DECISIONS | DRAFT_DECISIONS | SKIP_DECISIONS
    if decision in known_decisions:
        return ""
    return f"caseId={case_id} 的 humanDecision={row.get('humanDecision')} 未识别，已回退到 status/reviewStatus。"


def _normalize_case_status(status: str) -> str:
    token = _normalize_token(status)
    if token in APPROVED_DECISIONS:
        return "ACTIVE"
    if token in REJECTED_DECISIONS:
        return "REJECTED"
    if token in DRAFT_DECISIONS:
        return "DRAFT"
    if token in {"archive", "archived", "归档"}:
        return "ARCHIVED"
    if token in {"active", "draft", "rejected", "archived"}:
        return token.upper()
    return "DRAFT"


def _validate_import_item(case_id: str, item: dict[str, object]) -> list[str]:
    warnings: list[str] = []
    if not case_id:
        warnings.append("缺少 caseId。")
    if len(case_id) > 120:
        warnings.append(f"caseId={case_id} 超过 120 个字符。")
    if not str(item.get("question") or "").strip():
        warnings.append(f"caseId={case_id} 缺少 question。")
    if item.get("status") == "ACTIVE" and not item.get("requiredChunkIds"):
        warnings.append(f"caseId={case_id} 已通过但缺少 requiredChunkIds。")
    if item.get("status") == "ACTIVE" and not item.get("expectedAnswer"):
        warnings.append(f"caseId={case_id} 已通过但缺少 expectedAnswer。")
    for field_name in LIST_FIELDS:
        invalid_ids = [value for value in item.get(field_name) or [] if not _is_uuid(value)]
        if invalid_ids:
            warnings.append(
                f"caseId={case_id} 的 {field_name} 包含非 UUID 值：{', '.join(invalid_ids[:3])}。"
            )
    return warnings


def _prune_import_item(item: dict[str, object]) -> dict[str, object]:
    return {field_name: item.get(field_name) for field_name in BACKEND_IMPORT_FIELDS if field_name in item}


def _split_ids(value: str) -> list[str]:
    text = value.strip()
    if text in {"[]", "-"}:
        return []
    if text.startswith("["):
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError(f"Expected list value, got: {value}")
        return [str(item).strip() for item in data if str(item).strip()]
    return _dedupe([part.strip() for part in re.split(r"[;,\n\r\t，、 ]+", text) if part.strip()])


def _join_ids(values: Iterable[str]) -> str:
    return ";".join(values)


def _dedupe(values: Iterable[str]) -> list[str]:
    results: list[str] = []
    for value in values:
        if value and value not in results:
            results.append(value)
    return results


def _normalize_token(value: object) -> str:
    return _stripped(value).lower().replace(" ", "_").replace("-", "_")


def _stripped(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _optional_str(value: object) -> str | None:
    text = _stripped(value)
    return text or None


def _is_uuid(value: object) -> bool:
    try:
        uuid.UUID(str(value))
    except (TypeError, ValueError):
        return False
    return True
