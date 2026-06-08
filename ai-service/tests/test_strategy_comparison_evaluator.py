import pytest

from app.rag.evaluators import (
    OfflineEvaluationCase,
    OfflineStrategyRun,
    evaluate_run,
    evaluate_strategy_comparison,
)
from app.schemas.common import SourceMetadata


def test_evaluate_run_scores_recall_precision_mrr_and_citation_hit() -> None:
    evaluation_case = OfflineEvaluationCase(
        case_id="rag-rewrite",
        question="How does advanced RAG rewrite a query?",
        relevant_chunk_ids={"advanced-rewrite", "advanced-rerank"},
        expected_citation_chunk_ids={"advanced-rewrite"},
    )
    run = OfflineStrategyRun(
        case_id="rag-rewrite",
        strategy_name="advanced-rag",
        retrieved=[
            _source("advanced-doc", "advanced-rewrite"),
            _source("other-doc", "crud-note"),
            _source("advanced-doc", "advanced-rerank"),
        ],
        citations=[_source("advanced-doc", "advanced-rewrite")],
    )

    metrics = evaluate_run(evaluation_case, run, k=2)

    assert metrics.recall_at_k == 0.5
    assert metrics.precision_at_k == 0.5
    assert metrics.mrr == 1.0
    assert metrics.citation_hit == 1.0


def test_strategy_comparison_prefers_advanced_rag_fixture() -> None:
    cases = [
        OfflineEvaluationCase(
            case_id="metadata-rerank",
            question="How should RAG use metadata filters and rerank?",
            relevant_chunk_ids={"advanced-filter", "advanced-rerank"},
            expected_citation_chunk_ids={"advanced-rerank"},
        ),
        OfflineEvaluationCase(
            case_id="parent-child",
            question="Why hydrate parent child context?",
            relevant_chunk_ids={"advanced-parent", "advanced-child"},
            expected_citation_chunk_ids={"advanced-parent"},
        ),
    ]
    runs = [
        OfflineStrategyRun(
            case_id="metadata-rerank",
            strategy_name="basic-rag",
            retrieved=[
                _source("crud-doc", "crud-note"),
                _source("advanced-doc", "advanced-filter"),
            ],
            citations=[_source("crud-doc", "crud-note")],
        ),
        OfflineStrategyRun(
            case_id="parent-child",
            strategy_name="basic-rag",
            retrieved=[
                _source("basic-doc", "single-child"),
                _source("advanced-doc", "advanced-child"),
            ],
            citations=[],
        ),
        OfflineStrategyRun(
            case_id="metadata-rerank",
            strategy_name="advanced-rag",
            retrieved=[
                _source("advanced-doc", "advanced-rerank"),
                _source("advanced-doc", "advanced-filter"),
            ],
            citations=[_source("advanced-doc", "advanced-rerank")],
        ),
        OfflineStrategyRun(
            case_id="parent-child",
            strategy_name="advanced-rag",
            retrieved=[
                _source("advanced-doc", "advanced-parent"),
                _source("advanced-doc", "advanced-child"),
            ],
            citations=[_source("advanced-doc", "advanced-parent")],
        ),
    ]

    comparison = evaluate_strategy_comparison(cases, runs, k=2)

    basic = comparison.metrics_by_strategy["basic-rag"]
    advanced = comparison.metrics_by_strategy["advanced-rag"]

    assert advanced.recall_at_k == 1.0
    assert advanced.precision_at_k == 1.0
    assert advanced.mrr == 1.0
    assert advanced.citation_hit == 1.0
    assert advanced.recall_at_k > basic.recall_at_k
    assert advanced.precision_at_k > basic.precision_at_k
    assert advanced.mrr > basic.mrr
    assert advanced.citation_hit > basic.citation_hit


def test_strategy_comparison_prefers_graph_rag_for_relationship_questions() -> None:
    cases = [
        OfflineEvaluationCase(
            case_id="graph-relationship",
            question="How does GraphRAG connect entities with retrieval relationships?",
            relevant_chunk_ids={"graph-entity-extraction", "graph-relationship-traversal"},
            expected_citation_chunk_ids={"graph-relationship-traversal"},
        ),
        OfflineEvaluationCase(
            case_id="graph-expansion",
            question="Which graph expansion terms support relationship-aware citations?",
            relevant_chunk_ids={"graph-expansion-terms", "graph-citation-context"},
            expected_citation_chunk_ids={"graph-citation-context"},
        ),
    ]
    runs = [
        OfflineStrategyRun(
            case_id="graph-relationship",
            strategy_name="advanced-rag",
            retrieved=[
                _source("advanced-doc", "query-rewrite-note"),
                _source("graph-doc", "graph-entity-extraction"),
            ],
            citations=[_source("advanced-doc", "query-rewrite-note")],
        ),
        OfflineStrategyRun(
            case_id="graph-expansion",
            strategy_name="advanced-rag",
            retrieved=[
                _source("advanced-doc", "rerank-note"),
                _source("graph-doc", "graph-expansion-terms"),
            ],
            citations=[],
        ),
        OfflineStrategyRun(
            case_id="graph-relationship",
            strategy_name="graph-rag",
            retrieved=[
                _source("graph-doc", "graph-relationship-traversal"),
                _source("graph-doc", "graph-entity-extraction"),
            ],
            citations=[_source("graph-doc", "graph-relationship-traversal")],
        ),
        OfflineStrategyRun(
            case_id="graph-expansion",
            strategy_name="graph-rag",
            retrieved=[
                _source("graph-doc", "graph-citation-context"),
                _source("graph-doc", "graph-expansion-terms"),
            ],
            citations=[_source("graph-doc", "graph-citation-context")],
        ),
    ]

    comparison = evaluate_strategy_comparison(cases, runs, k=2)

    advanced = comparison.metrics_by_strategy["advanced-rag"]
    graph = comparison.metrics_by_strategy["graph-rag"]

    assert graph.recall_at_k == 1.0
    assert graph.precision_at_k == 1.0
    assert graph.mrr == 1.0
    assert graph.citation_hit == 1.0
    assert graph.recall_at_k > advanced.recall_at_k
    assert graph.precision_at_k > advanced.precision_at_k
    assert graph.mrr > advanced.mrr
    assert graph.citation_hit > advanced.citation_hit


def test_strategy_comparison_rejects_unknown_case() -> None:
    with pytest.raises(ValueError, match="unknown evaluation case"):
        evaluate_strategy_comparison(
            cases=[],
            runs=[
                OfflineStrategyRun(
                    case_id="missing-case",
                    strategy_name="basic-rag",
                    retrieved=[],
                )
            ],
            k=2,
        )


def _source(document_id: str, chunk_id: str) -> SourceMetadata:
    return SourceMetadata(
        document_id=document_id,
        chunk_id=chunk_id,
        title=chunk_id.replace("-", " ").title(),
        metadata={"content_preview": chunk_id},
    )
