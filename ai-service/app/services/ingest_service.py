from __future__ import annotations

from uuid import uuid4

from app.core.config import settings
from app.core.constants import DocumentType, FileType
from app.core.pydantic_compat import model_copy_update
from app.core.tracing import TraceBuilder
from app.db.repositories import repository
from app.rag.chunkers.base import (
    CodeAwareChunker,
    ParentChildChunker,
    QAPairChunker,
    SimpleChunker,
    SimpleWindowChunker,
    TableRowGroupChunker,
    _bounded_int,
    _document_sections,
)
from app.rag.graph import RuleBasedGraphExtractor
from app.rag.loaders.base import InlineContentLoader
from app.rag.parsers.registry import ParserRegistry
from app.schemas.ingest import (
    ChunkRecord,
    DocumentIngestRequest,
    DocumentIngestResponse,
    EmbeddingRebuildRequest,
    EmbeddingRebuildResponse,
    ParsedDocument,
)
from app.services.adapters.base import AdapterCallContext
from app.services.adapters.registry import embedding_adapter, get_embedding_model_name


class IngestService:
    def __init__(self) -> None:
        self.loader = InlineContentLoader()
        self.chunker = SimpleChunker()
        self.simple_window_chunker = SimpleWindowChunker()
        self.parent_child_chunker = ParentChildChunker()
        self.table_row_group_chunker = TableRowGroupChunker()
        self.qa_pair_chunker = QAPairChunker()
        self.code_aware_chunker = CodeAwareChunker()
        self.parser_registry = ParserRegistry()
        self.graph_extractor = RuleBasedGraphExtractor()

    async def ingest_document(self, payload: DocumentIngestRequest) -> DocumentIngestResponse:
        trace_builder = TraceBuilder(
            operation="ingest_document",
            strategy_name="document-ingest",
            model_name=get_embedding_model_name(),
        )
        trace_builder.set_attribute("knowledge_base_id", payload.knowledge_base_id)
        trace_builder.set_attribute("document_type", payload.document_type)
        raw_content = await self.loader.load(payload.file)
        trace_builder.add_step(
            name="load_document",
            status="completed",
            detail="Loaded raw document content.",
            payload={"filename": payload.file.filename, "file_type": payload.file.file_type},
        )

        parser = self.parser_registry.get_parser(payload.file.file_type)
        parsed_content = await parser.parse(raw_content=raw_content, request=payload)
        parsed_text = _sanitize_text_for_storage(parsed_content.text)
        if not parsed_text.strip():
            parser_status = parsed_content.metadata.get("status")
            parser_error = (
                parsed_content.metadata.get("error")
                or parsed_content.metadata.get("last_poll_error")
                or parsed_content.metadata.get("reason")
            )
            raise RuntimeError(
                f"parser {parser.name} returned empty content for file_type={payload.file.file_type}, "
                f"status={parser_status}, error={parser_error}"
            )
        parsed_document = ParsedDocument(
            document_id=payload.document_id,
            title=payload.title,
            normalized_text=parsed_text,
            parser_name=parser.name,
            parser_version=parser.version,
            metadata=parsed_content.metadata,
        )
        repository.save_document(
            _parsed_document_for_storage(parsed_document),
            request=payload,
            preserve_summary=True,
        )
        trace_builder.add_step(
            name="parse_document",
            status="completed",
            detail="Parsed and normalized document content.",
            payload={"parser_name": parser.name, "parser_version": parser.version},
        )

        requested_chunk_strategy = _chunk_strategy(payload)
        chunk_strategy, chunk_strategy_downgrade_reason = _resolve_chunk_strategy(
            request=payload,
            parsed_document=parsed_document,
            requested_chunk_strategy=requested_chunk_strategy,
        )
        if chunk_strategy == "parent-child":
            chunker = self.parent_child_chunker
        elif chunk_strategy == "table-row-group":
            chunker = self.table_row_group_chunker
        elif chunk_strategy == "simple-window":
            chunker = self.simple_window_chunker
        elif chunk_strategy == "qna-pair":
            chunker = self.qa_pair_chunker
        elif chunk_strategy == "code-aware":
            chunker = self.code_aware_chunker
        else:
            chunker = self.chunker
        chunks = await chunker.chunk(parsed_document=parsed_document, request=payload)
        if not chunks:
            raise RuntimeError(
                f"chunker produced no chunks for document_id={payload.document_id}, parser={parser.name}"
            )
        repository.save_chunks(payload.document_id, payload.knowledge_base_id, chunks)
        trace_builder.add_step(
            name="chunk_document",
            status="completed",
            detail="Built chunk records for storage.",
            payload={
                "chunk_count": len(chunks),
                "requested_chunk_strategy": requested_chunk_strategy,
                "resolved_chunk_strategy": chunk_strategy,
                "stored_chunk_strategy": chunks[0].metadata.get("chunk_strategy") if chunks else None,
                "chunk_strategy_router": _chunk_strategy_router_name(payload),
                "chunk_strategy_downgrade_reason": chunk_strategy_downgrade_reason,
                "document_type": payload.document_type,
                "file_type": payload.file.file_type,
            },
        )

        graph_entity_count = 0
        graph_relationship_count = 0
        retrievable_chunks = [chunk for chunk in chunks if chunk.metadata.get("chunk_level") != "parent"]
        for chunk in retrievable_chunks:
            entities = self.graph_extractor.extract_entities(chunk.content)
            relationships = self.graph_extractor.extract_relationships(entities)
            graph_entity_count += len(entities)
            graph_relationship_count += len(relationships)
            repository.save_graph_facts(
                knowledge_base_id=payload.knowledge_base_id,
                document_id=payload.document_id,
                chunk_id=chunk.chunk_id,
                entities=entities,
                relationships=relationships,
            )
        trace_builder.add_step(
            name="extract_graph_facts",
            status="completed",
            detail="Extracted graph entities and relationships from chunks.",
            payload={
                "entity_count": graph_entity_count,
                "relationship_count": graph_relationship_count,
            },
        )

        if retrievable_chunks:
            embeddings = await embedding_adapter.embed(
                texts=[_embedding_input(chunk) for chunk in retrievable_chunks],
                context=AdapterCallContext(
                    trace_id=trace_builder.trace.trace_id,
                    run_id=trace_builder.trace.run_id,
                    operation="embed_chunks",
                    model_name=get_embedding_model_name(),
                    strategy_name="document-ingest",
                ),
            )
            repository.save_embeddings(
                chunks=retrievable_chunks,
                embeddings=embeddings,
                embedding_model=get_embedding_model_name(),
            )
        trace_builder.add_step(
            name="embed_chunks",
            status="completed",
            detail="Called embedding adapter for stored chunks.",
            model_name=get_embedding_model_name(),
        )

        trace = trace_builder.finalize(status="completed")
        return DocumentIngestResponse(
            document_id=payload.document_id,
            chunk_count=len(chunks),
            parser_name=parser.name,
            file_type=payload.file.file_type,
            trace=trace,
        )

    async def rebuild_embeddings(
        self,
        payload: EmbeddingRebuildRequest,
    ) -> EmbeddingRebuildResponse:
        trace_builder = TraceBuilder(
            operation="rebuild_embeddings",
            strategy_name="embedding-rebuild",
            model_name=get_embedding_model_name(),
        )
        target_document_ids = payload.document_ids
        rebuilt_documents: list[str] = []
        for document_id in target_document_ids:
            chunks = repository.get_chunks(document_id)
            retrievable_chunks = [chunk for chunk in chunks if chunk.metadata.get("chunk_level") != "parent"]
            if not retrievable_chunks:
                continue
            embeddings = await embedding_adapter.embed(
                texts=[_embedding_input(chunk) for chunk in retrievable_chunks],
                context=AdapterCallContext(
                    trace_id=trace_builder.trace.trace_id,
                    run_id=trace_builder.trace.run_id,
                    operation="embed_chunks",
                    model_name=get_embedding_model_name(),
                    strategy_name="embedding-rebuild",
                ),
            )
            repository.save_embeddings(
                chunks=retrievable_chunks,
                embeddings=embeddings,
                embedding_model=get_embedding_model_name(),
            )
            rebuilt_documents.append(document_id)
        trace_builder.add_step(
            name="rebuild_embeddings",
            status="completed",
            detail="Replayed embeddings for available chunks.",
            model_name=settings.default_embedding_model,
            payload={"document_count": len(rebuilt_documents)},
        )
        trace = trace_builder.finalize(status="completed")
        return EmbeddingRebuildResponse(
            knowledge_base_id=payload.knowledge_base_id,
            rebuilt_documents=rebuilt_documents,
            trace=trace,
        )


