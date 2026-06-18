from __future__ import annotations

import os
from typing import Any, TypedDict

from app.agents.nodes.clarification_agent import ClarificationAgent
from app.agents.nodes.code_log_tool_agent import CodeLogToolAgent
from app.agents.nodes.diagnosis_agent import DiagnosisAgent
from app.agents.nodes.escalation_agent import EscalationAgent
from app.agents.nodes.evaluation_review_agent import EvaluationReviewAgent
from app.agents.nodes.retrieval_agent import RetrievalAgent
from app.agents.nodes.risk_review_agent import RiskReviewAgent
from app.agents.runnables.support_nodes import support_node_runnable
from app.agents.states.support_state import SupportAgentState
from app.core.pydantic_compat import model_to_dict
from app.core.tracing import TraceBuilder
from app.schemas.agent import (
    AgentInvokeRequest,
    AgentWorkflowStep,
    DiagnosticStep,
    EscalationRecommendation,
    ReviewCard,
    StudyPlan,
    SupportPlan,
)
from app.services.rag_service import RagService


class _SupportGraphState(TypedDict):
    state: SupportAgentState


class SupportSupervisorWorkflow:
    """Controlled supervisor for after-sales technical support.

    The supervisor uses explicit code gates instead of free-form LLM routing.
    `needs_clarification` is the only terminal state that may skip later gates;
    every diagnostic terminal state must pass risk review and evaluation review.
    """

    BASE_REQUIRED_GATES = [
        "clarification_agent",
        "retrieval_agent",
        "diagnosis_agent",
        "risk_review_agent",
        "escalation_agent",
        "evaluation_review_agent",
    ]
    CONDITIONAL_GATES = ["code_log_tool_agent"]

    def __init__(self, *, rag_service: RagService) -> None:
        self.clarification_agent = ClarificationAgent()
        self.retrieval_agent = RetrievalAgent(rag_service=rag_service)
        self.code_log_tool_agent = CodeLogToolAgent()
        self.diagnosis_agent = DiagnosisAgent()
        self.risk_review_agent = RiskReviewAgent()
        self.escalation_agent = EscalationAgent()
        self.evaluation_review_agent = EvaluationReviewAgent()

    async def run(self, *, payload: AgentInvokeRequest, trace_builder: TraceBuilder) -> SupportAgentState:
        state = self._initialize_state(payload=payload, trace_builder=trace_builder)
        requested_runtime = _support_workflow_runtime_mode()
        trace_builder.set_attribute("workflow_requested_runtime", requested_runtime)
        if requested_runtime == "local":
            trace_builder.set_attribute("support_workflow_runtime_fallback_reason", "explicit_local_runtime")
            return await self._run_local(state=state, trace_builder=trace_builder)

        langgraph_runtime = _load_langgraph_runtime()
        if langgraph_runtime is None:
            fallback_reason = "langgraph_dependency_unavailable"
            trace_builder.set_attribute("support_workflow_runtime_fallback_reason", fallback_reason)
            if requested_runtime == "langgraph":
                raise RuntimeError(
                    "LangGraph runtime was requested but langgraph is not installed. "
                    "Install ai-service dependencies or set AI_AGENT_SUPPORT_WORKFLOW_RUNTIME=auto/local."
                )
            return await self._run_local(state=state, trace_builder=trace_builder)
        try:
            graph = self._build_langgraph(runtime=langgraph_runtime, trace_builder=trace_builder)
        except Exception as exc:  # pragma: no cover - only exercised when optional dependency is installed.
            trace_builder.set_attribute(
                "support_workflow_runtime_error",
                f"{type(exc).__name__}: {exc}",
            )
            raise

        state.workflow_runtime = "langgraph"
        trace_builder.set_attribute("workflow_runtime", state.workflow_runtime)
        try:
            result = await graph.ainvoke({"state": state})
        except Exception as exc:  # pragma: no cover - depends on optional runtime internals.
            trace_builder.set_attribute(
                "support_workflow_runtime_error",
                f"{type(exc).__name__}: {exc}",
            )
            raise
        return result["state"]

    def _initialize_state(self, *, payload: AgentInvokeRequest, trace_builder: TraceBuilder) -> SupportAgentState:
        state = SupportAgentState(request=payload)
        state.route.question_type = _classify_question(payload.user_input)
        state.route.selected_strategy_name = _select_strategy(payload, state.route.question_type)
        state.required_gates = list(self.BASE_REQUIRED_GATES)
        trace_builder.trace.strategy_name = state.route.selected_strategy_name
        trace_builder.set_attribute("support_mode", True)
        trace_builder.set_attribute("workflow_version", state.workflow_version)
        trace_builder.set_attribute("workflow_runtime", state.workflow_runtime)
        trace_builder.set_attribute("workflow_status", state.workflow_status)
        trace_builder.set_attribute("question_type", state.route.question_type)
        trace_builder.set_attribute("selected_strategy_name", state.route.selected_strategy_name)
        trace_builder.set_attribute("required_gates", state.required_gates)
        return state

    async def _run_local(self, *, state: SupportAgentState, trace_builder: TraceBuilder) -> SupportAgentState:
        state.workflow_runtime = "local"
        trace_builder.set_attribute("workflow_runtime", state.workflow_runtime)
        self._node_start(state, trace_builder)

        clarification = self._node_clarification(state, trace_builder)
        if not clarification.can_continue:
            self._mark_skipped_remaining_gates(state)
            self._node_finish(state, trace_builder)
            return state

        await self._node_retrieval(state, trace_builder)
        if state.route.has_log_or_code_signal:
            self._node_code_log(state, trace_builder)
        else:
            self._mark_skipped_gate(state, self.code_log_tool_agent.name)
        self._node_diagnosis(state, trace_builder)
        self._node_risk_review(state, trace_builder)
        self._node_escalation(state, trace_builder)
        self._node_prepare_final_draft(state)
        self._node_evaluation_review(state, trace_builder)
        self._node_finish(state, trace_builder)
        return state

    def _build_langgraph(self, *, runtime: tuple[Any, Any, Any], trace_builder: TraceBuilder) -> Any:
        StateGraph, START, END = runtime
        graph = StateGraph(_SupportGraphState)

        async def retrieval_node(graph_state: _SupportGraphState) -> _SupportGraphState:
            return await self._graph_retrieval(graph_state, trace_builder)

        graph.add_node(
            "support_supervisor_start",
            support_node_runnable(
                "support_supervisor_start",
                lambda graph_state: self._graph_start(graph_state, trace_builder),
            ),
        )
        graph.add_node(
            self.clarification_agent.name,
            support_node_runnable(
                self.clarification_agent.name,
                lambda graph_state: self._graph_clarification(graph_state, trace_builder),
            ),
        )
        graph.add_node(self.retrieval_agent.name, support_node_runnable(self.retrieval_agent.name, retrieval_node))
        graph.add_node(
            self.code_log_tool_agent.name,
            support_node_runnable(
                self.code_log_tool_agent.name,
                lambda graph_state: self._graph_code_log(graph_state, trace_builder),
            ),
        )
        graph.add_node(
            self.diagnosis_agent.name,
            support_node_runnable(
                self.diagnosis_agent.name,
                lambda graph_state: self._graph_diagnosis(graph_state, trace_builder),
            ),
        )
        graph.add_node(
            self.risk_review_agent.name,
            support_node_runnable(
                self.risk_review_agent.name,
                lambda graph_state: self._graph_risk_review(graph_state, trace_builder),
            ),
        )
        graph.add_node(
            self.escalation_agent.name,
            support_node_runnable(
                self.escalation_agent.name,
                lambda graph_state: self._graph_escalation(graph_state, trace_builder),
            ),
        )
        graph.add_node(
            "prepare_final_draft",
            support_node_runnable("prepare_final_draft", self._graph_prepare_final_draft),
        )
        graph.add_node(
            self.evaluation_review_agent.name,
            support_node_runnable(
                self.evaluation_review_agent.name,
                lambda graph_state: self._graph_evaluation_review(graph_state, trace_builder),
            ),
        )
        graph.add_node(
            "support_supervisor_finish",
            support_node_runnable(
                "support_supervisor_finish",
                lambda graph_state: self._graph_finish(graph_state, trace_builder),
            ),
        )

        graph.add_edge(START, "support_supervisor_start")
        graph.add_edge("support_supervisor_start", self.clarification_agent.name)
        graph.add_conditional_edges(
            self.clarification_agent.name,
            self._route_after_clarification,
            {
                "finish": "support_supervisor_finish",
                "retrieval": self.retrieval_agent.name,
            },
        )
        graph.add_conditional_edges(
            self.retrieval_agent.name,
            self._route_after_retrieval,
            {
                "code_log": self.code_log_tool_agent.name,
                "diagnosis": self.diagnosis_agent.name,
            },
        )
        graph.add_edge(self.code_log_tool_agent.name, self.diagnosis_agent.name)
        graph.add_edge(self.diagnosis_agent.name, self.risk_review_agent.name)
        graph.add_edge(self.risk_review_agent.name, self.escalation_agent.name)
        graph.add_edge(self.escalation_agent.name, "prepare_final_draft")
        graph.add_edge("prepare_final_draft", self.evaluation_review_agent.name)
        graph.add_edge(self.evaluation_review_agent.name, "support_supervisor_finish")
        graph.add_edge("support_supervisor_finish", END)
        return graph.compile()

    def _graph_start(self, graph_state: _SupportGraphState, trace_builder: TraceBuilder) -> _SupportGraphState:
        self._node_start(graph_state["state"], trace_builder)
        return graph_state

    def _graph_clarification(
        self,
        graph_state: _SupportGraphState,
        trace_builder: TraceBuilder,
    ) -> _SupportGraphState:
        clarification = self._node_clarification(graph_state["state"], trace_builder)
        if not clarification.can_continue:
            self._mark_skipped_remaining_gates(graph_state["state"])
        return graph_state

    async def _graph_retrieval(
        self,
        graph_state: _SupportGraphState,
        trace_builder: TraceBuilder,
    ) -> _SupportGraphState:
        await self._node_retrieval(graph_state["state"], trace_builder)
        return graph_state

    def _graph_code_log(self, graph_state: _SupportGraphState, trace_builder: TraceBuilder) -> _SupportGraphState:
        self._node_code_log(graph_state["state"], trace_builder)
        return graph_state

    def _graph_diagnosis(self, graph_state: _SupportGraphState, trace_builder: TraceBuilder) -> _SupportGraphState:
        self._node_diagnosis(graph_state["state"], trace_builder)
        return graph_state

    def _graph_risk_review(
        self,
        graph_state: _SupportGraphState,
        trace_builder: TraceBuilder,
    ) -> _SupportGraphState:
        self._node_risk_review(graph_state["state"], trace_builder)
        return graph_state

    def _graph_escalation(self, graph_state: _SupportGraphState, trace_builder: TraceBuilder) -> _SupportGraphState:
        self._node_escalation(graph_state["state"], trace_builder)
        return graph_state

    def _graph_prepare_final_draft(self, graph_state: _SupportGraphState) -> _SupportGraphState:
        self._node_prepare_final_draft(graph_state["state"])
        return graph_state

    def _graph_evaluation_review(
        self,
        graph_state: _SupportGraphState,
        trace_builder: TraceBuilder,
    ) -> _SupportGraphState:
        self._node_evaluation_review(graph_state["state"], trace_builder)
        return graph_state

    def _graph_finish(self, graph_state: _SupportGraphState, trace_builder: TraceBuilder) -> _SupportGraphState:
        self._node_finish(graph_state["state"], trace_builder)
        return graph_state

    def _route_after_clarification(self, graph_state: _SupportGraphState) -> str:
        state = graph_state["state"]
        if state.clarification and not state.clarification.can_continue:
            return "finish"
        return "retrieval"

    def _route_after_retrieval(self, graph_state: _SupportGraphState) -> str:
        state = graph_state["state"]
        if state.route.has_log_or_code_signal:
            return "code_log"
        self._mark_skipped_gate(state, self.code_log_tool_agent.name)
        return "diagnosis"

    def _node_start(self, state: SupportAgentState, trace_builder: TraceBuilder) -> None:
        self._sync_gate_contract(state)
        self._set_workflow_attributes(state, trace_builder)
        self._record_step(
            state,
            trace_builder,
            name="support_supervisor_start",
            detail="Started controlled support supervisor workflow.",
            payload={
                "workflow_version": state.workflow_version,
                "question_type": state.route.question_type,
                "selected_strategy_name": state.route.selected_strategy_name,
                "workflow_runtime": state.workflow_runtime,
                "required_gates": state.required_gates,
            },
        )

    def _node_clarification(
        self,
        state: SupportAgentState,
        trace_builder: TraceBuilder,
    ):
        clarification = self.clarification_agent.run(state)
        self._sync_gate_contract(state)
        self._record_step(
            state,
            trace_builder,
            name=self.clarification_agent.name,
            detail="Extracted incident context and required clarifications.",
            payload={
                "can_continue": clarification.can_continue,
                "missing_required_fields": clarification.missing_required_fields,
                "clarification_count": len(clarification.clarification_questions),
                "severity_hint": state.incident.severity_hint,
                "has_log_or_code_signal": state.route.has_log_or_code_signal,
            },
        )
        self._mark_completed_gate(state, self.clarification_agent.name)
        if not clarification.can_continue:
            state.answer = _compose_clarification_response(clarification.clarification_questions)
            state.support_plan = _support_plan_from_state(state)
            state.follow_up_questions = clarification.clarification_questions
            state.study_plan = _study_plan_from_state(state)
            state.review_cards = _review_cards_from_state(state)
            state.workflow_status = "needs_clarification"
            state.route.final_status = "needs_clarification"
        return clarification

    async def _node_retrieval(self, state: SupportAgentState, trace_builder: TraceBuilder) -> None:
        retrieval = await self.retrieval_agent.run(state)
        self._record_step(
            state,
            trace_builder,
            name=self.retrieval_agent.name,
            detail="Retrieved support evidence from the knowledge base.",
            payload={
                "strategy_name": retrieval.strategy_name,
                "citation_count": len(retrieval.citations),
                "evidence_coverage": retrieval.evidence_coverage,
                "missing_evidence_reasons": retrieval.missing_evidence_reasons,
                "rag_trace_id": retrieval.rag_trace.trace_id if retrieval.rag_trace else None,
                "rag_run_id": retrieval.rag_trace.run_id if retrieval.rag_trace else None,
                "rewritten_query": retrieval.rewritten_query,
            },
        )
        if retrieval.rewritten_query:
            trace_builder.set_attribute("rag_rewritten_query", retrieval.rewritten_query)
        self._mark_completed_gate(state, self.retrieval_agent.name)

    def _node_code_log(self, state: SupportAgentState, trace_builder: TraceBuilder) -> None:
        if state.route.has_log_or_code_signal:
            log_analysis = self.code_log_tool_agent.run(state)
            self._record_step(
                state,
                trace_builder,
                name=self.code_log_tool_agent.name,
                detail="Analyzed user-provided code, error code, trace id, or log signal.",
                payload=model_to_dict(log_analysis),
            )
            self._mark_completed_gate(state, self.code_log_tool_agent.name)

    def _node_diagnosis(self, state: SupportAgentState, trace_builder: TraceBuilder) -> None:
        diagnosis = self.diagnosis_agent.run(state)
        self._record_step(
            state,
            trace_builder,
            name=self.diagnosis_agent.name,
            detail="Generated grounded support diagnosis and diagnostic steps.",
            payload={
                "hypothesis_count": len(diagnosis.hypotheses),
                "diagnostic_step_count": len(diagnosis.diagnostic_steps),
                "confidence": diagnosis.confidence,
                "summary": diagnosis.summary,
            },
        )
        self._mark_completed_gate(state, self.diagnosis_agent.name)

    def _node_risk_review(self, state: SupportAgentState, trace_builder: TraceBuilder) -> None:
        risk_review = self.risk_review_agent.run(state)
        self._record_step(
            state,
            trace_builder,
            name=self.risk_review_agent.name,
            detail="Reviewed production, data, and evidence risks before final response.",
            payload=model_to_dict(risk_review),
        )
        self._mark_completed_gate(state, self.risk_review_agent.name)

    def _node_escalation(self, state: SupportAgentState, trace_builder: TraceBuilder) -> None:
        risk_review = state.risk_review
        if risk_review and risk_review.requires_escalation:
            escalation = self.escalation_agent.run(state)
            self._record_step(
                state,
                trace_builder,
                name=self.escalation_agent.name,
                detail="Prepared support ticket escalation draft.",
                payload=model_to_dict(escalation),
            )
        else:
            state.escalation = self.escalation_agent.run(state)
            self._record_step(
                state,
                trace_builder,
                name=self.escalation_agent.name,
                detail="Prepared frontline ticket context without escalation.",
                payload=model_to_dict(state.escalation),
            )
        self._mark_completed_gate(state, self.escalation_agent.name)

    def _node_prepare_final_draft(self, state: SupportAgentState) -> None:
        state.support_plan = _support_plan_from_state(state)
        state.answer = _compose_final_response(state)

    def _node_evaluation_review(self, state: SupportAgentState, trace_builder: TraceBuilder) -> None:
        evaluation = self.evaluation_review_agent.run(state)
        self._record_step(
            state,
            trace_builder,
            name=self.evaluation_review_agent.name,
            detail="Evaluated evidence grounding, risk compliance, and answer completeness.",
            payload=model_to_dict(evaluation),
        )
        self._mark_completed_gate(state, self.evaluation_review_agent.name)

        state.support_plan = _support_plan_from_state(state)
        state.answer = _compose_final_response(state)
        self._apply_evaluation_outcome(state)
        state.follow_up_questions = _follow_up_questions_from_state(state)
        state.study_plan = _study_plan_from_state(state)
        state.review_cards = _review_cards_from_state(state)

    def _node_finish(self, state: SupportAgentState, trace_builder: TraceBuilder) -> None:
        evaluation_skipped_reason = None
        if state.route.final_status == "needs_clarification":
            evaluation_skipped_reason = "needs_clarification"
        self._sync_gate_contract(state)
        _finalize_support_trace(state, trace_builder, evaluation_skipped_reason=evaluation_skipped_reason)
        self._set_workflow_attributes(state, trace_builder)
        detail = (
            "Stopped before diagnosis because required support information is missing."
            if state.route.final_status == "needs_clarification"
            else "Finished controlled support supervisor workflow."
        )
        self._record_step(
            state,
            trace_builder,
            name="support_supervisor_finish",
            detail=detail,
            payload={
                "final_status": state.route.final_status,
                "workflow_status": state.workflow_status,
                "workflow_runtime": state.workflow_runtime,
                "evaluation_passed": state.evaluation_review.passed if state.evaluation_review else None,
                "required_gates": state.required_gates,
                "completed_gates": state.completed_gates,
                "skipped_gates": state.skipped_gates,
            },
        )

    def _apply_evaluation_outcome(self, state: SupportAgentState) -> None:
        evaluation = state.evaluation_review
        if evaluation is None or evaluation.passed:
            state.workflow_status = "completed"
            state.route.final_status = "completed"
            return
        state.workflow_status = "needs_review"
        state.route.final_status = "needs_review"
        missing = "、".join(evaluation.missing_required_sections) or "无"
        flags = "、".join(evaluation.hallucination_flags) or "无"
        fixes = evaluation.suggested_fixes or ["请由人工复核证据、风险和最终答复后再执行。"]
        notice_lines = [
            "",
            "人工复核要求",
            f"- 评估审查未通过，当前状态：{state.route.final_status}。",
            f"- 缺失项：{missing}。",
            f"- 风险标记：{flags}。",
            *[f"- 修复建议：{fix}" for fix in fixes],
        ]
        notice = "\n".join(notice_lines)
        if "人工复核要求" not in state.answer:
            state.answer = f"{state.answer}\n{notice}"
        if state.support_plan:
            risk_note = "评估审查未通过，必须人工复核证据、风险和最终答复后再继续。"
            next_action = "先修复评估审查缺失项，再由负责人确认是否执行或升级。"
            if risk_note not in state.support_plan.risk_notes:
                state.support_plan.risk_notes.append(risk_note)
            if next_action not in state.support_plan.next_actions:
                state.support_plan.next_actions.insert(0, next_action)

    def _mark_completed_gate(self, state: SupportAgentState, gate: str) -> None:
        _append_unique(state.completed_gates, gate)
        state.skipped_gates = [item for item in state.skipped_gates if item != gate]
        self._sync_gate_contract(state)

    def _mark_skipped_gate(self, state: SupportAgentState, gate: str) -> None:
        if gate in state.completed_gates:
            return
        _append_unique(state.skipped_gates, gate)
        self._sync_gate_contract(state)

    def _mark_skipped_remaining_gates(self, state: SupportAgentState) -> None:
        self._sync_gate_contract(state)
        for gate in state.required_gates:
            if gate not in state.completed_gates:
                self._mark_skipped_gate(state, gate)
        for gate in self.CONDITIONAL_GATES:
            if gate not in state.completed_gates:
                self._mark_skipped_gate(state, gate)

    def _sync_gate_contract(self, state: SupportAgentState) -> None:
        required = list(self.BASE_REQUIRED_GATES)
        if state.route.has_log_or_code_signal and self.code_log_tool_agent.name not in required:
            required.insert(required.index(self.diagnosis_agent.name), self.code_log_tool_agent.name)
        state.required_gates = required
        state.completed_gates = _dedupe(state.completed_gates)
        state.skipped_gates = _dedupe(
            gate for gate in state.skipped_gates if gate not in state.completed_gates
        )

    def _set_workflow_attributes(self, state: SupportAgentState, trace_builder: TraceBuilder) -> None:
        trace_builder.set_attribute("workflow_version", state.workflow_version)
        trace_builder.set_attribute("workflow_runtime", state.workflow_runtime)
        trace_builder.set_attribute("workflow_status", state.workflow_status)
        trace_builder.set_attribute("final_status", state.route.final_status)
        trace_builder.set_attribute("required_gates", state.required_gates)
        trace_builder.set_attribute("completed_gates", state.completed_gates)
        trace_builder.set_attribute("skipped_gates", state.skipped_gates)

    def _record_step(
        self,
        state: SupportAgentState,
        trace_builder: TraceBuilder,
        *,
        name: str,
        detail: str,
        payload: dict[str, object],
    ) -> None:
        state.workflow_steps.append(AgentWorkflowStep(name=name, detail=detail, payload=payload))
        trace_builder.add_step(name=name, status="completed", detail=detail, payload=payload)


