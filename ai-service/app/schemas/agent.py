from pydantic import BaseModel, Field

from app.schemas.common import SourceMetadata, TraceMetadata
from app.schemas.rag import RagRequestContext


class AgentInvokeRequest(BaseModel):
    agent_name: str = "study-agent"
    user_input: str
    strategy_name: str = "basic-rag"
    top_k: int = Field(default=5, ge=1, le=20)
    context: RagRequestContext
    variables: dict[str, object] = Field(default_factory=dict)


class AgentWorkflowStep(BaseModel):
    name: str
    detail: str
    payload: dict[str, object] = Field(default_factory=dict)


class AgentInvokeResponse(BaseModel):
    agent_name: str
    output: str
    citations: list[SourceMetadata]
    question_type: str = "general"
    selected_strategy_name: str = "basic-rag"
    workflow_steps: list[AgentWorkflowStep] = Field(default_factory=list)
    trace: TraceMetadata
