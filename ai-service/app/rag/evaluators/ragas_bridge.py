from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Sequence

from app.schemas.common import SourceMetadata
from app.schemas.rag import RagEvaluateRequest, RagEvaluationCase


DEFAULT_ID_METRICS = ("IDBasedContextPrecision", "IDBasedContextRecall")
DEFAULT_LLM_METRICS = ("Faithfulness", "ResponseRelevancy", "FactualCorrectness")


class RagasUnavailableError(RuntimeError):
    """Raised when the optional RAGAS runtime is not installed or cannot load."""


def build_ragas_sample(payload: RagEvaluateRequest) -> dict[str, object]:
    """Map the project evaluator payload to a RAGAS SingleTurnSample-like row.

    The returned value intentionally stays as a plain dict so the main FastAPI
    service does not import RAGAS on the hot path.
    """

    sample: dict[str, object] = {
        "user_input": payload.question,
        "retrieved_contexts": [source_to_ragas_context(source) for source in payload.citations],
        "retrieved_context_ids": [source.chunk_id for source in payload.citations],
    }
    if payload.generated_answer is not None:
        sample["response"] = payload.generated_answer
    if payload.expected_answer is not None:
        sample["reference"] = payload.expected_answer

    if payload.evaluation_case is not None:
        reference_ids = evaluation_case_reference_context_ids(payload.evaluation_case)
        if reference_ids:
            sample["reference_context_ids"] = reference_ids
        sample["metadata"] = {
            "case_id": payload.evaluation_case.case_id,
            "strategy_name": payload.strategy_name,
            "knowledge_base_id": payload.context.knowledge_base_id,
            "top_k": payload.evaluation_case.top_k,
        }

    return sample


def build_ragas_dataset_rows(payloads: Iterable[RagEvaluateRequest]) -> list[dict[str, object]]:
    return [build_ragas_sample(payload) for payload in payloads]


def source_to_ragas_context(source: SourceMetadata) -> str:
    metadata = source.metadata or {}
    text = _first_non_empty(
        metadata.get("content_preview"),
        metadata.get("snippet"),
        metadata.get("context"),
        metadata.get("text"),
        metadata.get("content"),
    )
    if text:
        return text

    parts = [source.title]
    if source.source_path:
        parts.append(f"source: {source.source_path}")
    if source.page_number is not None:
        parts.append(f"page: {source.page_number}")
    if source.sheet_name:
        parts.append(f"sheet: {source.sheet_name}")
    return "\n".join(part for part in parts if part)


def evaluation_case_reference_context_ids(evaluation_case: RagEvaluationCase) -> list[str]:
    ordered_ids: list[str] = []
    for group in (
        evaluation_case.required_chunk_ids,
        evaluation_case.supporting_chunk_ids,
        evaluation_case.acceptable_chunk_ids,
        evaluation_case.relevant_chunk_ids,
        evaluation_case.citation_chunk_ids,
        evaluation_case.expected_citation_chunk_ids,
    ):
        for chunk_id in group:
            if chunk_id and chunk_id not in ordered_ids:
                ordered_ids.append(chunk_id)
    return ordered_ids


def write_jsonl(rows: Iterable[dict[str, object]], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def read_jsonl(path: str | Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def load_ragas_metrics(metric_names: Sequence[str]) -> list[object]:
    try:
        from ragas import metrics as ragas_metrics
    except Exception as exc:  # pragma: no cover - depends on optional runtime
        raise RagasUnavailableError(
            "RAGAS is not installed in this Python environment. "
            "Install the optional RAGAS runtime before running RAGAS scoring."
        ) from exc

    loaded: list[object] = []
    for metric_name in metric_names:
        metric = _resolve_metric(ragas_metrics, metric_name)
        loaded.append(metric() if isinstance(metric, type) else metric)
    return loaded


def evaluate_with_ragas(
    rows: Iterable[dict[str, object]],
    *,
    metric_names: Sequence[str] = DEFAULT_ID_METRICS,
    **kwargs: object,
) -> object:
    try:
        from ragas import EvaluationDataset, evaluate
    except Exception as exc:  # pragma: no cover - depends on optional runtime
        raise RagasUnavailableError(
            "RAGAS is not installed in this Python environment. "
            "Install it in an isolated environment before running RAGAS scoring."
        ) from exc

    dataset = EvaluationDataset.from_list(list(rows))
    return evaluate(dataset, metrics=load_ragas_metrics(metric_names), **kwargs)


def _resolve_metric(ragas_metrics: object, metric_name: str) -> object:
    aliases = {
        "id_context_precision": "IDBasedContextPrecision",
        "id_context_recall": "IDBasedContextRecall",
        "answer_relevancy": "ResponseRelevancy",
        "response_relevancy": "ResponseRelevancy",
        "faithfulness": "Faithfulness",
        "factual_correctness": "FactualCorrectness",
    }
    lookup_name = aliases.get(metric_name, metric_name)
    try:
        return getattr(ragas_metrics, lookup_name)
    except AttributeError as exc:
        raise ValueError(f"Unsupported or unavailable RAGAS metric: {metric_name}") from exc


def _first_non_empty(*values: object) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""
