from app.core.tracing import TraceBuilder
from app.agents.workflow import StudyAgentWorkflow
from app.schemas.agent import AgentInvokeRequest, AgentInvokeResponse
from app.services.adapters.registry import get_llm_model_name
from app.services.rag_service import RagService


class AgentService:
    def __init__(self) -> None:
        self.rag_service = RagService()
        self.workflow = StudyAgentWorkflow(rag_service=self.rag_service)

    async def invoke(self, payload: AgentInvokeRequest) -> AgentInvokeResponse:
        trace_builder = TraceBuilder(
            operation="agent_invoke",
            strategy_name=payload.strategy_name,
            prompt_name="agent_invoke",
            prompt_version="v1",
            model_name=get_llm_model_name(),
        )
        state = await self.workflow.run(payload=payload, trace_builder=trace_builder)
        trace_builder.set_attribute("question_type", state.question_type)
        trace_builder.set_attribute("selected_strategy_name", state.selected_strategy_name)
        if state.rag_trace_id:
            trace_builder.set_attribute("rag_trace_id", state.rag_trace_id)
        trace = trace_builder.finalize(status="completed")
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
        )
