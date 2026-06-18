import logging
import time

from app.agents.graphs.support_supervisor import SupportSupervisorWorkflow, is_support_request
from app.agents.workflow import StudyAgentWorkflow
from app.core.pydantic_compat import model_to_dict
from app.core.tracing import TraceBuilder
from app.schemas.agent import AgentInvokeRequest, AgentInvokeResponse
from app.services.adapters.registry import get_llm_model_name
from app.services.rag_service import RagService

log = logging.getLogger(__name__)


class AgentService:
    def __init__(self) -> None:
        self.rag_service = RagService()
        self.workflow = StudyAgentWorkflow(rag_service=self.rag_service)
        self.support_workflow = SupportSupervisorWorkflow(rag_service=self.rag_service)

    async def invoke(self, payload: AgentInvokeRequest) -> AgentInvokeResponse:
        started = time.perf_counter()
        trace_builder = TraceBuilder(
            operation="agent_invoke",
            strategy_name=payload.strategy_name,
            prompt_name="agent_invoke",
            prompt_version="v1",
            model_name=get_llm_model_name(),
        )
        log.info(
            "Agent workflow start: agentName=%s, strategyName=%s, questionLength=%s, traceId=%s",
            payload.agent_name,
            payload.strategy_name,
            len(payload.user_input),
            trace_builder.trace.trace_id,
        )
        try:
            if is_support_request(payload):
                state = await self.support_workflow.run(payload=payload, trace_builder=trace_builder)
            else:
                state = await self.workflow.run(payload=payload, trace_builder=trace_builder)
        except Exception:
            duration_ms = int((time.perf_counter() - started) * 1000)
            log.exception(
                "Agent workflow failed: strategyName=%s, durationMs=%s, traceId=%s",
                payload.strategy_name,
                duration_ms,
                trace_builder.trace.trace_id,
            )
            raise
        route = getattr(state, "route", None)
        question_type = getattr(state, "question_type", None) or getattr(route, "question_type", "general")
        selected_strategy_name = getattr(state, "selected_strategy_name", None) or getattr(
            route, "selected_strategy_name", payload.strategy_name
        )
        steps = getattr(state, "steps", None) or getattr(state, "workflow_steps", [])
        trace_builder.set_attribute("question_type", question_type)
        trace_builder.set_attribute("selected_strategy_name", selected_strategy_name)
        if getattr(state, "support_mode", False):
            trace_builder.set_attribute("support_mode", True)
        support_plan = getattr(state, "support_plan", None)
        if support_plan is not None:
            trace_builder.set_attribute("support_plan", model_to_dict(support_plan))
        if state.rag_trace_id:
            trace_builder.set_attribute("rag_trace_id", state.rag_trace_id)
        if state.rag_trace:
            trace_builder.set_attribute("rag_run_id", state.rag_trace.run_id)
        workflow_status = getattr(state, "workflow_status", "completed") or "completed"
        trace_builder.set_attribute("workflow_status", workflow_status)
        trace = trace_builder.finalize(status=str(workflow_status))
        duration_ms = int((time.perf_counter() - started) * 1000)
        log.info(
            "Agent workflow completed: selectedStrategyName=%s, citationCount=%s, durationMs=%s, traceId=%s",
            selected_strategy_name,
            len(state.citations),
            duration_ms,
            trace.trace_id,
        )
        return AgentInvokeResponse(
            agent_name=payload.agent_name,
            output=state.answer,
            citations=state.citations,
            question_type=question_type,
            selected_strategy_name=selected_strategy_name,
            follow_up_questions=state.follow_up_questions,
            study_plan=state.study_plan,
            review_cards=state.review_cards,
            support_plan=support_plan,
            workflow_steps=steps,
            trace=trace,
            rag_trace=state.rag_trace,
        )
