import asyncio
import os

os.environ["AI_RAG_USE_DATABASE"] = "false"
os.environ["MODEL_PROVIDER"] = "stub"
os.environ["LLM_PROVIDER"] = "stub"
os.environ["EMBEDDING_PROVIDER"] = "stub"
os.environ["RERANK_PROVIDER"] = "stub"

from app.core.constants import DocumentType, FileType
from app.db.repositories import _hybrid_weights, repository
from app.schemas.common import SourceMetadata
from app.schemas.ingest import ChunkRecord, DocumentIngestRequest, DocumentPayload
from app.schemas.rag import RagEvaluateRequest, RagEvaluationCase, RagQueryRequest, RagRequestContext
from app.services.ingest_service import IngestService
from app.services.rag_service import RagService


def test_advanced_rag_applies_rewrite_filters_fusion_parent_context_and_rerank() -> None:
    response = asyncio.run(_advanced_query())

    assert response.citations
    assert all(source.metadata["topic"] == "advanced-rag" for source in response.citations)
    assert response.trace.attributes["rewritten_query"] != response.question
    assert "retrieval augmented generation" in str(response.trace.attributes["rewritten_query"])
    assert response.trace.attributes["retrieval_options"] == {"vectorWeight": 0.6, "keywordWeight": 0.4}

    step_statuses = {step.name: step.status for step in response.trace.steps}
    assert step_statuses["query_rewrite"] == "completed"
    assert step_statuses["multi_query_expand"] == "completed"
    assert step_statuses["fusion"] == "completed"
    assert step_statuses["parent_child_context"] == "completed"
    assert step_statuses["rerank"] == "completed"
    retrieve_step = next(step for step in response.trace.steps if step.name == "retrieve")
    assert retrieve_step.payload["retrieval_options_enabled"] is True
    context_step = next(step for step in response.trace.steps if step.name == "parent_child_context")
    assert context_step.payload["context_compression_enabled"] is True

    top_source = response.citations[0]
    assert top_source.rerank_score is not None
    assert top_source.metadata["parent_child_mode"] == "neighbor-window"
    assert top_source.metadata["context_compression_mode"] == "query-aware-sentence-pack"
    assert len(top_source.metadata["context_source_chunk_ids"]) >= 2
    assert top_source.metadata["matched_queries"]
    assert "Advanced RAG" in top_source.metadata["content_preview"]


def test_parent_child_context_uses_real_parent_chunk_when_available() -> None:
    _clear_in_memory_repository()
    repository.save_chunks(
        "doc-parent",
        "kb-parent-child",
        [
            ChunkRecord(
                chunk_id="parent-architecture",
                document_id="doc-parent",
                knowledge_base_id="kb-parent-child",
                title="Parent Architecture",
                chunk_index=0,
                content="Parent overview explains the complete Advanced RAG architecture.",
                metadata={},
            ),
            ChunkRecord(
                chunk_id="child-rewrite",
                document_id="doc-parent",
                knowledge_base_id="kb-parent-child",
                parent_chunk_id="parent-architecture",
                title="Child Rewrite",
                chunk_index=1,
                content="Query rewrite expands the user question before retrieval.",
                metadata={},
            ),
            ChunkRecord(
                chunk_id="child-rerank",
                document_id="doc-parent",
                knowledge_base_id="kb-parent-child",
                parent_chunk_id="parent-architecture",
                title="Child Rerank",
                chunk_index=2,
                content="Rerank scoring promotes the strongest citation evidence.",
                metadata={},
            ),
        ],
    )

    hydrated = repository.hydrate_parent_context([
        SourceMetadata(
            document_id="doc-parent",
            chunk_id="child-rerank",
            title="Child Rerank",
            score=0.9,
            metadata={"content_preview": "Rerank scoring promotes evidence."},
        )
    ])

    source = hydrated[0]
    assert source.metadata["parent_child_mode"] == "parent-child"
    assert source.metadata["parent_chunk_id"] == "parent-architecture"
    assert source.metadata["context_source_chunk_ids"] == [
        "parent-architecture",
        "child-rewrite",
        "child-rerank",
    ]
    assert "Parent overview" in source.metadata["content_preview"]
    assert "Query rewrite" in source.metadata["content_preview"]
    assert "Rerank scoring" in source.metadata["content_preview"]


