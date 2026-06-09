import logging

from fastapi import APIRouter, Request

from app.core.tracing import get_current_trace_id
from app.schemas.agent import AgentInvokeRequest, AgentInvokeResponse
from app.services.agent_service import AgentService


router = APIRouter()
service = AgentService()
log = logging.getLogger(__name__)


@router.post("/invoke", response_model=AgentInvokeResponse)
async def invoke_agent(payload: AgentInvokeRequest, request: Request) -> AgentInvokeResponse:
    trace_id = get_current_trace_id() or request.headers.get("x-trace-id", "")
    log.info(
        "Agent invoke received: agentName=%s, strategyName=%s, topK=%s, knowledgeBaseId=%s, traceId=%s",
        payload.agent_name,
        payload.strategy_name,
        payload.top_k,
        payload.context.knowledge_base_id,
        trace_id,
    )
    response = await service.invoke(payload)
    log.info(
        "Agent invoke completed: selectedStrategyName=%s, citationCount=%s, ragTraceId=%s, traceId=%s",
        response.selected_strategy_name,
        len(response.citations),
        response.trace.attributes.get("rag_trace_id") if response.trace.attributes else None,
        trace_id,
    )
    return response
