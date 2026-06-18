import os

os.environ["AI_RAG_USE_DATABASE"] = "false"
os.environ["MODEL_PROVIDER"] = "stub"
os.environ["LLM_PROVIDER"] = "stub"
os.environ["EMBEDDING_PROVIDER"] = "stub"
os.environ["RERANK_PROVIDER"] = "stub"

from app.agents.graphs.support_supervisor import is_support_request
from app.agents.nodes.clarification_agent import ClarificationAgent
from app.agents.nodes.evaluation_review_agent import EvaluationReviewAgent
from app.agents.nodes.risk_review_agent import RiskReviewAgent
from app.agents.states.support_state import DiagnosisResult, EscalationResult, SupportAgentState
from app.schemas.agent import AgentInvokeRequest
from app.schemas.common import SourceMetadata
from app.schemas.rag import RagRequestContext


def test_risk_review_escalates_missing_evidence_and_blocks_destructive_action() -> None:
    state = _support_state("P1 production outage, please restart and truncate broken cache table.")
    state.incident.severity_hint = "high"

    result = RiskReviewAgent().run(state)

    assert result.requires_escalation is True
    assert result.risk_level == "high"
    assert result.required_human_confirmations
    assert any("human" in item.lower() or "owner" in item.lower() for item in result.required_human_confirmations)
    assert any("destructive" in item.lower() or "production" in item.lower() for item in result.unsafe_actions)


def test_real_chinese_support_request_and_incident_fields_are_detected() -> None:
    state = _support_state("客户 P1 大面积不可用，无法登录控制台，生产环境，日志显示 HTTP 504，trace_id=abc-123456。")

    assert is_support_request(state.request) is True
    result = ClarificationAgent().run(state)

    assert result.can_continue is True
    assert state.incident.module_name == "登录"
    assert state.incident.environment == "production"
    assert state.incident.impact_scope == "major"
    assert state.incident.severity_hint == "critical"
    assert state.route.has_log_or_code_signal is True


def test_risk_review_scans_raw_rag_answer_for_unsafe_actions() -> None:
    state = _support_state("客户反馈登录偶发超时，当前问题已收敛。")
    state.citations = [
        SourceMetadata(
            document_id="doc-support-runbook",
            chunk_id="chunk-runbook-1",
            title="Support Runbook",
        )
    ]
    state.raw_rag_answer = "可以先直接重启生产网关，并删除异常会话记录。"

    result = RiskReviewAgent().run(state)

    assert result.requires_escalation is True
    assert result.required_human_confirmations
    assert any("production" in item.lower() for item in result.unsafe_actions)
    assert any("destructive" in item.lower() for item in result.unsafe_actions)


def test_evaluation_review_generates_draft_case_for_failed_gate() -> None:
    state = _support_state("Customer reports a login outage but no runbook evidence was retrieved.")
    state.route.question_type = "troubleshooting"
    state.route.selected_strategy_name = "advanced-rag"
    state.diagnosis = DiagnosisResult(summary="Tentative diagnosis.", diagnostic_steps=[])
    state.risk_review = None
    state.escalation = EscalationResult(required=False)

    result = EvaluationReviewAgent().run(state)

    assert result.passed is False
    assert "risk_review" in result.missing_required_sections
    assert result.candidate_eval_case is not None
    draft = result.candidate_eval_case
    assert draft["status"] == "DRAFT"
    assert draft["source"] == "support_evaluation_review_agent"
    assert draft["humanDecision"] == ""
    assert "needs-human-review" in draft["tags"]
    assert draft["metadata"]["requiresRiskReview"] is True
    assert draft["metadata"]["passedEvaluationReview"] is False
    assert "diagnostic_steps" in draft["metadata"]["missingRequiredSections"]
    assert "risk_review" in draft["metadata"]["missingRequiredSections"]


def test_evaluation_review_fails_missing_citations_even_when_escalated() -> None:
    state = _support_state("P1 production customer login outage, trace_id=abc-123456.")
    state.route.question_type = "troubleshooting"
    state.route.selected_strategy_name = "advanced-rag"
    state.diagnosis = DiagnosisResult(
        summary="No grounded root cause yet.",
        diagnostic_steps=[
            {
                "order": 1,
                "action": "Collect more evidence.",
                "expected_signal": "A cited runbook or log pattern supports the diagnosis.",
            }
        ],
    )
    state.risk_review = RiskReviewAgent().run(state)
    state.escalation = EscalationResult(required=True, severity="high")
    state.answer = (
        "售后分诊摘要\nNo grounded root cause yet.\n\n"
        "诊断步骤\n1. Collect more evidence.\n\n"
        "风险与升级\nEscalate."
    )

    result = EvaluationReviewAgent().run(state)

    assert result.passed is False
    assert "missing_citations" in result.hallucination_flags
    assert result.candidate_eval_case is not None
    assert "missing-evidence" in result.candidate_eval_case["tags"]


def test_evaluation_review_generates_importable_case_for_passed_gate() -> None:
    state = _support_state("P1 production customer login outage with HTTP 504 and trace_id=abc-123456.")
    state.route.question_type = "troubleshooting"
    state.route.selected_strategy_name = "advanced-rag"
    state.route.has_log_or_code_signal = True
    state.incident.severity_hint = "critical"
    state.incident.impact_scope = "major"
    state.incident.error_codes = ["P1", "HTTP 504"]
    state.incident.trace_ids = ["abc-123456"]
    state.citations = [
        SourceMetadata(
            document_id="doc-support-runbook",
            chunk_id="chunk-runbook-1",
            title="Support Runbook",
            score=0.91,
        )
    ]
    state.diagnosis = DiagnosisResult(
        summary="Gateway timeout likely comes from upstream dependency.",
        diagnostic_steps=[
            {
                "order": 1,
                "action": "Check gateway health.",
                "expected_signal": "Gateway timeout rate confirms the symptom.",
            }
        ],
    )
    state.risk_review = RiskReviewAgent().run(state)
    state.escalation = EscalationResult(required=True, severity="critical")
    state.answer = (
        "售后分诊摘要\nGateway timeout likely comes from upstream dependency.\n\n"
        "诊断步骤\n1. Check gateway health.\n\n"
        "风险与升级\nEscalate to tier-2."
    )

    result = EvaluationReviewAgent().run(state)

    assert result.passed is True
    assert result.candidate_eval_case is not None
    draft = result.candidate_eval_case
    assert draft["caseId"].startswith("support-agent-kb-support-nodes-pass")
    assert draft["requiredChunkIds"] == ["chunk-runbook-1"]
    assert draft["relevantDocumentIds"] == ["doc-support-runbook"]
    assert draft["topK"] == 3
    assert "requires-escalation" in draft["tags"]
    assert "log-or-code-analysis" in draft["tags"]
    assert draft["metadata"]["requiresEscalation"] is True
    assert draft["metadata"]["severity"] == "critical"
    assert draft["metadata"]["traceIds"] == ["abc-123456"]
    assert draft["metadata"]["expectedWorkflowNodes"][-1] == "evaluation_review_agent"


def _support_state(question: str) -> SupportAgentState:
    return SupportAgentState(
        request=AgentInvokeRequest(
            agent_name="technical-support-agent",
            user_input=question,
            strategy_name="basic-rag",
            top_k=3,
            context=RagRequestContext(knowledge_base_id="kb-support-nodes"),
            variables={"mode": "technical-support"},
        )
    )
