import base64
import asyncio
import io
import os
import zipfile

os.environ["AI_RAG_USE_DATABASE"] = "false"
os.environ["MODEL_PROVIDER"] = "stub"
os.environ["LLM_PROVIDER"] = "stub"
os.environ["EMBEDDING_PROVIDER"] = "stub"
os.environ["RERANK_PROVIDER"] = "stub"

from app.core.constants import DocumentType, FileType
from app.db.repositories import repository
from app.rag.chunkers.base import CodeAwareChunker, ParentChildChunker, QAPairChunker, SimpleChunker, SimpleWindowChunker
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


def test_ingest_service_routes_interview_experience_to_qna_pair_chunks() -> None:
    _clear_in_memory_repository()

    response = asyncio.run(_ingest_interview_qa_document())
    stored_chunks = repository.get_chunks("doc-interview-qa")

    assert response.chunk_count == len(stored_chunks)
    assert len(stored_chunks) == 2
    assert all(chunk.parent_chunk_id is None for chunk in stored_chunks)
    assert {chunk.metadata.get("chunk_strategy") for chunk in stored_chunks} == {"qna-pair"}
    assert stored_chunks[0].metadata["block_type"] == "qa_pair"
    assert stored_chunks[0].metadata["question_text"] == "How does RAG rerank improve retrieval?"
    assert "It scores candidate chunks" in stored_chunks[0].metadata["answer_text"]


def test_ingest_service_routes_code_snippet_to_code_aware_chunks() -> None:
    _clear_in_memory_repository()

    response = asyncio.run(_ingest_code_snippet_document())
    stored_chunks = repository.get_chunks("doc-code-aware")

    assert response.chunk_count == len(stored_chunks)
    assert stored_chunks
    assert all(chunk.parent_chunk_id is None for chunk in stored_chunks)
    assert {chunk.metadata.get("chunk_strategy") for chunk in stored_chunks} == {"code-aware"}
    assert {chunk.metadata.get("block_type") for chunk in stored_chunks} == {"code"}
    assert "build_query" in {chunk.metadata.get("symbol_name") for chunk in stored_chunks}
    assert any("def build_query" in chunk.content for chunk in stored_chunks)


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


def test_ingest_service_parses_xlsx_table_without_binary_garble() -> None:
    _clear_in_memory_repository()

    response = asyncio.run(_ingest_xlsx_document())
    stored_chunks = repository.get_chunks("doc-xlsx-table")
    combined_context = "\n".join(chunk.content for chunk in stored_chunks)

    assert response.chunk_count == len(stored_chunks)
    assert stored_chunks
    assert {chunk.metadata.get("chunk_strategy") for chunk in stored_chunks} == {"table-row-group"}
    assert stored_chunks[0].metadata["sheet_name"] == "指标表"
    assert stored_chunks[0].metadata["column_names"] == ["指标", "含义"]
    assert stored_chunks[0].metadata["row_range"] == "2-3"
    assert "Sheet: 指标表" in combined_context
    assert "Columns: 指标 | 含义" in combined_context
    assert "Row 2: 指标=召回率 | 含义=命中预期证据" in combined_context
    assert "\ufffd" not in combined_context
    assert "xl/worksheets" not in combined_context
    assert "PK" not in combined_context


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


def test_qna_pair_chunker_emits_one_chunk_per_question_answer_pair() -> None:
    chunks = asyncio.run(_qa_pair_chunks())

    assert len(chunks) == 2
    assert all(chunk.metadata["chunk_strategy"] == "qna-pair" for chunk in chunks)
    assert chunks[0].metadata["split_level"] == "qa-pair"
    assert chunks[0].metadata["question_text"] == "How does hybrid search help RAG?"
    assert chunks[0].metadata["qa_question_type"] == "concept"
    assert chunks[1].metadata["question_text"] == "Compare vector search and keyword search."
    assert chunks[1].metadata["qa_question_type"] == "comparison"


def test_code_aware_chunker_splits_raw_code_by_symbols() -> None:
    chunks = asyncio.run(_code_aware_chunks())

    assert len(chunks) == 2
    assert all(chunk.metadata["chunk_strategy"] == "code-aware" for chunk in chunks)
    assert [chunk.metadata["symbol_name"] for chunk in chunks] == ["build_query", "RagPipeline"]
    assert chunks[0].metadata["symbol_type"] == "function"
    assert chunks[1].metadata["symbol_type"] == "class"
    assert chunks[0].metadata["start_line"] == 1