def _chunk_strategy(request: DocumentIngestRequest) -> str:
    explicit = request.metadata.get("chunk_strategy") or request.metadata.get("chunkStrategy")
    if explicit:
        return str(explicit).strip().lower()
    return _route_chunk_strategy(
        document_type=str(request.document_type),
        file_type=str(request.file.file_type),
    )


def _resolve_chunk_strategy(
    *,
    request: DocumentIngestRequest,
    parsed_document: ParsedDocument,
    requested_chunk_strategy: str,
) -> tuple[str, str | None]:
    if requested_chunk_strategy != "parent-child" or _has_explicit_chunk_strategy(request):
        return requested_chunk_strategy, None

    downgrade_reason = _parent_child_downgrade_reason(
        request=request,
        parsed_document=parsed_document,
    )
    if downgrade_reason:
        return "recursive-overlap", downgrade_reason
    return requested_chunk_strategy, None


def _has_explicit_chunk_strategy(request: DocumentIngestRequest) -> bool:
    return bool(request.metadata.get("chunk_strategy") or request.metadata.get("chunkStrategy"))


def _parent_child_downgrade_reason(
    *,
    request: DocumentIngestRequest,
    parsed_document: ParsedDocument,
) -> str | None:
    text = parsed_document.normalized_text.strip()
    if not text:
        return "empty-document"

    min_document_chars = _bounded_int(
        request.metadata.get("parent_child_min_document_chars"),
        default=1200,
        minimum=200,
        maximum=20000,
    )
    child_size = _effective_child_chunk_size(request)
    min_section_chars = _bounded_int(
        request.metadata.get("parent_child_min_section_chars"),
        default=child_size + 1,
        minimum=100,
        maximum=10000,
    )

    if len(text) < min_document_chars:
        return f"document-too-short:{len(text)}<{min_document_chars}"

    section_lengths = [
        len(parsed_document.normalized_text[section.start : section.end].strip())
        for section in _document_sections(parsed_document.normalized_text)
    ]
    max_section_chars = max(section_lengths, default=0)
    if max_section_chars < min_section_chars:
        return f"sections-too-short:{max_section_chars}<{min_section_chars}"

    return None


