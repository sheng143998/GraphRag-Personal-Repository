import asyncio
import os

os.environ["AI_RAG_USE_DATABASE"] = "false"
os.environ["MODEL_PROVIDER"] = "stub"
os.environ["LLM_PROVIDER"] = "stub"
os.environ["EMBEDDING_PROVIDER"] = "stub"
os.environ["RERANK_PROVIDER"] = "stub"

from app.core.constants import DocumentType, FileType
from app.db.repositories import repository
from app.rag.chunkers.base import ParentChildChunker, SimpleChunker
from app.schemas.ingest import DocumentIngestRequest, DocumentPayload, ParsedDocument
from app.schemas.rag import RagQueryRequest, RagRequestContext
from app.services.ingest_service import IngestService
from app.services.rag_service import RagService


def test_parent_child_chunker_emits_parent_and_child_chunks() -> None:
    chunks = asyncio.run(_parent_child_chunks())

    parent_chunks = [chunk for chunk in chunks if chunk.metadata["chunk_level"] == "parent"]
    child_chunks = [chunk for chunk in chunks if chunk.metadata["chunk_level"] == "child"]

    assert parent_chunks
    assert child_chunks
    assert all(child.parent_chunk_id for child in child_chunks)
    assert child_chunks[0].parent_chunk_id == parent_chunks[0].chunk_id
    assert parent_chunks[0].metadata["child_chunk_ids"]
    assert parent_chunks[0].metadata["chunk_strategy"] == "parent-child"


def test_ingest_service_uses_parent_child_chunker_when_requested() -> None:
    _clear_in_memory_repository()

    response = asyncio.run(_ingest_parent_child_document())
    stored_chunks = repository.get_chunks("doc-parent-child-ingest")

    assert response.chunk_count == len(stored_chunks)
    assert any(chunk.parent_chunk_id for chunk in stored_chunks)
    assert any(chunk.metadata.get("chunk_level") == "parent" for chunk in stored_chunks)
    assert any(chunk.metadata.get("chunk_level") == "child" for chunk in stored_chunks)


def test_parent_child_ingest_query_hydrates_real_parent_context() -> None:
    _clear_in_memory_repository()

    response = asyncio.run(_ingest_then_parent_child_query())

    assert response.citations
    top_source = response.citations[0]
    assert top_source.metadata["parent_child_mode"] == "parent-child"
    assert top_source.metadata["parent_chunk_id"]
    assert "Parent child retrieval improves Advanced RAG context" in top_source.metadata["content_preview"]


def test_simple_chunker_remains_default_flat_chunker() -> None:
    chunks = asyncio.run(_simple_chunks())

    assert chunks
    assert all(chunk.parent_chunk_id is None for chunk in chunks)
    assert all(chunk.metadata["chunk_strategy"] == "simple-window" for chunk in chunks)


async def _parent_child_chunks():
    return await ParentChildChunker().chunk(
        parsed_document=ParsedDocument(
            document_id="doc-parent-child",
            title="Parent Child Notes",
            normalized_text=("Parent child retrieval improves Advanced RAG context. " * 40),
            parser_name="test-parser",
            parser_version="v1",
            metadata={"topic": "advanced-rag"},
        ),
        request=_request(
            document_id="doc-parent-child",
            metadata={
                "chunk_strategy": "parent-child",
                "parent_chunk_size": 900,
                "child_chunk_size": 300,
            },
        ),
    )


async def _simple_chunks():
    return await SimpleChunker().chunk(
        parsed_document=ParsedDocument(
            document_id="doc-simple",
            title="Simple Notes",
            normalized_text=("Simple flat chunking remains the default. " * 20),
            parser_name="test-parser",
            parser_version="v1",
            metadata={},
        ),
        request=_request(document_id="doc-simple", metadata={}),
    )


async def _ingest_parent_child_document():
    return await IngestService().ingest_document(
        _request(
            document_id="doc-parent-child-ingest",
            metadata={
                "chunk_strategy": "parent-child",
                "parent_chunk_size": 900,
                "child_chunk_size": 300,
            },
        )
    )


async def _ingest_then_parent_child_query():
    await _ingest_parent_child_document()
    return await RagService().query(
        RagQueryRequest(
            question="How does parent child retrieval improve Advanced RAG context?",
            top_k=2,
            strategy_name="parent-child",
            context=RagRequestContext(knowledge_base_id="kb-parent-child"),
        )
    )


def _request(document_id: str, metadata: dict[str, object]) -> DocumentIngestRequest:
    return DocumentIngestRequest(
        knowledge_base_id="kb-parent-child",
        document_id=document_id,
        title="Parent Child Notes",
        document_type=DocumentType.TECH_NOTE,
        metadata=metadata,
        file=DocumentPayload(
            filename="parent-child.md",
            file_type=FileType.MARKDOWN,
            content=("Parent child retrieval improves Advanced RAG context. " * 40),
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