def test_parent_child_context_falls_back_when_parent_chunk_is_missing() -> None:
    _clear_in_memory_repository()
    repository.save_chunks(
        "doc-missing-parent",
        "kb-parent-child",
        [
            ChunkRecord(
                chunk_id="child-a",
                document_id="doc-missing-parent",
                knowledge_base_id="kb-parent-child",
                parent_chunk_id="missing-parent",
                title="Child A",
                chunk_index=1,
                content="First child references a parent that is not stored.",
                metadata={},
            ),
            ChunkRecord(
                chunk_id="child-b",
                document_id="doc-missing-parent",
                knowledge_base_id="kb-parent-child",
                parent_chunk_id="missing-parent",
                title="Child B",
                chunk_index=2,
                content="Second child should still appear through neighbor fallback.",
                metadata={},
            ),
        ],
    )

    hydrated = repository.hydrate_parent_context([
        SourceMetadata(
            document_id="doc-missing-parent",
            chunk_id="child-a",
            title="Child A",
            score=0.9,
            metadata={"content_preview": "First child references a parent."},
        )
    ])

    source = hydrated[0]
    assert source.metadata["parent_child_mode"] == "neighbor-window"
    assert source.metadata["context_source_chunk_ids"] == ["child-a", "child-b"]
    assert "First child" in source.metadata["content_preview"]
    assert "Second child" in source.metadata["content_preview"]


def test_parent_child_context_compresses_long_parent_evidence() -> None:
    _clear_in_memory_repository()
    noisy_parent = "Background notes describe release chores and general setup details. " * 80
    repository.save_chunks(
        "doc-long-parent",
        "kb-parent-child",
        [
            ChunkRecord(
                chunk_id="parent-long",
                document_id="doc-long-parent",
                knowledge_base_id="kb-parent-child",
                title="Long Parent",
                chunk_index=0,
                content=noisy_parent,
                metadata={},
            ),
            ChunkRecord(
                chunk_id="child-evidence",
                document_id="doc-long-parent",
                knowledge_base_id="kb-parent-child",
                parent_chunk_id="parent-long",
                title="Evidence Child",
                chunk_index=1,
                content="Rerank evidence packing keeps the query matched sentence for Advanced RAG.",
                metadata={},
            ),
            ChunkRecord(
                chunk_id="child-noise",
                document_id="doc-long-parent",
                knowledge_base_id="kb-parent-child",
                parent_chunk_id="parent-long",
                title="Noise Child",
                chunk_index=2,
                content="Operational notes list unrelated cleanup details.",
                metadata={},
            ),
        ],
    )

    hydrated = repository.hydrate_parent_context([
        SourceMetadata(
            document_id="doc-long-parent",
            chunk_id="child-evidence",
            title="Evidence Child",
            score=0.9,
            metadata={
                "content_preview": "Rerank evidence packing keeps the query matched sentence.",
                "matched_queries": ["How does rerank evidence packing help Advanced RAG?"],
            },
        )
    ])

    source = hydrated[0]
    assert source.metadata["parent_child_mode"] == "parent-child"
    assert source.metadata["context_compression_mode"] == "query-aware-sentence-pack"
    assert source.metadata["context_original_chars"] > source.metadata["context_compressed_chars"]
    assert source.metadata["context_compressed_chars"] <= 1200
    assert "Rerank evidence packing" in source.metadata["content_preview"]


def test_rag_evaluation_scores_grounded_citations() -> None:
    response = asyncio.run(_evaluate_grounded_answer())

    assert response.result.grounded_score == 1.0
    assert response.result.retrieval_score > 0.0
    assert response.trace.status == "completed"


def test_rag_evaluation_penalizes_answer_mismatch() -> None:
    matched = asyncio.run(_evaluate_grounded_answer())
    mismatched = asyncio.run(_evaluate_mismatched_answer())

    assert matched.result.grounded_score > mismatched.result.grounded_score
    assert mismatched.result.grounded_score < 0.75
    assert matched.result.retrieval_score == mismatched.result.retrieval_score


def test_rag_evaluation_uses_structured_case_for_retrieval_metrics() -> None:
    structured = asyncio.run(_evaluate_structured_case())

    assert structured.result.retrieval_score == 1.0
    assert any("Structured evaluation case scored" in note for note in structured.result.notes)
    assert any("recall@k=1.00" in note for note in structured.result.notes)
    assert structured.trace.status == "completed"


def test_rag_evaluation_scores_graphrag_metadata_metrics() -> None:
    response = asyncio.run(_evaluate_graph_metadata_answer())

    assert response.result.retrieval_score > 0.2
    assert any("GraphRAG metadata scored" in note for note in response.result.notes)
    assert any("entity_coverage=1.00" in note for note in response.result.notes)
    assert any("relationship_hit=1.00" in note for note in response.result.notes)
    assert any("expansion_term_hit=1.00" in note for note in response.result.notes)


