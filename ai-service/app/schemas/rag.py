from pydantic import BaseModel, Field

from app.core.constants import DocumentType
from app.schemas.common import SourceMetadata, TraceMetadata


class RagRequestContext(BaseModel):
    knowledge_base_id: str
    session_id: str | None = None
    message_id: str | None = None
    document_types: list[DocumentType] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata_filters: dict[str, object] = Field(default_factory=dict)


class RagRetrieveRequest(BaseModel):
    query: str
    top_k: int = 5
    strategy_name: str = "basic-rag"
    context: RagRequestContext


class RagRetrieveResponse(BaseModel):
    query: str
    strategy_name: str
    results: list[SourceMetadata]
    trace: TraceMetadata


class RagQueryRequest(BaseModel):
    question: str
    top_k: int = 5
    strategy_name: str = "basic-rag"
    context: RagRequestContext


class RagQueryResponse(BaseModel):
    question: str
    answer: str
    citations: list[SourceMetadata]
    trace: TraceMetadata


class RagEvaluateRequest(BaseModel):
    question: str
    expected_answer: str | None = None
    generated_answer: str | None = None
    citations: list[SourceMetadata] = Field(default_factory=list)
    strategy_name: str = "basic-rag"
    context: RagRequestContext


class RagEvaluationResult(BaseModel):
    grounded_score: float
    retrieval_score: float
    notes: list[str] = Field(default_factory=list)


class RagEvaluateResponse(BaseModel):
    result: RagEvaluationResult
    trace: TraceMetadata
