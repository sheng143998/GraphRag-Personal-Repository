import asyncio
import os

os.environ["AI_RAG_USE_DATABASE"] = "false"
os.environ["MODEL_PROVIDER"] = "stub"
os.environ["LLM_PROVIDER"] = "stub"
os.environ["EMBEDDING_PROVIDER"] = "stub"
os.environ["RERANK_PROVIDER"] = "stub"

from app.core.constants import DocumentType, FileType
from app.db.repositories import repository
from app.schemas.common import SourceMetadata
from app.schemas.ingest import DocumentIngestRequest, DocumentPayload
from app.schemas.rag import RagEvaluateRequest, RagQueryRequest, RagRequestContext
from app.services.ingest_service import IngestService
from app.services.rag_service import RagService


def test_advanced_rag_applies_rewrite_filters_fusion_parent_context_and_rerank() -> None:
    response = asyncio.run(_advanced_query())

    assert response.citations
    assert all(source.metadata["topic"] == "advanced-rag" for source in response.citations)
    assert response.trace.attributes["rewritten_query"] != response.question
    assert "retrieval augmented generation" in str(response.trace.attributes["rewritten_query"])

    step_statuses = {step.name: step.status for step in response.trace.steps}
    assert step_statuses["query_rewrite"] == "completed"
    assert step_statuses["multi_query_expand"] == "completed"
    assert step_statuses["fusion"] == "completed"
    assert step_statuses["parent_child_context"] == "completed"
    assert step_statuses["rerank"] == "completed"

    top_source = response.citations[0]
    assert top_source.rerank_score is not None
    assert top_source.metadata["parent_child_mode"] == "neighbor-window"
    assert len(top_source.metadata["context_source_chunk_ids"]) >= 2
    assert top_source.metadata["matched_queries"]
    assert "Advanced RAG" in top_source.metadata["content_preview"]


def test_rag_evaluation_scores_grounded_citations() -> None:
    response = asyncio.run(_evaluate_grounded_answer())

    assert response.result.grounded_score == 1.0
    assert response.result.retrieval_score > 0.0
    assert response.trace.status == "completed"


def test_graph_rag_extracts_entities_and_augments_retrieval_trace() -> None:
    response = asyncio.run(_graph_rag_query())

    assert response.citations
    assert response.trace.attributes["graph_entities"]
    assert response.trace.attributes["graph_relationships"]
    assert "GraphRAG" in response.trace.attributes["graph_augmented_query"]
    step_statuses = {step.name: step.status for step in response.trace.steps}
    assert step_statuses["graph_extract"] == "completed"
    assert response.citations[0].metadata["graph_entities"]
    assert response.citations[0].metadata["graph_relationship_count"] > 0


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