def test_graph_rag_extracts_entities_and_augments_retrieval_trace() -> None:
    response = asyncio.run(_graph_rag_query())

    assert response.citations
    assert response.trace.attributes["graph_entities"]
    assert response.trace.attributes["graph_relationships"]
    assert "GraphRAG" in response.trace.attributes["graph_augmented_query"]
    assert response.trace.attributes["persisted_graph_matches"]["matched_entities"]
    assert response.trace.attributes["persisted_graph_matches"]["relationship_count"] > 0
    assert response.trace.attributes["graph_expansion_terms"]
    assert response.trace.attributes["graph_traversal_relationships"]
    step_statuses = {step.name: step.status for step in response.trace.steps}
    assert step_statuses["graph_extract"] == "completed"
    assert response.citations[0].metadata["graph_entities"]
    assert response.citations[0].metadata["graph_relationship_count"] > 0
    assert response.citations[0].metadata["persisted_graph_matched_entities"]
    assert response.citations[0].metadata["persisted_graph_relationship_count"] > 0
    assert response.citations[0].metadata["graph_expansion_terms"]
    assert response.citations[0].metadata["graph_traversal_relationships"]


def test_hybrid_weight_options_are_normalized_and_bounded() -> None:
    assert _hybrid_weights({"vectorWeight": 6, "keywordWeight": 4}) == (0.6, 0.4)
    assert _hybrid_weights({"vector_weight": -1, "keyword_weight": 2}) == (0.0, 1.0)
    assert _hybrid_weights({"vectorWeight": 0, "keywordWeight": 0}) == (0.7, 0.3)
    assert _hybrid_weights({"vectorWeight": "bad", "keywordWeight": "bad"}) == (0.7, 0.3)


async def _advanced_query():
    _clear_in_memory_repository()
    ingest_service = IngestService()
    rag_service = RagService()

    await ingest_service.ingest_document(
        _document(
            knowledge_base_id="kb-test-advanced",
            document_id="22222222-2222-2222-2222-222222222222",
            title="Advanced RAG Notes",
            topic="advanced-rag",
            content=(
                "Advanced RAG uses query rewrite, multi query retrieval, hybrid search, "
                "metadata filters, parent child chunk context, and rerank scoring. "
                * 12
            ),
        )
    )
    await ingest_service.ingest_document(
        _document(
            knowledge_base_id="kb-test-advanced",
            document_id="33333333-3333-3333-3333-333333333333",
            title="Basic CRUD Notes",
            topic="crud",
            content=("Knowledge base CRUD manages create read update delete screens. " * 12),
        )
    )

    return await rag_service.query(
        RagQueryRequest(
            question="How should RAG use metadata filters and rerank?",
            top_k=2,
            strategy_name="advanced-rag",
            context=RagRequestContext(
                knowledge_base_id="kb-test-advanced",
                metadata_filters={"topic": "advanced-rag"},
                retrieval_options={"vectorWeight": 0.6, "keywordWeight": 0.4},
            ),
        )
    )


async def _graph_rag_query():
    _clear_in_memory_repository()
    ingest_service = IngestService()
    rag_service = RagService()

    await ingest_service.ingest_document(
        _document(
            knowledge_base_id="kb-test-graph",
            document_id="44444444-4444-4444-4444-444444444444",
            title="GraphRAG Architecture Notes",
            topic="graph-rag",
            content=(
                "GraphRAG extracts Entities and Relationships from chunks. "
                "GraphRAG connects Query Rewrite, Entity Retrieval, and relationship-aware citations. "
                * 10
            ),
        )
    )

    return await rag_service.query(
        RagQueryRequest(
            question="How does GraphRAG use Entities and Relationships?",
            top_k=2,
            strategy_name="graph-rag",
            context=RagRequestContext(knowledge_base_id="kb-test-graph"),
        )
    )


async def _evaluate_grounded_answer():
    rag_service = RagService()
    return await rag_service.evaluate(
        RagEvaluateRequest(
            question="What does Advanced RAG use?",
            generated_answer="Advanced RAG uses query rewrite and rerank.",
            expected_answer="Advanced RAG uses query rewrite and rerank.",
            citations=[
                SourceMetadata(
                    document_id="22222222-2222-2222-2222-222222222222",
                    chunk_id="chunk-1",
                    title="Advanced RAG Notes",
                    score=0.9,
                    metadata={"content_preview": "Advanced RAG uses query rewrite and rerank."},
                )
            ],
            strategy_name="advanced-rag",
            context=RagRequestContext(knowledge_base_id="kb-test-advanced"),
        )
    )


