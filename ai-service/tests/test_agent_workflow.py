import asyncio
import os
import pytest

os.environ["AI_RAG_USE_DATABASE"] = "false"
os.environ["MODEL_PROVIDER"] = "stub"
os.environ["LLM_PROVIDER"] = "stub"
os.environ["EMBEDDING_PROVIDER"] = "stub"
os.environ["RERANK_PROVIDER"] = "stub"
os.environ["AI_AGENT_SUPPORT_WORKFLOW_RUNTIME"] = "local"

from app.core.constants import DocumentType, FileType
from app.core.pydantic_compat import model_to_dict, models_to_dicts
from app.core.tracing import reset_current_trace_id, set_current_trace_id
from app.core.tracing import TraceBuilder
from app.agents.states.support_state import EvaluationReviewResult
from app.agents.workflow import StudyAgentWorkflow
from app.schemas.agent import AgentInvokeRequest
from app.schemas.ingest import DocumentIngestRequest, DocumentPayload
from app.schemas.rag import RagRequestContext
from app.services.adapters.registry import get_llm_model_name
from app.services.agent_service import AgentService
from app.services.ingest_service import IngestService
from app.services.rag_service import RagService


def test_agent_workflow_routes_implementation_question_to_advanced_rag() -> None:
    response = asyncio.run(_invoke_agent("kb-agent-advanced", "How should I implement RAG rerank code?"))

    assert response.question_type == "implementation"
    assert response.selected_strategy_name == "advanced-rag"
    assert response.citations
    assert [step.name for step in response.workflow_steps] == [
        "classify_question",
        "select_rag_strategy",
        "retrieve_and_generate",
        "cite_sources",
        "generate_follow_up_questions",
        "generate_study_plan",
        "generate_review_cards",
    ]
    assert len(response.follow_up_questions) == 3
    assert response.trace.attributes["follow_up_questions"] == response.follow_up_questions
    assert response.study_plan is not None
    assert len(response.study_plan.steps) == 3
    assert response.trace.attributes["study_plan"] == model_to_dict(response.study_plan)
    assert len(response.review_cards) == 2
    assert response.trace.attributes["review_cards"] == models_to_dicts(response.review_cards)
    assert response.trace.attributes["question_type"] == "implementation"
    assert response.trace.attributes["selected_strategy_name"] == "advanced-rag"
    assert response.trace.attributes["rag_trace_id"]


def test_study_agent_customer_business_question_does_not_enter_support_supervisor() -> None:
    response = asyncio.run(
        _invoke_agent(
            "kb-agent-customer-segmentation",
            "客户分群算法如何实现？",
            agent_name="study-agent",
        )
    )

    assert response.support_plan is None
    assert response.question_type == "implementation"
    assert [step.name for step in response.workflow_steps] == [
        "classify_question",
        "select_rag_strategy",
        "retrieve_and_generate",
        "cite_sources",
        "generate_follow_up_questions",
        "generate_study_plan",
        "generate_review_cards",
    ]


def test_agent_workflow_respects_explicit_strategy() -> None:
    response = asyncio.run(
        _invoke_agent(
            "kb-agent-basic",
            "How does a basic RAG pipeline answer from context?",
            strategy_name="basic-rag",
        )
    )

    assert response.selected_strategy_name == "basic-rag"
    assert response.citations
    assert response.follow_up_questions
    assert response.study_plan is not None
    assert response.review_cards


def test_agent_workflow_exposes_retrieval_options_in_retrieve_step() -> None:
    response = asyncio.run(
        _invoke_agent(
            "kb-agent-options",
            "How should I implement RAG rerank code?",
            strategy_name="advanced-rag",
            retrieval_options={"vectorWeight": 0.6, "keywordWeight": 0.4},
        )
    )

    retrieve_step = next(step for step in response.workflow_steps if step.name == "retrieve_and_generate")
    assert retrieve_step.payload["retrieval_options_enabled"] is True
    assert retrieve_step.payload["retrieval_option_keys"] == [
        "keywordWeight",
        "vectorWeight",
    ]


def test_agent_workflow_reuses_request_trace_id_for_nested_rag() -> None:
    token = set_current_trace_id("trace-agent-unified")
    try:
        response = asyncio.run(
            _invoke_agent(
                "kb-agent-unified-trace",
                "How should I implement RAG rerank code?",
                strategy_name="advanced-rag",
            )
        )
    finally:
        reset_current_trace_id(token)

    retrieve_step = next(step for step in response.workflow_steps if step.name == "retrieve_and_generate")
    assert response.trace.trace_id == "trace-agent-unified"
    assert response.rag_trace is not None
    assert response.rag_trace.trace_id == "trace-agent-unified"
    assert response.rag_trace.attributes["rewritten_query"]
    assert response.trace.attributes["rag_trace_id"] == "trace-agent-unified"
    assert response.trace.attributes["rag_run_id"] == response.rag_trace.run_id
    assert response.trace.attributes["rag_rewritten_query"] == response.rag_trace.attributes["rewritten_query"]
    assert retrieve_step.payload["rag_trace_id"] == "trace-agent-unified"
    assert retrieve_step.payload["rag_rewritten_query"] == response.rag_trace.attributes["rewritten_query"]


