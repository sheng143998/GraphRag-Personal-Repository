from datetime import datetime

from pydantic import BaseModel, Field


class SourceMetadata(BaseModel):
    document_id: str
    chunk_id: str
    title: str
    source_path: str | None = None
    score: float | None = None
    rerank_score: float | None = None
    page_number: int | None = None
    sheet_name: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class TraceStep(BaseModel):
    name: str
    status: str
    detail: str
    model_name: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    timestamp: datetime


class TraceMetadata(BaseModel):
    trace_id: str
    run_id: str
    operation: str
    strategy_name: str
    prompt_name: str | None = None
    prompt_version: str | None = None
    model_name: str | None = None
    status: str = "running"
    started_at: datetime
    finished_at: datetime | None = None
    latency_ms: float | None = None
    error_message: str | None = None
    steps: list[TraceStep] = Field(default_factory=list)
    attributes: dict[str, object] = Field(default_factory=dict)
