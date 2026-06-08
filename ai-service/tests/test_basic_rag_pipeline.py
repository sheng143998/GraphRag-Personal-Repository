import asyncio
import os

os.environ["AI_RAG_USE_DATABASE"] = "false"
os.environ["MODEL_PROVIDER"] = "stub"
os.environ["LLM_PROVIDER"] = "stub"
os.environ["EMBEDDING_PROVIDER"] = "stub"
os.environ["RERANK_PROVIDER"] = "stub"

from app.core.constants import DocumentType, FileType
from app.schemas.ingest import DocumentIngestRequest, DocumentPayload
from app.schemas.rag import RagQueryRequest, RagRequestContext
from app.services.ingest_service import IngestService
from app.services.rag_service import RagService


def test_ingest_then_query_returns_citation() -> None:
    response = asyncio.run(_ingest_then_query())
    assert response.citations
    assert "REQUIRES_NEW" in response.citations[0].metadata["content_preview"]


async def _ingest_then_query():
    ingest_service = IngestService()
    rag_service = RagService()

    await ingest_service.ingest_document(
        DocumentIngestRequest(
            knowledge_base_id="kb-test-basic",
            document_id="11111111-1111-1111-1111-111111111111",
            title="Spring Transaction Notes",
            document_type=DocumentType.TECH_NOTE,
            file=DocumentPayload(
                filename="spring-transaction-notes.md",
                file_type=FileType.MARKDOWN,
                content=(
                    "In Spring transaction propagation, REQUIRES_NEW suspends the current "
                    "transaction and starts a new independent transaction."
                ),
            ),
        )
    )

    return await rag_service.query(
        RagQueryRequest(
            question="How does REQUIRES_NEW handle the current transaction?",
            top_k=3,
            strategy_name="basic-rag",
            context=RagRequestContext(knowledge_base_id="kb-test-basic"),
        )
    )
