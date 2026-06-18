from __future__ import annotations

from app.agents.states.support_state import RetrievalEvidencePack, SupportAgentState
from app.schemas.rag import RagQueryRequest
from app.services.rag_service import RagService


class RetrievalAgent:
    name = "retrieval_agent"

    def __init__(self, *, rag_service: RagService) -> None:
        self.rag_service = rag_service

    async def run(self, state: SupportAgentState) -> RetrievalEvidencePack:
        strategy_name = state.route.selected_strategy_name or "advanced-rag"
        response = await self.rag_service.query(
            RagQueryRequest(
                question=state.request.user_input,
                top_k=state.request.top_k,
                strategy_name=strategy_name,
                context=state.request.context,
            )
        )
        citations = response.citations
        rewritten_query = None
        if response.trace.attributes:
            rewritten_query = response.trace.attributes.get("rewritten_query")
        coverage = min(1.0, len(citations) / max(1, state.request.top_k))
        missing_reasons = [] if citations else ["no_retrieved_citations"]
        result = RetrievalEvidencePack(
            strategy_name=strategy_name,
            rewritten_query=str(rewritten_query) if rewritten_query else None,
            answer=response.answer,
            citations=citations,
            evidence_coverage=coverage,
            missing_evidence_reasons=missing_reasons,
            rag_trace=response.trace,
        )
        state.retrieval = result
        state.raw_rag_answer = response.answer
        state.answer = response.answer
        state.citations = citations
        state.rag_trace = response.trace
        state.rag_trace_id = response.trace.trace_id
        return result

