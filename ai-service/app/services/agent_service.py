from app.core.config import settings
from app.core.tracing import TraceBuilder
from app.prompts.registry import prompt_registry
from app.schemas.agent import AgentInvokeRequest, AgentInvokeResponse
from app.schemas.rag import RagRetrieveRequest
from app.services.adapters.base import AdapterCallContext
from app.services.adapters.registry import get_llm_model_name, llm_adapter
from app.services.rag_service import RagService


class AgentService:
    def __init__(self) -> None:
        self.rag_service = RagService()

    async def invoke(self, payload: AgentInvokeRequest) -> AgentInvokeResponse:
        trace_builder = TraceBuilder(
            operation="agent_invoke",
            strategy_name=payload.strategy_name,
            prompt_name="agent_invoke",
            prompt_version="v1",
            model_name=get_llm_model_name(),
        )
        retrieve_response = await self.rag_service.retrieve(
            payload=RagRetrieveRequest(
                query=payload.user_input,
                top_k=5,
                strategy_name=payload.strategy_name,
                context=payload.context,
            )
        )
        trace_builder.add_step(
            name="retrieve_context",
            status="completed",
            detail="Retrieved context for agent invocation.",
            payload={
                "retrieval_trace_id": retrieve_response.trace.trace_id,
                "citation_count": len(retrieve_response.results),
            },
        )
        prompt = prompt_registry.render(
            name="agent_invoke",
            version="v1",
            variables={
                "agent_name": payload.agent_name,
                "user_input": payload.user_input,
                "context": "\n\n".join(
                    citation.metadata.get("content_preview", "") for citation in retrieve_response.results
                ),
            },
        )
        output = await llm_adapter.generate(
            prompt=prompt,
            context=AdapterCallContext(
                trace_id=trace_builder.trace.trace_id,
                run_id=trace_builder.trace.run_id,
                operation="agent_generate",
                model_name=get_llm_model_name(),
                prompt_name="agent_invoke",
                prompt_version="v1",
                strategy_name=payload.strategy_name,
            ),
        )
        trace_builder.add_step(
            name="agent_generate",
            status="completed",
            detail="Generated agent response from retrieved context.",
            model_name=settings.default_llm_model,
            payload={"citation_count": len(retrieve_response.results)},
        )
        trace = trace_builder.finalize(status="completed")
        return AgentInvokeResponse(
            agent_name=payload.agent_name,
            output=output,
            citations=retrieve_response.results,
            trace=trace,
        )
