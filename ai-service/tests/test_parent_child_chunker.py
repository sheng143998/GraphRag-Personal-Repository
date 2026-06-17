import asyncio
import os

os.environ["AI_RAG_USE_DATABASE"] = "false"
os.environ["MODEL_PROVIDER"] = "stub"
os.environ["LLM_PROVIDER"] = "stub"
os.environ["EMBEDDING_PROVIDER"] = "stub"
os.environ["RERANK_PROVIDER"] = "stub"

from app.core.constants import DocumentType, FileType
from app.db.repositories import repository
from app.rag.chunkers.base import ParentChildChunker, SimpleChunker, SimpleWindowChunker
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
    assert parent_chunks[0].metadata["chunk_algorithm"] == "section-parent-recursive-child"
    assert parent_chunks[0].metadata["embedding_text_mode"] == "heading-aware"
    assert "char_start" in parent_chunks[0].metadata
    assert "char_end" in child_chunks[0].metadata


def test_ingest_service_uses_parent_child_chunker_when_requested() -> None:
    _clear_in_memory_repository()

    response = asyncio.run(_ingest_parent_child_document())
    stored_chunks = repository.get_chunks("doc-parent-child-ingest")

    assert response.chunk_count == len(stored_chunks)
    assert any(chunk.parent_chunk_id for chunk in stored_chunks)
    assert any(chunk.metadata.get("chunk_level") == "parent" for chunk in stored_chunks)
    assert any(chunk.metadata.get("chunk_level") == "child" for chunk in stored_chunks)


def test_ingest_service_routes_tech_note_markdown_to_parent_child_chunking() -> None:
    _clear_in_memory_repository()

    response = asyncio.run(_ingest_default_document())
    stored_chunks = repository.get_chunks("doc-default-parent-child")

    assert response.chunk_count == len(stored_chunks)
    assert any(chunk.metadata.get("chunk_level") == "parent" for chunk in stored_chunks)
    assert any(chunk.parent_chunk_id for chunk in stored_chunks if chunk.metadata.get("chunk_level") == "child")
    assert {chunk.metadata.get("chunk_strategy") for chunk in stored_chunks} == {"parent-child"}


def test_ingest_service_downgrades_short_auto_parent_child_document_to_recursive_overlap() -> None:
    _clear_in_memory_repository()

    response = asyncio.run(_ingest_short_default_document())
    stored_chunks = repository.get_chunks("doc-short-recursive")

    assert response.chunk_count == len(stored_chunks)
    assert stored_chunks
    assert all(chunk.parent_chunk_id is None for chunk in stored_chunks)
    assert {chunk.metadata.get("chunk_strategy") for chunk in stored_chunks} == {"recursive-overlap"}


def test_ingest_service_routes_code_snippet_to_recursive_overlap() -> None:
    _clear_in_memory_repository()

    response = asyncio.run(_ingest_code_snippet_document())
    stored_chunks = repository.get_chunks("doc-code-recursive")

    assert response.chunk_count == len(stored_chunks)
    assert stored_chunks
    assert all(chunk.parent_chunk_id is None for chunk in stored_chunks)
    assert {chunk.metadata.get("chunk_strategy") for chunk in stored_chunks} == {"recursive-overlap"}


def test_ingest_service_routes_table_files_to_row_group_chunks() -> None:
    _clear_in_memory_repository()

    response = asyncio.run(_ingest_csv_document())
    stored_chunks = repository.get_chunks("doc-csv-table")

    assert response.chunk_count == len(stored_chunks)
    assert stored_chunks
    assert all(chunk.parent_chunk_id is None for chunk in stored_chunks)
    assert {chunk.metadata.get("chunk_strategy") for chunk in stored_chunks} == {"table-row-group"}
    assert {chunk.metadata.get("block_type") for chunk in stored_chunks} == {"table_rows"}
    assert stored_chunks[0].metadata["column_names"] == ["metric", "meaning"]
    assert stored_chunks[0].metadata["sheet_name"] == "RAG Metrics"
    assert stored_chunks[0].metadata["row_range"] == "2-3"
    assert "Row 2: metric=recall" in stored_chunks[0].content