def test_after_sales_support_agent_generates_structured_support_plan() -> None:
    response = asyncio.run(
        _invoke_agent(
            "kb-agent-support",
            "客户 P1 大面积不可用，无法登录控制台，请给出售后排障步骤。",
            agent_name="after-sales-support-agent",
            variables={"mode": "support"},
        )
    )

    assert response.question_type == "troubleshooting"
    assert response.selected_strategy_name == "advanced-rag"
    assert response.support_plan is not None
    assert response.support_plan.diagnostic_steps
    assert "Confirm impact scope" in response.support_plan.diagnostic_steps[0].action
    assert response.support_plan.escalation.required is True
    assert response.support_plan.escalation.severity == "critical"
    assert response.support_plan.escalation.suggested_queue == "tier-2-technical-support"
    assert response.support_plan.evidence_references
    assert "售后分诊摘要" in response.output
    assert "风险与升级" in response.output
    assert response.trace.attributes["support_mode"] is True
    assert response.trace.status == "completed"
    assert response.trace.attributes["workflow_runtime"] == "local"
    assert response.trace.attributes["workflow_status"] == "completed"
    assert response.trace.attributes["final_status"] == "completed"
    assert response.trace.attributes["support_escalation_required"] is True
    assert response.trace.attributes["support_plan"]["escalation"]["severity"] == "critical"
    assert response.trace.attributes["required_gates"] == [
        "clarification_agent",
        "retrieval_agent",
        "code_log_tool_agent",
        "diagnosis_agent",
        "risk_review_agent",
        "escalation_agent",
        "evaluation_review_agent",
    ]
    assert response.trace.attributes["completed_gates"] == response.trace.attributes["required_gates"]
    assert response.trace.attributes["skipped_gates"] == []
    step_names = [step.name for step in response.workflow_steps]
    assert step_names[:4] == [
        "support_supervisor_start",
        "clarification_agent",
        "retrieval_agent",
        "code_log_tool_agent",
    ]
    assert "diagnosis_agent" in step_names
    assert "risk_review_agent" in step_names
    assert "escalation_agent" in step_names
    assert "evaluation_review_agent" in step_names
    assert step_names[-1] == "support_supervisor_finish"


def test_support_supervisor_returns_clarification_before_diagnosis_when_context_is_missing() -> None:
    response = asyncio.run(
        _invoke_agent(
            "kb-agent-support-clarify",
            "Customer says it is broken.",
            agent_name="technical-support-agent",
            variables={"mode": "technical-support"},
        )
    )

    step_names = [step.name for step in response.workflow_steps]
    assert step_names == [
        "support_supervisor_start",
        "clarification_agent",
        "support_supervisor_finish",
    ]
    assert response.support_plan is not None
    assert response.support_plan.clarification_questions
    assert response.citations == []
    assert "需要先补充关键信息" in response.output
    assert response.trace.attributes["workflow_version"] == "support-supervisor-v1"
    assert response.trace.status == "needs_clarification"
    assert response.trace.attributes["workflow_status"] == "needs_clarification"
    assert response.trace.attributes["final_status"] == "needs_clarification"
    assert response.trace.attributes["support_evaluation_passed"] is None
    assert response.trace.attributes["support_evaluation_skipped_reason"] == "needs_clarification"
    assert response.trace.attributes["completed_gates"] == ["clarification_agent"]
    assert "risk_review_agent" in response.trace.attributes["skipped_gates"]
    assert "evaluation_review_agent" in response.trace.attributes["skipped_gates"]


def test_support_supervisor_triggers_log_analysis_risk_escalation_and_evaluation() -> None:
    response = asyncio.run(
        _invoke_agent(
            "kb-agent-support-log",
            (
                "P1 production customer login outage affects all users. "
                "HTTP 504 gateway timeout, trace_id=abc-123456, after release v2.3.1. "
                "Logs show upstream service timed out."
            ),
            agent_name="technical-support-agent",
            variables={"mode": "technical-support", "product": "Support Console"},
        )
    )

    step_names = [step.name for step in response.workflow_steps]
    assert "retrieval_agent" in step_names
    assert "code_log_tool_agent" in step_names
    assert "diagnosis_agent" in step_names
    assert "risk_review_agent" in step_names
    assert "escalation_agent" in step_names
    assert "evaluation_review_agent" in step_names
    log_step = next(step for step in response.workflow_steps if step.name == "code_log_tool_agent")
    assert log_step.payload["detected_error_type"] == "timeout"
    risk_step = next(step for step in response.workflow_steps if step.name == "risk_review_agent")
    assert risk_step.payload["requires_escalation"] is True
    evaluation_step = next(step for step in response.workflow_steps if step.name == "evaluation_review_agent")
    assert "groundedness_score" in evaluation_step.payload
    assert response.support_plan is not None
    assert response.support_plan.escalation.required is True
    assert response.support_plan.escalation.ticket_fields["trace_ids"] == ["abc-123456"]
    assert response.trace.attributes["support_evaluation_passed"] in {True, False}


