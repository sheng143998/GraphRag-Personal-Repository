from fastapi import APIRouter

from app.schemas.rag import (
    RagEvaluateRequest,
    RagEvaluateResponse,
    RagQueryRequest,
    RagQueryResponse,
    RagRetrieveRequest,
    RagRetrieveResponse,
)
from app.services.rag_service import RagService


router = APIRouter()
service = RagService()


@router.post("/retrieve", response_model=RagRetrieveResponse)
async def rag_retrieve(payload: RagRetrieveRequest) -> RagRetrieveResponse:
    return await service.retrieve(payload)


@router.post("/query", response_model=RagQueryResponse)
async def rag_query(payload: RagQueryRequest) -> RagQueryResponse:
    return await service.query(payload)


@router.post("/evaluate", response_model=RagEvaluateResponse)
async def rag_evaluate(payload: RagEvaluateRequest) -> RagEvaluateResponse:
    return await service.evaluate(payload)