def test_markdown_block_aware_chunking_keeps_code_and_image_blocks_atomic() -> None:
    chunks = asyncio.run(_markdown_block_chunks())

    code_chunks = [chunk for chunk in chunks if chunk.metadata["block_type"] == "code"]
    image_chunks = [chunk for chunk in chunks if chunk.metadata["block_type"] == "image_caption"]

    assert len(code_chunks) == 1
    assert "def build_query" in code_chunks[0].content
    assert "return query + ' graph rag expansion'" in code_chunks[0].content
    assert code_chunks[0].metadata["split_level"] == "code-block"
    assert len(image_chunks) == 1
    assert image_chunks[0].content.strip() == "![RAG flow](./images/rag-flow.png)"
    assert image_chunks[0].metadata["split_level"] == "image-reference"
    assert image_chunks[0].metadata["quality_score"] < 0.5


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


def test_parent_child_chunker_downgrades_single_identical_child_segment() -> None:
    chunks = asyncio.run(_single_child_parent_child_chunks())

    assert len(chunks) == 1
    assert chunks[0].parent_chunk_id is None
    assert chunks[0].metadata["chunk_strategy"] == "recursive-overlap"
    assert chunks[0].metadata["chunk_algorithm"] == "parent-child-single-child-downgrade"
    assert chunks[0].metadata["parent_child_downgrade_reason"] == "single-child-identical-parent"
    assert not any(chunk.metadata.get("chunk_level") == "parent" for chunk in chunks)


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


