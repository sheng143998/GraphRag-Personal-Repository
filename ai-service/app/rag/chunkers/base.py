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


class ParentChildChunker(BaseChunker):
    async def chunk(
        self,
        *,
        parsed_document: ParsedDocument,
        request: DocumentIngestRequest,
    ) -> list[ChunkRecord]:
        text = parsed_document.normalized_text
        if not text:
            return []

        parent_size = _bounded_int(request.metadata.get("parent_chunk_size"), default=1500, minimum=500, maximum=4000)
        child_size = _bounded_int(request.metadata.get("child_chunk_size"), default=500, minimum=100, maximum=1500)
        if child_size >= parent_size:
            child_size = max(100, parent_size // 3)
        chunks: list[ChunkRecord] = []
        chunk_index = 0
        for parent_offset in range(0, len(text), parent_size):
            parent_content = text[parent_offset : parent_offset + parent_size]
            parent_id = str(uuid4())
            child_records: list[ChunkRecord] = []
            for child_offset in range(0, len(parent_content), child_size):
                child_content = parent_content[child_offset : child_offset + child_size]
                child_records.append(
                    ChunkRecord(
                        chunk_id=str(uuid4()),
                        document_id=request.document_id,
                        knowledge_base_id=request.knowledge_base_id,
                        parent_chunk_id=parent_id,
                        title=parsed_document.title,
                        chunk_index=0,
                        content=child_content,
                        metadata=_chunk_metadata(
                            parsed_document=parsed_document,
                            request=request,
                            content=child_content,
                            chunk_strategy="parent-child",
                            chunk_level="child",
                        ),
                    )
                )

            chunks.append(
                ChunkRecord(
                    chunk_id=parent_id,
                    document_id=request.document_id,
                    knowledge_base_id=request.knowledge_base_id,
                    title=parsed_document.title,
                    chunk_index=chunk_index,
                    content=parent_content,
                    metadata={
                        **_chunk_metadata(
                            parsed_document=parsed_document,
                            request=request,
                            content=parent_content,
                            chunk_strategy="parent-child",
                            chunk_level="parent",
                        ),
                        "child_chunk_ids": [child.chunk_id for child in child_records],
                    },
                )
            )
            chunk_index += 1

            for child in child_records:
                chunks.append(child.copy(update={"chunk_index": chunk_index}))
                chunk_index += 1
        return chunks


def _chunk_metadata(
    *,
    parsed_document: ParsedDocument,
    request: DocumentIngestRequest,
    content: str,
    chunk_strategy: str,
    chunk_level: str,
) -> dict[str, object]:
    return {
        **parsed_document.metadata,
        **request.metadata,
        "knowledge_base_id": request.knowledge_base_id,
        "title": parsed_document.title,
        "document_type": request.document_type,
        "file_type": request.file.file_type,
        "chunk_strategy": chunk_strategy,
        "chunk_level": chunk_level,
        "content_preview": content[:600],
        "tags": request.tags,
        "tech_stack": request.tech_stack,
    }


def _bounded_int(value: object, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed < minimum:
        return minimum
    if parsed > maximum:
        return maximum
    return parsed