def is_support_request(payload: AgentInvokeRequest) -> bool:
    variables = payload.variables or {}
    mode_values = {
        str(variables.get("mode", "")).lower(),
        str(variables.get("scenario", "")).lower(),
        str(variables.get("agent_profile", "")).lower(),
    }
    text = payload.user_input.lower()
    agent_name = payload.agent_name.lower()
    real_chinese_support_signal = _contains_any(
        text,
        ("工单", "售后", "报修", "升级二线", "客户问题", "客户故障", "客户报障", "客户投诉"),
    )
    real_chinese_customer_incident_signal = _contains_any(text, ("客户",)) and _contains_any(
        text,
        ("故障", "异常", "报错", "不可用", "超时", "中断", "无法", "告警"),
    )
    explicit_agent = any(term in agent_name for term in ("support", "after-sales", "aftersales", "customer-success"))
    explicit_mode = bool(mode_values & {"support", "after-sales", "aftersales", "technical-support", "customer-support"})
    strong_support_signal = _contains_any(
        text,
        (
            "support ticket",
            "customer issue",
            "customer incident",
            "sla",
            "ticket escalation",
            "工单",
            "售后",
            "报修",
            "升级二线",
            "客户问题",
            "客户故障",
            "客户报障",
            "客户投诉",
        ),
    )
    customer_incident_signal = _contains_any(text, ("customer", "客户")) and _contains_any(
        text,
        (
            "outage",
            "down",
            "fault",
            "failure",
            "error",
            "exception",
            "unavailable",
            "timeout",
            "broken",
            "incident",
            "故障",
            "异常",
            "报错",
            "不可用",
            "超时",
            "中断",
            "无法",
            "告警",
        ),
    )
    return (
        explicit_agent
        or explicit_mode
        or strong_support_signal
        or customer_incident_signal
        or real_chinese_support_signal
        or real_chinese_customer_incident_signal
    )


