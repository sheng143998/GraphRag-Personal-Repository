import re

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
        retrieval_score = (
            _structured_retrieval_score(structured_metrics)
            if structured_metrics is not None
            else min(1.0, len(payload.citations) / 5) if payload.citations else 0.0
        )
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


def _content_tokens(value: str) -> set[str]:
    tokens = {
        token
        for token in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", value.lower())
        if len(token) > 2
    }
    return tokens
