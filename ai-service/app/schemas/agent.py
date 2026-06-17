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


class StudyPlan(BaseModel):
    summary: str
    focus_areas: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)


class ReviewCard(BaseModel):
    question: str
    expected_answer: str
    source_hint: str = ""
    difficulty: str = "medium"


class DiagnosticStep(BaseModel):
    order: int
    action: str
    expected_signal: str = ""
    evidence_hint: str = ""
    fallback: str = ""


class EscalationRecommendation(BaseModel):
    required: bool = False
    severity: str = "low"
    reason: str = ""
    suggested_queue: str = "technical-support"
    ticket_summary: str = ""
    ticket_fields: dict[str, object] = Field(default_factory=dict)


class SupportPlan(BaseModel):
    issue_summary: str
    clarification_questions: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    diagnostic_steps: list[DiagnosticStep] = Field(default_factory=list)
    escalation: EscalationRecommendation = Field(default_factory=EscalationRecommendation)
    risk_notes: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class AgentInvokeResponse(BaseModel):
    agent_name: str
    output: str
    citations: list[SourceMetadata]
    question_type: str = "general"
    selected_strategy_name: str = "basic-rag"
    follow_up_questions: list[str] = Field(default_factory=list)
    study_plan: StudyPlan | None = None
    review_cards: list[ReviewCard] = Field(default_factory=list)
    support_plan: SupportPlan | None = None
    workflow_steps: list[AgentWorkflowStep] = Field(default_factory=list)
    trace: TraceMetadata
    rag_trace: TraceMetadata | None = None
