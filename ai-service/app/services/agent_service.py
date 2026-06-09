import logging
import time

from app.core.tracing import TraceBuilder
from app.agents.workflow import StudyAgentWorkflow
from app.schemas.agent import AgentInvokeRequest, AgentInvokeResponse
from app.services.adapters.registry import get_llm_model_name
from app.services.rag_service import RagService

log = logging.getLogger(__name__)


class AgentService:
    def __init__(self) -> None:
        self.rag_service = RagService()
        self.workflow = StudyAgentWorkflow(rag_service=self.rag_service)

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
        trace_builder.set_attribute("question_type", state.question_type)
        trace_builder.set_attribute("selected_strategy_name", state.selected_strategy_name)
        if state.rag_trace_id:
            trace_builder.set_attribute("rag_trace_id", state.rag_trace_id)
        if state.rag_trace:
            trace_builder.set_attribute("rag_run_id", state.rag_trace.run_id)
        trace = trace_builder.finalize(status="completed")
        duration_ms = int((time.perf_counter() - started) * 1000)
        log.info(
            "Agent workflow completed: selectedStrategyName=%s, citationCount=%s, durationMs=%s, traceId=%s",
            state.selected_strategy_name,
            len(state.citations),
            duration_ms,
            trace.trace_id,
        )
        return AgentInvokeResponse(
            agent_name=payload.agent_name,
            output=state.answer,
            citations=state.citations,
            question_type=state.question_type,
            selected_strategy_name=state.selected_strategy_name,
            follow_up_questions=state.follow_up_questions,
            study_plan=state.study_plan,
            review_cards=state.review_cards,
            workflow_steps=state.steps,
            trace=trace,
            rag_trace=state.rag_trace,
        )
