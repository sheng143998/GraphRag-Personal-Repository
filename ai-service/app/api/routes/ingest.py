from fastapi import APIRouter

from app.schemas.ingest import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    EmbeddingRebuildRequest,
    EmbeddingRebuildResponse,
)
from app.services.ingest_service import IngestService


router = APIRouter()
service = IngestService()


@router.post("/document", response_model=DocumentIngestResponse)
async def ingest_document(payload: DocumentIngestRequest) -> DocumentIngestResponse:
    return await service.ingest_document(payload)


@router.post("/rebuild-embeddings", response_model=EmbeddingRebuildResponse)
async def rebuild_embeddings(
    payload: EmbeddingRebuildRequest,
) -> EmbeddingRebuildResponse:
    return await service.rebuild_embeddings(payload)