def test_ingest_service_allows_explicit_chunk_strategy_override() -> None:
    _clear_in_memory_repository()

    response = asyncio.run(_ingest_code_snippet_parent_child_override())
    stored_chunks = repository.get_chunks("doc-code-parent-override")

    assert response.chunk_count == len(stored_chunks)
    assert any(chunk.metadata.get("chunk_level") == "parent" for chunk in stored_chunks)
    assert any(chunk.parent_chunk_id for chunk in stored_chunks if chunk.metadata.get("chunk_level") == "child")
    assert {chunk.metadata.get("chunk_strategy") for chunk in stored_chunks} == {"parent-child"}


def test_parent_child_ingest_query_hydrates_real_parent_context() -> None:
    _clear_in_memory_repository()

    response = asyncio.run(_ingest_then_parent_child_query())

    assert response.citations
    top_source = response.citations[0]
    assert top_source.metadata["parent_child_mode"] == "parent-child"
    assert top_source.metadata["parent_chunk_id"]
    assert "Parent child retrieval improves Advanced RAG context" in top_source.metadata["content_preview"]


def test_simple_chunker_defaults_to_recursive_overlap_with_section_metadata() -> None:
    chunks = asyncio.run(_simple_chunks())

    assert chunks
    assert all(chunk.parent_chunk_id is None for chunk in chunks)
    assert all(chunk.metadata["chunk_strategy"] == "recursive-overlap" for chunk in chunks)
    assert chunks[0].metadata["chunk_algorithm"] == "recursive-overlap"
    assert chunks[0].metadata["chunk_overlap"] == 60
    assert chunks[0].metadata["heading_path"] == ["Spring Notes"]
    assert chunks[0].metadata["section_title"] == "Spring Notes"
    assert "Heading path: Spring Notes" in chunks[0].metadata["embedding_text"]
    assert "char_start" in chunks[0].metadata
    assert "char_end" in chunks[0].metadata


def test_chunker_marks_prompt_examples_and_image_captions_as_lower_quality() -> None:
    prompt_chunks = asyncio.run(_prompt_example_chunks())
    image_chunks = asyncio.run(_image_caption_chunks())

    assert prompt_chunks[0].metadata["block_type"] == "prompt_example"
    assert prompt_chunks[0].metadata["quality_score"] < 1.0
    assert "prompt_example" in prompt_chunks[0].metadata["low_quality_reasons"]
    assert image_chunks[0].metadata["block_type"] == "image_caption"
    assert image_chunks[0].metadata["quality_score"] < 0.5
    assert "image_or_attachment_reference" in image_chunks[0].metadata["low_quality_reasons"]


def test_simple_window_chunker_remains_available_for_explicit_compatibility() -> None:
    chunks = asyncio.run(_simple_window_chunks())

    assert chunks
    assert all(chunk.parent_chunk_id is None for chunk in chunks)
    assert all(chunk.metadata["chunk_strategy"] == "simple-window" for chunk in chunks)
    assert chunks[0].metadata["chunk_algorithm"] == "fixed-character-window"


def test_parent_child_chunker_uses_heading_sections_as_parent_chunks() -> None:
    chunks = asyncio.run(_section_parent_child_chunks())

    parent_chunks = [chunk for chunk in chunks if chunk.metadata["chunk_level"] == "parent"]
    child_chunks = [chunk for chunk in chunks if chunk.metadata["chunk_level"] == "child"]

    assert [chunk.metadata["section_title"] for chunk in parent_chunks] == ["RAG Chapter", "Agent Chapter"]
    assert all(chunk.metadata["parent_heading"] in {"RAG Chapter", "Agent Chapter"} for chunk in child_chunks)
    assert all(chunk.metadata["chunk_overlap"] == 40 for chunk in child_chunks)
    assert all("child_index_in_parent" in chunk.metadata for chunk in child_chunks)


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
            normalized_text=(
                "# Spring Notes\n\n"
                "Simple flat chunking is now recursive and heading-aware. " * 8
            ),
            parser_name="test-parser",
            parser_version="v1",
            metadata={},
        ),
        request=_request(
            document_id="doc-simple",
            metadata={
                "chunk_size": 220,
                "chunk_overlap": 60,
            },
        ),
    )


async def _simple_window_chunks():
    return await SimpleWindowChunker().chunk(
        parsed_document=ParsedDocument(
            document_id="doc-simple-window",
            title="Simple Window Notes",
            normalized_text=("Simple flat chunking remains available for compatibility. " * 10),
            parser_name="test-parser",
            parser_version="v1",
            metadata={},
        ),
        request=_request(
            document_id="doc-simple-window",
            metadata={
                "chunk_strategy": "simple-window",
                "chunk_size": 180,
            },
        ),
    )


