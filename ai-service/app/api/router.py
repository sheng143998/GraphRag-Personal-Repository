from fastapi import APIRouter

from app.api.routes import agent, health, ingest, rag


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