def _effective_child_chunk_size(request: DocumentIngestRequest) -> int:
    parent_size = _bounded_int(request.metadata.get("parent_chunk_size"), default=1500, minimum=500, maximum=5000)
    child_size = _bounded_int(request.metadata.get("child_chunk_size"), default=500, minimum=100, maximum=1500)
    if child_size >= parent_size:
        return max(100, parent_size // 3)
    return child_size


def _chunk_strategy_router_name(request: DocumentIngestRequest) -> str:
    if request.metadata.get("chunk_strategy") or request.metadata.get("chunkStrategy"):
        return "explicit-metadata"
    return "document-file-type"


def _route_chunk_strategy(*, document_type: str, file_type: str) -> str:
    table_like_file_types = {
        FileType.CSV.value,
        FileType.XLS.value,
        FileType.XLSX.value,
    }
    exact_or_short_document_types = {
        DocumentType.JOB_DESCRIPTION.value,
    }
    long_note_document_types = {
        DocumentType.TECH_NOTE.value,
        DocumentType.COURSE_NOTE.value,
        DocumentType.DEVELOPMENT_EXPERIENCE.value,
        DocumentType.PROJECT_EXPERIENCE.value,
    }
    parent_child_file_types = {
        FileType.MARKDOWN.value,
        FileType.TEXT.value,
        FileType.HTML.value,
        FileType.DOCX.value,
        FileType.PDF.value,
    }

    normalized_document_type = document_type.strip().lower()
    normalized_file_type = file_type.strip().lower()

    if normalized_file_type in table_like_file_types:
        return "table-row-group"
    if normalized_document_type == DocumentType.INTERVIEW_EXPERIENCE.value:
        return "qna-pair"
    if normalized_document_type == DocumentType.CODE_SNIPPET.value:
        return "code-aware"
    if normalized_document_type in exact_or_short_document_types:
        return "recursive-overlap"
    if normalized_document_type in long_note_document_types and normalized_file_type in parent_child_file_types:
        return "parent-child"
    return "recursive-overlap"


def _parsed_document_for_storage(parsed_document: ParsedDocument) -> ParsedDocument:
    metadata = {
        key: value
        for key, value in parsed_document.metadata.items()
        if key not in {"spreadsheet_tables"}
    }
    return model_copy_update(parsed_document, {"metadata": metadata})


def _sanitize_text_for_storage(text: str) -> str:
    return text.replace("\x00", "")


def _embedding_input(chunk: ChunkRecord) -> str:
    value = chunk.metadata.get("embedding_text")
    return str(value) if isinstance(value, str) and value.strip() else chunk.content
