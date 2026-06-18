from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.agent import AgentInvokeRequest, AgentWorkflowStep, ReviewCard, StudyPlan, SupportPlan
from app.schemas.common import SourceMetadata, TraceMetadata


class SupportRouteState(BaseModel):
    question_type: str = "general"
    selected_strategy_name: str = "basic-rag"
    has_log_or_code_signal: bool = False
    early_return: bool = False
    final_status: str = "running"


class IncidentContext(BaseModel):
    product_name: str = ""
    module_name: str = ""
    version: str = ""
    environment: str = ""
    tenant_or_region: str = ""
    symptom: str = ""
    error_codes: list[str] = Field(default_factory=list)
    log_snippets: list[str] = Field(default_factory=list)
    trace_ids: list[str] = Field(default_factory=list)
    impact_scope: str = ""
    severity_hint: str = "low"
    started_at: str = ""
    recent_changes: list[str] = Field(default_factory=list)
    attempted_actions: list[str] = Field(default_factory=list)
    customer_expectation: str = ""
    missing_fields: list[str] = Field(default_factory=list)


class ClarificationResult(BaseModel):
    can_continue: bool = True
    missing_required_fields: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class RetrievalEvidencePack(BaseModel):
    strategy_name: str = "basic-rag"
    rewritten_query: str | None = None
    answer: str = ""
    citations: list[SourceMetadata] = Field(default_factory=list)
    evidence_coverage: float = 0.0
    missing_evidence_reasons: list[str] = Field(default_factory=list)
    rag_trace: TraceMetadata | None = None


class CodeLogAnalysisResult(BaseModel):
    triggered: bool = False
    detected_error_type: str = ""
    suspected_component: str = ""
    key_signals: list[str] = Field(default_factory=list)
    timeline_hints: list[str] = Field(default_factory=list)
    safe_checks: list[str] = Field(default_factory=list)
    unsafe_actions: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class DiagnosisHypothesis(BaseModel):
    summary: str
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    needs_validation: bool = True


class DiagnosisResult(BaseModel):
    summary: str = ""
    hypotheses: list[DiagnosisHypothesis] = Field(default_factory=list)
    diagnostic_steps: list[dict[str, object]] = Field(default_factory=list)
    fallback_actions: list[str] = Field(default_factory=list)
    evidence_mapping: dict[str, list[str]] = Field(default_factory=dict)
    confidence: float = 0.0


class RiskReviewResult(BaseModel):
    risk_level: str = "low"
    unsafe_actions: list[str] = Field(default_factory=list)
    required_human_confirmations: list[str] = Field(default_factory=list)
    data_safety_notes: list[str] = Field(default_factory=list)
    production_change_notes: list[str] = Field(default_factory=list)
    requires_escalation: bool = False
    escalation_reason: str = ""
    allowed_next_actions: list[str] = Field(default_factory=list)


class EscalationResult(BaseModel):
    required: bool = False
    severity: str = "low"
    suggested_queue: str = "frontline-support"
    ticket_summary: str = ""
    ticket_description: str = ""
    ticket_fields: dict[str, object] = Field(default_factory=dict)
    attachments: list[str] = Field(default_factory=list)


class EvaluationReviewResult(BaseModel):
    passed: bool = True
    groundedness_score: float = 0.0
    citation_coverage_score: float = 0.0
    risk_compliance_score: float = 0.0
    answer_completeness_score: float = 0.0
    hallucination_flags: list[str] = Field(default_factory=list)
    missing_required_sections: list[str] = Field(default_factory=list)
    suggested_fixes: list[str] = Field(default_factory=list)
    candidate_eval_case: dict[str, object] | None = None


class SupportAgentState(BaseModel):
    request: AgentInvokeRequest
    workflow_version: str = "support-supervisor-v1"
    support_mode: bool = True
    route: SupportRouteState = Field(default_factory=SupportRouteState)
    incident: IncidentContext = Field(default_factory=IncidentContext)
    clarification: ClarificationResult | None = None
    retrieval: RetrievalEvidencePack | None = None
    log_analysis: CodeLogAnalysisResult | None = None
    diagnosis: DiagnosisResult | None = None
    risk_review: RiskReviewResult | None = None
    escalation: EscalationResult | None = None
    evaluation_review: EvaluationReviewResult | None = None
    support_plan: SupportPlan | None = None
    study_plan: StudyPlan | None = None
    review_cards: list[ReviewCard] = Field(default_factory=list)
    answer: str = ""
    raw_rag_answer: str = ""
    citations: list[SourceMetadata] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    rag_trace_id: str | None = None
    rag_trace: TraceMetadata | None = None
    workflow_steps: list[AgentWorkflowStep] = Field(default_factory=list)
    loops: int = 0
