from dataclasses import dataclass, field
from typing import Iterable

from app.schemas.common import SourceMetadata


@dataclass(frozen=True)
class OfflineEvaluationCase:
    case_id: str
    question: str
    required_chunk_ids: set[str] = field(default_factory=set)
    supporting_chunk_ids: set[str] = field(default_factory=set)
    acceptable_chunk_ids: set[str] = field(default_factory=set)
    citation_chunk_ids: set[str] = field(default_factory=set)
    relevant_chunk_ids: set[str] = field(default_factory=set)
    relevant_document_ids: set[str] = field(default_factory=set)
    expected_citation_chunk_ids: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class OfflineStrategyRun:
    case_id: str
    strategy_name: str
    retrieved: list[SourceMetadata]
    citations: list[SourceMetadata] = field(default_factory=list)


@dataclass(frozen=True)
class RetrievalMetrics:
    recall_at_k: float
    precision_at_k: float
    chunk_recall_at_k: float
    document_recall_at_k: float
    evidence_recall_at_k: float
    mrr: float
    citation_hit: float


@dataclass(frozen=True)
class StrategyComparison:
    k: int
    metrics_by_strategy: dict[str, RetrievalMetrics]


def evaluate_strategy_comparison(
    cases: Iterable[OfflineEvaluationCase],
    runs: Iterable[OfflineStrategyRun],
    *,
    k: int,
) -> StrategyComparison:
    if k <= 0:
        raise ValueError("k must be greater than 0")

    cases_by_id = {case.case_id: case for case in cases}
    metric_values: dict[str, list[RetrievalMetrics]] = {}

    for run in runs:
        try:
            case = cases_by_id[run.case_id]
        except KeyError as exc:
            raise ValueError(f"Run references unknown evaluation case: {run.case_id}") from exc
        metric_values.setdefault(run.strategy_name, []).append(evaluate_run(case, run, k=k))

    return StrategyComparison(
        k=k,
        metrics_by_strategy={
            strategy_name: _average_metrics(values)
            for strategy_name, values in metric_values.items()
        },
    )


def evaluate_run(
    case: OfflineEvaluationCase,
    run: OfflineStrategyRun,
    *,
    k: int,
) -> RetrievalMetrics:
    if k <= 0:
        raise ValueError("k must be greater than 0")

    top_k = run.retrieved[:k]
    chunk_targets = _chunk_targets(case)
    document_targets = case.relevant_document_ids
    evidence_total = len(chunk_targets) + len(document_targets)
    relevant_hits = sum(1 for source in top_k if _is_relevant(case, source))
    first_relevant_rank = _first_relevant_rank(case, top_k)
    chunk_hits = {
        source.chunk_id
        for source in top_k
        if source.chunk_id in chunk_targets
    }
    document_hits = {
        source.document_id
        for source in top_k
        if source.document_id in document_targets
    }
    precision_denominator = len(top_k)

    return RetrievalMetrics(
        recall_at_k=(relevant_hits / evidence_total) if evidence_total else 0.0,
        precision_at_k=(relevant_hits / precision_denominator) if precision_denominator else 0.0,
        chunk_recall_at_k=(len(chunk_hits) / len(chunk_targets)) if chunk_targets else 0.0,
        document_recall_at_k=(len(document_hits) / len(document_targets)) if document_targets else 0.0,
        evidence_recall_at_k=(relevant_hits / evidence_total) if evidence_total else 0.0,
        mrr=(1.0 / first_relevant_rank) if first_relevant_rank else 0.0,
        citation_hit=1.0 if any(_is_expected_citation(case, source) for source in run.citations) else 0.0,
    )


def _average_metrics(values: list[RetrievalMetrics]) -> RetrievalMetrics:
    if not values:
        return RetrievalMetrics(
            recall_at_k=0.0,
            precision_at_k=0.0,
            chunk_recall_at_k=0.0,
            document_recall_at_k=0.0,
            evidence_recall_at_k=0.0,
            mrr=0.0,
            citation_hit=0.0,
        )

    total = len(values)
    return RetrievalMetrics(
        recall_at_k=sum(value.recall_at_k for value in values) / total,
        precision_at_k=sum(value.precision_at_k for value in values) / total,
        chunk_recall_at_k=sum(value.chunk_recall_at_k for value in values) / total,
        document_recall_at_k=sum(value.document_recall_at_k for value in values) / total,
        evidence_recall_at_k=sum(value.evidence_recall_at_k for value in values) / total,
        mrr=sum(value.mrr for value in values) / total,
        citation_hit=sum(value.citation_hit for value in values) / total,
    )


def _first_relevant_rank(case: OfflineEvaluationCase, sources: list[SourceMetadata]) -> int | None:
    for index, source in enumerate(sources, start=1):
        if _is_relevant(case, source):
            return index
    return None


def _is_expected_citation(case: OfflineEvaluationCase, source: SourceMetadata) -> bool:
    citation_targets = case.citation_chunk_ids or case.expected_citation_chunk_ids
    if citation_targets:
        return source.chunk_id in citation_targets
    return _is_relevant(case, source)


def _is_relevant(case: OfflineEvaluationCase, source: SourceMetadata) -> bool:
    return source.chunk_id in _chunk_targets(case) or source.document_id in case.relevant_document_ids


def _chunk_targets(case: OfflineEvaluationCase) -> set[str]:
    layered_targets = (
        case.required_chunk_ids
        | case.supporting_chunk_ids
        | case.acceptable_chunk_ids
    )
    return layered_targets or case.relevant_chunk_ids
