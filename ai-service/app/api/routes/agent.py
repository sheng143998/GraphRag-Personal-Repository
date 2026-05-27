from fastapi import APIRouter

from app.schemas.agent import AgentInvokeRequest, AgentInvokeResponse
from app.services.agent_service import AgentService


router = APIRouter()
service = AgentService()


@router.post("/invoke", response_model=AgentInvokeResponse)
async def invoke_agent(payload: AgentInvokeRequest) -> AgentInvokeResponse:
    return await service.invoke(payload)
