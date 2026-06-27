from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class MemoryQuery(BaseModel):
    customer_id: str = ""
    product: str = ""
    version: str = ""
    environment: str = ""
    error_codes: list[str] = Field(default_factory=list)
    top_k: int = 5


class AgentMemory(BaseModel):
    memory_id: str
    memory_type: str
    scope: str = "global"
    title: str
    summary: str
    customer_id: str = ""
    product: str = ""
    version: str = ""
    environment: str = ""
    error_codes: list[str] = Field(default_factory=list)
    source: str = "in_memory_seed"
    confidence: float = 0.75
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tags: list[str] = Field(default_factory=list)


class MemoryMatch(BaseModel):
    memory: AgentMemory
    score: float
    matched_fields: list[str] = Field(default_factory=list)


class MemoryRetrievalEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = "memory.read"
    query: MemoryQuery
    matched_memories: list[MemoryMatch] = Field(default_factory=list)
    used_memory_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    rationale: str = ""


class MemoryPolicyDecision(BaseModel):
    allowed: bool
    reason: str
    required_review: bool = True
    target_memory_type: str = "experience"


class MemoryWriteCandidate(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = "memory.write.candidate"
    status: str = "candidate"
    proposed_memory: AgentMemory
    policy_decision: MemoryPolicyDecision
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    not_persisted: bool = True


class MemoryEvaluationResult(BaseModel):
    event_type: str = "memory.evaluate"
    recalled_count: int = 0
    used_count: int = 0
    memory_recall_score: float = 0.0
    notes: list[str] = Field(default_factory=list)