def _classify_question(text: str) -> str:
    lowered = text.lower()
    if _contains_any(lowered, ("无法", "故障", "异常", "告警", "不可用", "报错", "超时", "中断")):
        return "troubleshooting"
    if _contains_any(
        lowered,
        ("bug", "error", "exception", "failed", "outage", "down", "fault", "failure", "无法", "故障", "异常", "告警", "不可用"),
    ):
        return "troubleshooting"
    if _contains_any(lowered, ("code", "class", "function", "api", "实现", "代码", "接口")):
        return "implementation"
    if _contains_any(lowered, ("interview", "面试", "八股")):
        return "interview"
    if _contains_any(lowered, ("what", "why", "how", "原理", "什么", "为什么", "如何")):
        return "conceptual"
    return "general"


def _select_strategy(payload: AgentInvokeRequest, question_type: str) -> str:
    if payload.strategy_name and payload.strategy_name != "basic-rag":
        return payload.strategy_name
    if question_type in {"implementation", "troubleshooting", "interview"}:
        return "advanced-rag"
    if payload.context.metadata_filters:
        return "metadata-filter"
    return "advanced-rag"


def _support_plan_from_state(state: SupportAgentState) -> SupportPlan:
    clarification_questions = []
    if state.clarification:
        clarification_questions = state.clarification.clarification_questions
    evidence_references = _evidence_refs(state)
    diagnostic_steps = []
    if state.diagnosis:
        for item in state.diagnosis.diagnostic_steps:
            diagnostic_steps.append(
                DiagnosticStep(
                    order=int(item.get("order") or len(diagnostic_steps) + 1),
                    action=str(item.get("action") or ""),
                    expected_signal=str(item.get("expected_signal") or ""),
                    evidence_hint=", ".join(str(ref) for ref in item.get("evidence_refs") or []),
                    fallback=str(item.get("fallback") or ""),
                )
            )
    escalation = state.escalation
    risk_review = state.risk_review
    risk_notes = []
    if risk_review:
        risk_notes.extend(risk_review.data_safety_notes)
        risk_notes.extend(risk_review.production_change_notes)
        risk_notes.extend(risk_review.required_human_confirmations)
    if state.evaluation_review and not state.evaluation_review.passed:
        risk_notes.append("评估审查未通过，需人工复核证据、风险和最终答复后再继续。")
    return SupportPlan(
        issue_summary=f"售后支持案例：{state.incident.symptom or state.request.user_input[:80]}",
        clarification_questions=clarification_questions,
        evidence_references=evidence_references,
        diagnostic_steps=diagnostic_steps,
        escalation=EscalationRecommendation(
            required=bool(escalation and escalation.required),
            severity=escalation.severity if escalation else state.incident.severity_hint,
            reason=(risk_review.escalation_reason if risk_review else ""),
            suggested_queue=escalation.suggested_queue if escalation else "frontline-support",
            ticket_summary=escalation.ticket_summary if escalation else "",
            ticket_fields=escalation.ticket_fields if escalation else {},
        ),
        risk_notes=risk_notes or ["所有诊断结论必须基于引用证据；涉及生产风险时需人工确认。"],
        next_actions=_next_actions(state),
    )