async def _evaluate_mismatched_answer():
    rag_service = RagService()
    return await rag_service.evaluate(
        RagEvaluateRequest(
            question="What does Advanced RAG use?",
            generated_answer="Basic CRUD manages create read update delete screens.",
            expected_answer="Advanced RAG uses query rewrite and rerank.",
            citations=[
                SourceMetadata(
                    document_id="22222222-2222-2222-2222-222222222222",
                    chunk_id="chunk-1",
                    title="Advanced RAG Notes",
                    score=0.9,
                    metadata={"content_preview": "Advanced RAG uses query rewrite and rerank."},
                )
            ],
            strategy_name="advanced-rag",
            context=RagRequestContext(knowledge_base_id="kb-test-advanced"),
        )
    )


async def _evaluate_structured_case():
    rag_service = RagService()
    return await rag_service.evaluate(
        RagEvaluateRequest(
            question="What does Advanced RAG use?",
            generated_answer="Advanced RAG uses query rewrite and rerank.",
            expected_answer="Advanced RAG uses query rewrite and rerank.",
            citations=[
                SourceMetadata(
                    document_id="22222222-2222-2222-2222-222222222222",
                    chunk_id="advanced-rerank",
                    title="Advanced RAG Notes",
                    score=0.9,
                    metadata={"content_preview": "Advanced RAG uses query rewrite and rerank."},
                ),
                SourceMetadata(
                    document_id="33333333-3333-3333-3333-333333333333",
                    chunk_id="crud-note",
                    title="CRUD Notes",
                    score=0.4,
                    metadata={"content_preview": "CRUD manages screens."},
                ),
            ],
            strategy_name="advanced-rag",
            context=RagRequestContext(knowledge_base_id="kb-test-advanced"),
            evaluation_case=RagEvaluationCase(
                case_id="advanced-rag-rerank",
                relevant_chunk_ids=["advanced-rerank"],
                expected_citation_chunk_ids=["advanced-rerank"],
                top_k=1,
            ),
        )
    )


async def _evaluate_graph_metadata_answer():
    rag_service = RagService()
    return await rag_service.evaluate(
        RagEvaluateRequest(
            question="How does GraphRAG connect entities and relationships?",
            generated_answer="GraphRAG connects entities with relationship-aware citations.",
            expected_answer="GraphRAG connects entities with relationship-aware citations.",
            citations=[
                SourceMetadata(
                    document_id="graph-doc",
                    chunk_id="graph-citation-context",
                    title="GraphRAG Citation Context",
                    score=0.9,
                    metadata={
                        "content_preview": "GraphRAG uses entities, relationships, and expansion terms for relationship-aware citations.",
                        "graph_entities": ["GraphRAG", "Entities", "Relationships"],
                        "graph_matched_entities": ["GraphRAG", "Entities"],
                        "persisted_graph_matched_entities": ["Relationships"],
                        "graph_relationship_count": 2,
                        "persisted_graph_relationship_count": 2,
                        "graph_expansion_terms": ["relationship-aware", "citations"],
                        "graph_traversal_relationships": [
                            {"source": "GraphRAG", "target": "Relationships", "relation_type": "connects"}
                        ],
                    },
                )
            ],
            strategy_name="graph-rag",
            context=RagRequestContext(knowledge_base_id="kb-test-graph"),
        )
    )


def _document(
    *,
    knowledge_base_id: str,
    document_id: str,
    title: str,
    topic: str,
    content: str,
) -> DocumentIngestRequest:
    return DocumentIngestRequest(
        knowledge_base_id=knowledge_base_id,
        document_id=document_id,
        title=title,
        document_type=DocumentType.TECH_NOTE,
        metadata={"topic": topic},
        file=DocumentPayload(
            filename=f"{title.lower().replace(' ', '-')}.md",
            file_type=FileType.MARKDOWN,
            content=content,
        ),
    )


def _clear_in_memory_repository() -> None:
    if hasattr(repository, "documents"):
        repository.documents.clear()
    if hasattr(repository, "chunks"):
        repository.chunks.clear()
    if hasattr(repository, "graph_entities"):
        repository.graph_entities.clear()
    if hasattr(repository, "graph_relationships"):
        repository.graph_relationships.clear()
