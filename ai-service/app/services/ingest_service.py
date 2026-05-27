from __future__ import annotations

from uuid import uuid4

from app.core.config import settings
from app.core.tracing import TraceBuilder
from app.db.repositories import repository
from app.rag.chunkers.base import SimpleChunker
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
        self.parser_registry = ParserRegistry()

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
        parsed_document = ParsedDocument(
            document_id=payload.document_id,
            title=payload.title,
            normalized_text=parsed_content.text,
            parser_name=parser.name,
            parser_version=parser.version,
            metadata=parsed_content.metadata,
        )
        repository.save_document(parsed_document, request=payload)
        trace_builder.add_step(
            name="parse_document",
            status="completed",
            detail="Parsed and normalized document content.",
            payload={"parser_name": parser.name, "parser_version": parser.version},
        )

        chunks = await self.chunker.chunk(parsed_document=parsed_document, request=payload)
        repository.save_chunks(payload.document_id, payload.knowledge_base_id, chunks)
        trace_builder.add_step(
            name="chunk_document",
            status="completed",
            detail="Built chunk records for storage.",
            payload={"chunk_count": len(chunks)},
        )

        if chunks:
            embeddings = await embedding_adapter.embed(
                texts=[chunk.content for chunk in chunks],
                context=AdapterCallContext(
                    trace_id=trace_builder.trace.trace_id,
                    run_id=trace_builder.trace.run_id,
                    operation="embed_chunks",
                    model_name=get_embedding_model_name(),
                    strategy_name="document-ingest",
                ),
            )
            repository.save_embeddings(
                chunks=chunks,
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
            if not chunks:
                continue
            embeddings = await embedding_adapter.embed(
                texts=[chunk.content for chunk in chunks],
                context=AdapterCallContext(
                    trace_id=trace_builder.trace.trace_id,
                    run_id=trace_builder.trace.run_id,
                    operation="embed_chunks",
                    model_name=get_embedding_model_name(),
                    strategy_name="embedding-rebuild",
                ),
            )
            repository.save_embeddings(
                chunks=chunks,
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