def _compose_clarification_response(questions: list[str]) -> str:
    lines = ["需要先补充关键信息，暂不进入诊断。", "", "请补充："]
    lines.extend(f"- {question}" for question in questions)
    return "\n".join(lines)


def _compose_final_response(state: SupportAgentState) -> str:
    plan = state.support_plan or _support_plan_from_state(state)
    summary = state.raw_rag_answer.strip() if state.citations else ""
    if not summary and state.diagnosis:
        summary = state.diagnosis.summary
    if not state.citations and state.escalation and state.escalation.required:
        summary = (
            f"{summary} 当前证据不足，只能作为待验证假设；请升级并由人工复核。"
        ).strip()
    if not summary:
        summary = "当前没有可用的 RAG 回答。"
    lines = [
        "售后分诊摘要",
        summary,
        "",
        "澄清问题",
        *([f"- {question}" for question in plan.clarification_questions] or ["- 暂无必须补充的问题。"]),
        "",
        "证据引用",
        *([f"- {reference}" for reference in plan.evidence_references] or ["- 未检索到可引用的知识库证据。"]),
        "",
        "诊断步骤",
        *[
            f"{step.order}. {step.action} 预期信号：{step.expected_signal}"
            for step in plan.diagnostic_steps
        ],
        "",
        "风险与升级",
        f"- 是否升级：{'是' if plan.escalation.required else '否'}",
        f"- 严重度：{plan.escalation.severity}",
        f"- 原因：{plan.escalation.reason or '当前可按一线流程继续，但需保留证据。'}",
        "",
        "风险提示",
        *[f"- {note}" for note in plan.risk_notes],
        "",
        "下一步动作",
        *[f"- {action}" for action in plan.next_actions],
    ]
    return "\n".join(lines)