async def _section_parent_child_chunks():
    return await ParentChildChunker().chunk(
        parsed_document=ParsedDocument(
            document_id="doc-section-parent-child",
            title="Section Notes",
            normalized_text=(
                "# RAG Chapter\n\n"
                "RAG notes should keep a complete chapter as parent context. "
                "Child chunks should remain small enough for precise embedding retrieval.\n\n"
                "# Agent Chapter\n\n"
                "Agent orchestration notes should keep node, state, and tool context together. "
                "Parent chunks are answer context and child chunks are embedding units."
            ),
            parser_name="test-parser",
            parser_version="v1",
            metadata={"topic": "chunking"},
        ),
        request=_request(
            document_id="doc-section-parent-child",
            metadata={
                "chunk_strategy": "parent-child",
                "parent_chunk_size": 900,
                "child_chunk_size": 120,
                "child_chunk_overlap": 40,
            },
        ),
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


async def _ingest_default_document():
    return await IngestService().ingest_document(
        _request(
            document_id="doc-default-parent-child",
            metadata={
                "parent_chunk_size": 900,
                "child_chunk_size": 300,
            },
        )
    )


async def _ingest_short_default_document():
    return await IngestService().ingest_document(
        _request(
            document_id="doc-short-recursive",
            content=(
                "# RAG Fusion\n\n"
                "RAG Fusion uses multiple retrieval queries and fuses ranked evidence.\n\n"
                "This short note should stay as recursive-overlap chunks instead of emitting identical parent and child chunks."
            ),
            metadata={
                "parent_chunk_size": 900,
                "child_chunk_size": 300,
            },
        )
    )


async def _ingest_code_snippet_document():
    return await IngestService().ingest_document(
        _request(
            document_id="doc-code-recursive",
            document_type=DocumentType.CODE_SNIPPET,
            metadata={
                "chunk_size": 220,
                "chunk_overlap": 60,
            },
        )
    )


async def _ingest_csv_document():
    return await IngestService().ingest_document(
        _request(
            document_id="doc-csv-table",
            document_type=DocumentType.TECH_NOTE,
            file_type=FileType.CSV,
            filename="rag-metrics.csv",
            content="metric,meaning\nrecall,hit expected evidence\nprecision,avoid irrelevant chunks\n",
            metadata={
                "sheet_name": "RAG Metrics",
                "table_row_group_size": 2,
            },
        )
    )


async def _ingest_code_snippet_parent_child_override():
    return await IngestService().ingest_document(
        _request(
            document_id="doc-code-parent-override",
            document_type=DocumentType.CODE_SNIPPET,
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


def _request(
    document_id: str,
    metadata: dict[str, object],
    *,
    document_type: DocumentType = DocumentType.TECH_NOTE,
    file_type: FileType = FileType.MARKDOWN,
    filename: str = "parent-child.md",
    content: str | None = None,
) -> DocumentIngestRequest:
    return DocumentIngestRequest(
        knowledge_base_id="kb-parent-child",
        document_id=document_id,
        title="Parent Child Notes",
        document_type=document_type,
        metadata=metadata,
        file=DocumentPayload(
            filename=filename,
            file_type=file_type,
            content=content or ("Parent child retrieval improves Advanced RAG context. " * 40),
        ),
    )


async def _prompt_example_chunks():
    return await SimpleChunker().chunk(
        parsed_document=ParsedDocument(
            document_id="doc-prompt",
            title="extract_graph prompt examples",
            normalized_text=(
                "# Extract Graph\n\n"
                "-Goal- Given a text document, identify entities and relationships.\n\n"
                "-Steps-\n"
                "1. Identify all entities.\n"
                "2. Identify all relationships.\n\n"
                "Example Input: Text with entities.\n"
                "Output: JSON records."
            ),
            parser_name="test-parser",
            parser_version="v1",
            metadata={},
        ),
        request=_request(
            document_id="doc-prompt",
            metadata={"chunk_strategy": "recursive-overlap"},
        ),
    )


async def _image_caption_chunks():
    return await SimpleChunker().chunk(
        parsed_document=ParsedDocument(
            document_id="doc-image",
            title="Image Notes",
            normalized_text="![[parent-child-diagram.png]]",
            parser_name="test-parser",
            parser_version="v1",
            metadata={},
        ),
        request=_request(
            document_id="doc-image",
            metadata={"chunk_strategy": "recursive-overlap"},
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
