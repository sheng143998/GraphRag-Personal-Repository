from pydantic import BaseModel, Field

from app.core.constants import DocumentType, FileType
from app.schemas.common import TraceMetadata


class DocumentPayload(BaseModel):
    filename: str
    file_type: FileType
    content: str | None = None
    content_base64: str | None = None
    source_path: str | None = None
    mime_type: str | None = None


class DocumentIngestRequest(BaseModel):
    knowledge_base_id: str
    document_id: str
    title: str
    document_type: DocumentType
    file: DocumentPayload
    tags: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class ParsedDocument(BaseModel):
    document_id: str
    title: str
    normalized_text: str
    parser_name: str
    parser_version: str
    metadata: dict[str, object] = Field(default_factory=dict)


class ChunkRecord(BaseModel):
    chunk_id: str
    document_id: str
    knowledge_base_id: str | None = None
    parent_chunk_id: str | None = None
    title: str | None = None
    chunk_index: int
    content: str
    metadata: dict[str, object] = Field(default_factory=dict)


class DocumentIngestResponse(BaseModel):
    document_id: str
    chunk_count: int
    parser_name: str
    file_type: FileType
    trace: TraceMetadata


class EmbeddingRebuildRequest(BaseModel):
    knowledge_base_id: str
    document_ids: list[str] = Field(default_factory=list)


class EmbeddingRebuildResponse(BaseModel):
    knowledge_base_id: str
    rebuilt_documents: list[str]
    trace: TraceMetadata