def _follow_up_questions_from_state(state: SupportAgentState) -> list[str]:
    topic = state.incident.symptom or state.request.user_input[:60]
    if state.clarification and not state.clarification.can_continue:
        return state.clarification.clarification_questions
    return [
        f"{topic} 还缺哪些客户现场信息？",
        f"哪个诊断信号最能验证 {topic} 的根因？",
        f"{topic} 是否已经满足升级到二线支持的条件？",
    ]


def _study_plan_from_state(state: SupportAgentState) -> StudyPlan:
    return StudyPlan(
        summary=f"对 {state.incident.symptom or state.request.user_input[:60]} 进行售后支持分诊。",
        focus_areas=[
            state.route.question_type,
            state.route.selected_strategy_name,
            state.incident.severity_hint,
        ],
        steps=[
            "补齐影响范围、错误码、日志和 trace id。",
            "按诊断步骤执行只读检查，并把结果附到工单。",
            "根据风险审查和评估审查决定是否升级。",
        ],
    )


def _review_cards_from_state(state: SupportAgentState) -> list[ReviewCard]:
    topic = state.incident.symptom or state.request.user_input[:60]
    return [
        ReviewCard(
            question=f"处理 {topic} 前必须先确认哪些信息？",
            expected_answer="确认影响范围、环境、错误码、trace id、日志证据、回滚路径和负责人。",
            source_hint=_evidence_refs(state)[0] if _evidence_refs(state) else "",
            difficulty="medium",
        ),
        ReviewCard(
            question=f"{topic} 什么时候必须升级？",
            expected_answer="高影响、证据不足、涉及生产变更或数据安全风险时必须升级。",
            source_hint=_evidence_refs(state)[0] if _evidence_refs(state) else "",
            difficulty="hard",
        ),
    ]