async def _single_child_parent_child_chunks():
    return await ParentChildChunker().chunk(
        parsed_document=ParsedDocument(
            document_id="doc-single-child-parent",
            title="Short Explicit Parent Child",
            normalized_text=(
                "# Short Chapter\n\n"
                "This section is long enough to be a parent segment but too short to split into multiple child chunks. "
                "It used to create one parent and one child with identical content."
            ),
            parser_name="test-parser",
            parser_version="v1",
            metadata={},
        ),
        request=_request(
            document_id="doc-single-child-parent",
            metadata={
                "chunk_strategy": "parent-child",
                "parent_chunk_size": 900,
                "child_chunk_size": 500,
                "child_chunk_overlap": 80,
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


async def _qa_pair_chunks():
    return await QAPairChunker().chunk(
        parsed_document=ParsedDocument(
            document_id="doc-qa",
            title="Interview Notes",
            normalized_text=(
                "Q: How does hybrid search help RAG?\n"
                "A: It combines semantic recall with keyword precision.\n\n"
                "Question: Compare vector search and keyword search.\n"
                "Answer: Vector search catches meaning, while keyword search catches exact terms."
            ),
            parser_name="test-parser",
            parser_version="v1",
            metadata={},
        ),
        request=_request(
            document_id="doc-qa",
            document_type=DocumentType.INTERVIEW_EXPERIENCE,
            metadata={},
        ),
    )


async def _code_aware_chunks():
    return await CodeAwareChunker().chunk(
        parsed_document=ParsedDocument(
            document_id="doc-code",
            title="Code Notes",
            normalized_text=(
                "def build_query(query: str) -> str:\n"
                "    return query.strip().lower()\n\n"
                "class RagPipeline:\n"
                "    def run(self, question: str) -> str:\n"
                "        return build_query(question)\n"
            ),
            parser_name="test-parser",
            parser_version="v1",
            metadata={"language": "python"},
        ),
        request=_request(
            document_id="doc-code",
            document_type=DocumentType.CODE_SNIPPET,
            filename="pipeline.py",
            metadata={},
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


async def _markdown_block_chunks():
    return await SimpleChunker().chunk(
        parsed_document=ParsedDocument(
            document_id="doc-markdown-blocks",
            title="Markdown Block Notes",
            normalized_text=(
                "# Markdown Blocks\n\n"
                "Intro text explains why code and images should be treated as separate blocks.\n\n"
                "```python\n"
                "def build_query(query: str) -> str:\n"
                "    normalized = query.strip().lower()\n"
                "    if not normalized:\n"
                "        return 'empty query'\n"
                "    return query + ' graph rag expansion'\n"
                "```\n\n"
                "![RAG flow](./images/rag-flow.png)\n\n"
                "Closing text should remain a normal paragraph chunk."
            ),
            parser_name="test-parser",
            parser_version="v1",
            metadata={},
        ),
        request=_request(
            document_id="doc-markdown-blocks",
            metadata={
                "chunk_size": 200,
                "chunk_overlap": 40,
                "min_chunk_size": 80,
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
                "Child chunks should remain small enough for precise embedding retrieval. " * 5
                + "\n\n"
                "# Agent Chapter\n\n"
                "Agent orchestration notes should keep node, state, and tool context together. "
                "The graph starts with classify_question, then selects retrieval tools, then records trace fields. "
                "Reducers merge retrieved evidence, rerank scores, generated answer drafts, and citation metadata. "
                "Tool nodes should keep retry state, timeout state, and fallback reason close to the execution step. "
                "Parent chunks are answer context and child chunks are embedding units for precise retrieval."
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
            document_id="doc-code-aware",
            document_type=DocumentType.CODE_SNIPPET,
            filename="query_builder.py",
            content=(
                "def build_query(query: str) -> str:\n"
                "    normalized = query.strip().lower()\n"
                "    return normalized\n\n"
                "class QueryBuilder:\n"
                "    def build(self, query: str) -> str:\n"
                "        return build_query(query)\n"
            ),
            metadata={
                "language": "python",
            },
        )
    )


async def _ingest_interview_qa_document():
    return await IngestService().ingest_document(
        _request(
            document_id="doc-interview-qa",
            document_type=DocumentType.INTERVIEW_EXPERIENCE,
            content=(
                "Q: How does RAG rerank improve retrieval?\n"
                "A: It scores candidate chunks after initial recall and moves better evidence upward.\n\n"
                "Question: Compare parent-child and recursive overlap chunking.\n"
                "Answer: Parent-child retrieves smaller child chunks but answers with parent context."
            ),
            metadata={},
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


async def _ingest_xlsx_document():
    return await IngestService().ingest_document(
        _request(
            document_id="doc-xlsx-table",
            document_type=DocumentType.TECH_NOTE,
            file_type=FileType.XLSX,
            filename="rag-metrics.xlsx",
            content_base64=_xlsx_base64(),
            metadata={
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
    content_base64: str | None = None,
) -> DocumentIngestRequest:
    content_value = content if content is not None else None if content_base64 else ("Parent child retrieval improves Advanced RAG context. " * 40)
    return DocumentIngestRequest(
        knowledge_base_id="kb-parent-child",
        document_id=document_id,
        title="Parent Child Notes",
        document_type=document_type,
        metadata=metadata,
        file=DocumentPayload(
            filename=filename,
            file_type=file_type,
            content=content_value,
            content_base64=content_base64,
        ),
    )


def _xlsx_base64() -> str:
    shared_strings = ["指标", "含义", "召回率", "命中预期证据", "精确率", "避免无关片段"]
    rows = [
        [0, 1],
        [2, 3],
        [4, 5],
    ]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr(
            "xl/workbook.xml",
            (
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets><sheet name="指标表" sheetId="1" r:id="rId1"/></sheets>'
                "</workbook>"
            ),
        )
        zf.writestr(
            "xl/_rels/workbook.xml.rels",
            (
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                'Target="worksheets/sheet1.xml"/>'
                "</Relationships>"
            ),
        )
        zf.writestr(
            "xl/sharedStrings.xml",
            (
                '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                + "".join(f"<si><t>{value}</t></si>" for value in shared_strings)
                + "</sst>"
            ),
        )
        zf.writestr(
            "xl/worksheets/sheet1.xml",
            (
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                + "".join(
                    f'<row r="{row_index}">'
                    + "".join(
                        f'<c r="{column}{row_index}" t="s"><v>{shared_string_index}</v></c>'
                        for column, shared_string_index in zip(["A", "B"], row, strict=False)
                    )
                    + "</row>"
                    for row_index, row in enumerate(rows, start=1)
                )
                + "</sheetData></worksheet>"
            ),
        )
    return base64.b64encode(buffer.getvalue()).decode("ascii")


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
