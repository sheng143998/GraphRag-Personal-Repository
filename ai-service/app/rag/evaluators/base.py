import re
from dataclasses import dataclass

from app.schemas.rag import RagEvaluateRequest, RagEvaluationResult
from app.rag.evaluators.strategy_comparison import (
    OfflineEvaluationCase,
    OfflineStrategyRun,
    evaluate_run,
)


class BaseRagEvaluator:
    async def evaluate(self, payload: RagEvaluateRequest) -> RagEvaluationResult:
        raise NotImplementedError


class SimpleRagEvaluator(BaseRagEvaluator):
    async def evaluate(self, payload: RagEvaluateRequest) -> RagEvaluationResult:
        generated_answer = payload.generated_answer or ""
        answer_alignment = _answer_alignment_score(
            payload.expected_answer,
            generated_answer,
        )
        citation_support = _citation_support_score(generated_answer, payload.citations)
        if payload.citations:
            grounded_score = max(0.1, min(1.0, (citation_support * 0.6) + (answer_alignment * 0.4)))
        else:
            grounded_score = min(0.2, answer_alignment * 0.2)
        structured_metrics = _structured_retrieval_metrics(payload)
        base_retrieval_score = (
            _structured_retrieval_score(structured_metrics)
            if structured_metrics is not None
            else min(1.0, len(payload.citations) / 5) if payload.citations else 0.0
        )
        graph_metrics = _graph_retrieval_metrics(payload)
        retrieval_score = _combine_retrieval_scores(base_retrieval_score, graph_metrics)
        notes = [
            "Skeleton evaluator uses citation support and answer alignment heuristic scoring.",
        ]
        if structured_metrics is None:
            notes.append("No structured evaluation case supplied; retrieval quality uses citation-count heuristic.")
        else:
            notes.append(
                "Structured evaluation case scored "
                f"recall@k={structured_metrics.recall_at_k:.2f}, "
                f"precision@k={structured_metrics.precision_at_k:.2f}, "
                f"mrr={structured_metrics.mrr:.2f}, "
                f"citation_hit={structured_metrics.citation_hit:.2f}."
            )
        if graph_metrics is not None:
            notes.append(
                "GraphRAG metadata scored "
                f"entity_coverage={graph_metrics.entity_coverage:.2f}, "
                f"relationship_hit={graph_metrics.relationship_hit:.2f}, "
                f"expansion_term_hit={graph_metrics.expansion_term_hit:.2f}."
            )
        return RagEvaluationResult(
            grounded_score=grounded_score,
            retrieval_score=retrieval_score,
            notes=notes,
        )


def _answer_alignment_score(expected_answer: str | None, generated_answer: str) -> float:
    if not expected_answer:
        return 1.0
    return _token_overlap_score(expected_answer, generated_answer)


def _citation_support_score(generated_answer: str, citations: list) -> float:
    if not citations:
        return 0.0

    previews = []
    for citation in citations:
        metadata = getattr(citation, "metadata", None) or {}
        preview = metadata.get("content_preview") or metadata.get("snippet")
        if preview:
            previews.append(str(preview))
        title = getattr(citation, "title", None)
        if title:
            previews.append(str(title))

    if not previews:
        return 0.7
    return max(0.2, _token_overlap_score(generated_answer, " ".join(previews)))


def _token_overlap_score(left: str, right: str) -> float:
    left_tokens = _content_tokens(left)
    right_tokens = _content_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens)


def _structured_retrieval_metrics(payload: RagEvaluateRequest):
    evaluation_case = payload.evaluation_case
    if evaluation_case is None:
        return None
    if (
        not evaluation_case.relevant_chunk_ids
        and not evaluation_case.relevant_document_ids
        and not evaluation_case.expected_citation_chunk_ids
    ):
        return None

    return evaluate_run(
        OfflineEvaluationCase(
            case_id=evaluation_case.case_id,
            question=payload.question,
            relevant_chunk_ids=set(evaluation_case.relevant_chunk_ids),
            relevant_document_ids=set(evaluation_case.relevant_document_ids),
            expected_citation_chunk_ids=set(evaluation_case.expected_citation_chunk_ids),
        ),
        OfflineStrategyRun(
            case_id=evaluation_case.case_id,
            strategy_name=payload.strategy_name,
            retrieved=payload.citations,
            citations=payload.citations,
        ),
        k=max(1, evaluation_case.top_k),
    )


def _structured_retrieval_score(metrics) -> float:
    return (
        metrics.recall_at_k
        + metrics.precision_at_k
        + metrics.mrr
        + metrics.citation_hit
    ) / 4


@dataclass(frozen=True)
class GraphRetrievalMetrics:
    entity_coverage: float
    relationship_hit: float
    expansion_term_hit: float

    @property
    def score(self) -> float:
        return (self.entity_coverage + self.relationship_hit + self.expansion_term_hit) / 3


def _graph_retrieval_metrics(payload: RagEvaluateRequest) -> GraphRetrievalMetrics | None:
    if not payload.citations:
        return None

    graph_entities: set[str] = set()
    matched_entities: set[str] = set()
    expansion_terms: set[str] = set()
    matched_expansion_terms: set[str] = set()
    relationship_hit = False

    for citation in payload.citations:
        metadata = getattr(citation, "metadata", None) or {}
        preview = str(metadata.get("content_preview") or "")
        title = str(getattr(citation, "title", "") or "")
        searchable_text = f"{title} {preview}".lower()

        graph_entities.update(_string_values(metadata.get("graph_entities")))
        matched_entities.update(_string_values(metadata.get("graph_matched_entities")))
        matched_entities.update(_string_values(metadata.get("persisted_graph_matched_entities")))

        citation_expansion_terms = set(_string_values(metadata.get("graph_expansion_terms")))
        expansion_terms.update(citation_expansion_terms)
        matched_expansion_terms.update(
            term
            for term in citation_expansion_terms
            if term.lower() in searchable_text
        )

        if _relationship_count(metadata.get("graph_relationship_count")) > 0:
            relationship_hit = True
        if _relationship_count(metadata.get("persisted_graph_relationship_count")) > 0:
            relationship_hit = True
        if _string_values(metadata.get("graph_traversal_relationships")):
            relationship_hit = True

    if not graph_entities and not expansion_terms and not relationship_hit:
        return None

    return GraphRetrievalMetrics(
        entity_coverage=(len(matched_entities & graph_entities) / len(graph_entities)) if graph_entities else 0.0,
        relationship_hit=1.0 if relationship_hit else 0.0,
        expansion_term_hit=(len(matched_expansion_terms) / len(expansion_terms)) if expansion_terms else 0.0,
    )


def _combine_retrieval_scores(base_score: float, graph_metrics: GraphRetrievalMetrics | None) -> float:
    if graph_metrics is None:
        return base_score
    return (base_score * 0.7) + (graph_metrics.score * 0.3)


def _string_values(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        results: list[str] = []
        for item in value:
            if isinstance(item, dict):
                results.extend(str(candidate) for candidate in item.values() if candidate)
            elif item:
                results.append(str(item))
        return results
    if isinstance(value, dict):
        return [str(item) for item in value.values() if item]
    return [str(value)]


def _relationship_count(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _content_tokens(value: str) -> set[str]:
    tokens = {
        token
        for token in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", value.lower())
        if len(token) > 2
    }
    return tokens
