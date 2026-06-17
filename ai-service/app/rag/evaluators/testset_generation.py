from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from app.schemas.ingest import ChunkRecord


DEFAULT_CASES_PER_DOCUMENT = 3
DEFAULT_TOP_K = 5


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
            "reviewStatus": self.review_status,
            "reviewSuggestion": self.review_suggestion,
            "confidence": self.confidence,
        }

    def to_review_row(self) -> dict[str, object]:
        return {
            "caseId": self.case_id,
            "status": self.status,
            "reviewStatus": self.review_status,
            "question": self.question,
            "expectedAnswer": self.expected_answer,
            "requiredChunkIds": ";".join(self.required_chunk_ids),
            "supportingChunkIds": ";".join(self.supporting_chunk_ids),
            "acceptableChunkIds": ";".join(self.acceptable_chunk_ids),
            "citationChunkIds": ";".join(self.citation_chunk_ids),
            "relevantDocumentIds": ";".join(self.relevant_document_ids),
            "confidence": self.confidence,
            "reviewSuggestion": self.review_suggestion,
            "humanDecision": "",
            "humanNotes": "",
        }


def generate_case_drafts(
    chunks: Sequence[ChunkRecord],
    *,
    cases_per_document: int = DEFAULT_CASES_PER_DOCUMENT,
    top_k: int = DEFAULT_TOP_K,
) -> list[EvaluationCaseDraft]:
    grouped = _group_chunks(chunks)
    drafts: list[EvaluationCaseDraft] = []
    for document_id, document_chunks in grouped.items():
        candidates = _rank_candidates(document_chunks)
        for index, chunk in enumerate(candidates[: max(1, cases_per_document)], start=1):
            siblings = _supporting_siblings(chunk, candidates)
            drafts.append(_draft_from_chunk(chunk, siblings=siblings, ordinal=index, top_k=top_k))
    return drafts


def write_import_json(drafts: Iterable[EvaluationCaseDraft], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps([draft.to_import_item() for draft in drafts], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_review_csv(drafts: Iterable[EvaluationCaseDraft], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [draft.to_review_row() for draft in drafts]
    fieldnames = [
        "caseId",
        "status",
        "reviewStatus",
        "question",
        "expectedAnswer",
        "requiredChunkIds",
        "supportingChunkIds",
        "acceptableChunkIds",
        "citationChunkIds",
        "relevantDocumentIds",
        "confidence",
        "reviewSuggestion",
        "humanDecision",
        "humanNotes",
    ]
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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
        question=f"根据《{title}》，{topic} 的关键处理方式是什么？",
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
    if any(marker in text for marker in ("步骤", "原因", "方案", "风险", "对比", "排查", "实现")):
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
        answer = answer[:520].rsplit(" ", 1)[0].strip()
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


def _confidence(chunk: ChunkRecord, answer: str, supporting_ids: list[str]) -> float:
    metadata = chunk.metadata or {}
    quality = float(metadata.get("quality_score") or 1.0)
    length_bonus = 0.1 if len(answer) >= 120 else 0.0
    support_bonus = 0.1 if supporting_ids else 0.0
    return round(min(0.95, max(0.25, (quality * 0.65) + length_bonus + support_bonus)), 2)


def _clean_content(text: str) -> str:
    text = re.sub(r"```.*?```", "代码片段略。", text, flags=re.S)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[。！？.!?])\s+", text) if part.strip()]


def _dedupe(values: Iterable[str]) -> list[str]:
    results: list[str] = []
    for value in values:
        if value and value not in results:
            results.append(value)
    return results


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
