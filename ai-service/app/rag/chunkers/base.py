from __future__ import annotations

from uuid import uuid4

from app.schemas.ingest import ChunkRecord, DocumentIngestRequest, ParsedDocument


class BaseChunker:
    async def chunk(
        self,
        *,
        parsed_document: ParsedDocument,
        request: DocumentIngestRequest,
    ) -> list[ChunkRecord]:
        raise NotImplementedError


class SimpleChunker(BaseChunker):
    async def chunk(
        self,
        *,
        parsed_document: ParsedDocument,
        request: DocumentIngestRequest,
    ) -> list[ChunkRecord]:
        text = parsed_document.normalized_text
        if not text:
            return []
        size = 500
        chunks: list[ChunkRecord] = []
        for index, offset in enumerate(range(0, len(text), size)):
            content = text[offset : offset + size]
            chunks.append(
                ChunkRecord(
                    chunk_id=str(uuid4()),
                    document_id=request.document_id,
                    knowledge_base_id=request.knowledge_base_id,
                    title=parsed_document.title,
                    chunk_index=index,
                    content=content,
                    metadata={
                        **parsed_document.metadata,
                        **request.metadata,
                        "knowledge_base_id": request.knowledge_base_id,
                        "title": parsed_document.title,
                        "document_type": request.document_type,
                        "file_type": request.file.file_type,
                        "chunk_strategy": "simple-window",
                        "content_preview": content[:600],
                        "tags": request.tags,
                        "tech_stack": request.tech_stack,
                    },
                )
            )
        return chunks
