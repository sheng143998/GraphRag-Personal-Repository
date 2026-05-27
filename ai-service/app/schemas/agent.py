from pydantic import BaseModel, Field

from app.schemas.common import SourceMetadata, TraceMetadata
from app.schemas.rag import RagRequestContext


class AgentInvokeRequest(BaseModel):
    agent_name: str = "study-agent"
    user_input: str
    strategy_name: str = "basic-rag"
    context: RagRequestContext
    variables: dict[str, object] = Field(default_factory=dict)


class AgentInvokeResponse(BaseModel):
    agent_name: str
    output: str
    citations: list[SourceMetadata]
    trace: TraceMetadata