def _evidence_refs(state: SupportAgentState) -> list[str]:
    refs = []
    for index, citation in enumerate(state.citations[:3], start=1):
        parts = [f"[{index}] {citation.title}"]
        if citation.chunk_id:
            parts.append(f"chunk={citation.chunk_id}")
        if citation.score is not None:
            parts.append(f"score={citation.score:.2f}")
        refs.append(" ".join(parts))
    return refs


def _next_actions(state: SupportAgentState) -> list[str]:
    if state.clarification and not state.clarification.can_continue:
        return ["先补齐澄清问题，再重新进入检索和诊断。"]
    actions = []
    if state.risk_review:
        actions.extend(state.risk_review.allowed_next_actions[:2])
    if state.escalation and state.escalation.required:
        actions.append("将工单草稿转交二线技术支持，并附上 trace id、证据 chunk 和已执行检查。")
    else:
        actions.append("按诊断步骤继续一线排查，并记录每一步结果。")
    return actions


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword and keyword in text for keyword in keywords)


def _load_langgraph_runtime() -> tuple[Any, Any, Any] | None:
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        return None
    return StateGraph, START, END


def _support_workflow_runtime_mode() -> str:
    mode = os.getenv("AI_AGENT_SUPPORT_WORKFLOW_RUNTIME", "").strip().lower()
    if mode in {"local", "auto", "langgraph"}:
        return mode
    legacy_flag = os.getenv("AI_AGENT_ENABLE_LANGGRAPH_RUNTIME", "").strip().lower()
    if legacy_flag in {"1", "true", "yes", "on"}:
        return "langgraph"
    if legacy_flag in {"0", "false", "no", "off"}:
        return "local"
    return "auto"


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _dedupe(values) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _finalize_support_trace(
    state: SupportAgentState,
    trace_builder: TraceBuilder,
    *,
    evaluation_skipped_reason: str | None = None,
) -> None:
    trace_builder.set_attribute("workflow_version", state.workflow_version)
    trace_builder.set_attribute("workflow_runtime", state.workflow_runtime)
    trace_builder.set_attribute("workflow_status", state.workflow_status)
    trace_builder.set_attribute("final_status", state.route.final_status)
    trace_builder.set_attribute("required_gates", state.required_gates)
    trace_builder.set_attribute("completed_gates", state.completed_gates)
    trace_builder.set_attribute("skipped_gates", state.skipped_gates)
    if state.support_plan is not None:
        trace_builder.set_attribute("support_plan", model_to_dict(state.support_plan))
        trace_builder.set_attribute("support_escalation_required", state.support_plan.escalation.required)
        trace_builder.set_attribute("support_severity", state.support_plan.escalation.severity)
    trace_builder.set_attribute(
        "support_evaluation_passed",
        state.evaluation_review.passed if state.evaluation_review else None,
    )
    if evaluation_skipped_reason:
        trace_builder.set_attribute("support_evaluation_skipped_reason", evaluation_skipped_reason)
    if state.rag_trace_id:
        trace_builder.set_attribute("rag_trace_id", state.rag_trace_id)
    if state.rag_trace:
        trace_builder.set_attribute("rag_run_id", state.rag_trace.run_id)