def test_support_supervisor_marks_needs_review_when_evaluation_fails() -> None:
    forced_failure = EvaluationReviewResult(
        passed=False,
        groundedness_score=0.4,
        citation_coverage_score=0.3,
        risk_compliance_score=0.5,
        answer_completeness_score=0.6,
        hallucination_flags=["forced_review_failure"],
        missing_required_sections=["risk_review"],
        suggested_fixes=["请补充风险审查说明。"],
    )
    response = asyncio.run(
        _invoke_agent(
            "kb-agent-support-review",
            (
                "P1 production customer payment outage affects all users. "
                "HTTP 503, trace_id=pay-987654, after config change. "
                "Please truncate the cache table to recover quickly."
            ),
            agent_name="technical-support-agent",
            variables={"mode": "technical-support", "product": "Payment Console"},
            evaluation_override=forced_failure,
        )
    )

    assert response.trace.status == "needs_review"
    assert response.trace.attributes["workflow_status"] == "needs_review"
    assert response.trace.attributes["final_status"] == "needs_review"
    assert response.trace.attributes["support_evaluation_passed"] is False
    assert "人工复核要求" in response.output
    assert response.support_plan is not None
    assert any("评估审查未通过" in note for note in response.support_plan.risk_notes)
    assert response.trace.attributes["completed_gates"] == response.trace.attributes["required_gates"]


def test_study_workflow_rejects_direct_support_request_without_supervisor_gates() -> None:
    workflow = StudyAgentWorkflow(rag_service=RagService())
    trace_builder = TraceBuilder(
        operation="agent_invoke",
        strategy_name="basic-rag",
        prompt_name="agent_invoke",
        prompt_version="v1",
        model_name=get_llm_model_name(),
    )
    payload = AgentInvokeRequest(
        agent_name="technical-support-agent",
        user_input="客户 P1 大面积不可用，无法登录控制台，trace_id=abc-123456。",
        context=RagRequestContext(knowledge_base_id="kb-direct-support"),
        variables={"mode": "technical-support"},
    )

    with pytest.raises(ValueError, match="Support requests must be routed"):
        asyncio.run(workflow.run(payload=payload, trace_builder=trace_builder))


async def _invoke_agent(
    knowledge_base_id: str,
    question: str,
    *,
    agent_name: str = "study-agent",
    strategy_name: str = "basic-rag",
    retrieval_options: dict[str, object] | None = None,
    variables: dict[str, object] | None = None,
    ingest_support_notes: bool = True,
    evaluation_override: EvaluationReviewResult | None = None,
):
    ingest_service = IngestService()
    agent_service = AgentService()
    if evaluation_override is not None:
        agent_service.support_workflow.evaluation_review_agent.run = lambda state: _forced_evaluation(
            state,
            evaluation_override,
        )

    await ingest_service.ingest_document(
        DocumentIngestRequest(
            knowledge_base_id=knowledge_base_id,
            document_id=f"{knowledge_base_id}-doc",
            title="Agent Workflow Notes",
            document_type=DocumentType.TECH_NOTE,
            file=DocumentPayload(
                filename="agent-workflow.md",
                file_type=FileType.MARKDOWN,
                content=_agent_notes_content(ingest_support_notes=ingest_support_notes),
            ),
        )
    )

    return await agent_service.invoke(
        AgentInvokeRequest(
            agent_name=agent_name,
            user_input=question,
            strategy_name=strategy_name,
            top_k=3,
            context=RagRequestContext(
                knowledge_base_id=knowledge_base_id,
                retrieval_options=retrieval_options or {},
            ),
            variables=variables or {},
        )
    )


def _agent_notes_content(*, ingest_support_notes: bool) -> str:
    base = (
        "Advanced RAG can rewrite implementation questions, retrieve multiple "
        "candidate chunks, rerank them, and answer with citations. Basic RAG "
        "retrieves context and generates an answer from the selected chunks. "
    )
    if not ingest_support_notes:
        return base
    return (
        f"{base}"
        "售后支持排障要求先确认客户影响范围、错误码、trace id 和业务影响，"
        "再按 Runbook 执行安全检查；P1 或大面积不可用必须升级二线技术支持。"
    )


def _forced_evaluation(state, result: EvaluationReviewResult) -> EvaluationReviewResult:
    state.evaluation_review = result
    return result
