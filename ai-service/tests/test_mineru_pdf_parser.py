import asyncio
import base64
import os
from unittest.mock import AsyncMock, patch

os.environ["AI_RAG_USE_DATABASE"] = "false"
os.environ["MODEL_PROVIDER"] = "stub"
os.environ["LLM_PROVIDER"] = "stub"
os.environ["EMBEDDING_PROVIDER"] = "stub"
os.environ["RERANK_PROVIDER"] = "stub"

from app.core.constants import DocumentType, FileType
from app.core.config import settings
from app.rag.parsers.base import MinerUPdfParser
from app.schemas.ingest import DocumentIngestRequest, DocumentPayload


def test_mineru_timeout_falls_back_to_pdf_text() -> None:
    result, put_called = asyncio.run(_parse_timeout_case())

    assert result.metadata["status"] == "timeout"
    assert "MinerU fallback PDF text" in result.text
    assert "\x00" not in result.text
    if not settings.mineru_api_token:
        assert put_called is True


def test_mineru_done_uses_local_pdf_fallback_when_markdown_missing() -> None:
    result = asyncio.run(_parse_done_missing_markdown_case())

    assert result.metadata["status"] == "completed"
    assert "Local MinerU fallback text" in result.text
    assert "\x00" not in result.text


async def _parse_timeout_case():
    request = DocumentIngestRequest(
        knowledge_base_id="kb-pdf",
        document_id="doc-pdf",
        title="MinerU PDF",
        document_type=DocumentType.TECH_NOTE,
        file=DocumentPayload(
            filename="mineru.pdf",
            file_type=FileType.PDF,
            content_base64=_fake_pdf_base64(),
        ),
    )

    fake_poll_response = _FakeResponse({"code": 0, "data": {"state": "waiting-file"}})
    if settings.mineru_api_token:
        fake_submit_response = _FakeResponse({"code": 0, "data": {"batch_id": "task-1", "file_urls": ["https://upload.local/pdf"]}})
    else:
        fake_submit_response = _FakeResponse({"code": 0, "data": {"task_id": "task-1", "file_url": "https://upload.local/pdf"}})

    with patch("httpx.AsyncClient") as client_cls, patch("asyncio.sleep", new=AsyncMock()):
        client = client_cls.return_value.__aenter__.return_value
        client.post = AsyncMock(side_effect=[fake_submit_response])
        client.put = AsyncMock(return_value=_FakeResponse({}))
        client.get = AsyncMock(side_effect=[fake_poll_response] * 70)
        parser = MinerUPdfParser()
        return await parser.parse(
            raw_content="%PDF-1.4\x00\x00binary-stream",
            request=request,
        ), client.put.called


async def _parse_done_missing_markdown_case():
    request = DocumentIngestRequest(
        knowledge_base_id="kb-pdf",
        document_id="doc-pdf-done",
        title="MinerU PDF Done",
        document_type=DocumentType.TECH_NOTE,
        file=DocumentPayload(
            filename="mineru-done.pdf",
            file_type=FileType.PDF,
            content_base64=_fake_pdf_base64_with_text("Local MinerU fallback text"),
        ),
    )

    fake_submit_response = _FakeResponse({"code": 0, "data": {"task_id": "task-done", "file_url": "https://upload.local/pdf"}})
    fake_done_response = _FakeResponse({"code": 0, "data": {"state": "done", "markdown_url": "https://cdn.local/missing.md"}})

    with patch("httpx.AsyncClient") as client_cls, patch("asyncio.sleep", new=AsyncMock()):
        client = client_cls.return_value.__aenter__.return_value
        client.post = AsyncMock(return_value=fake_submit_response)
        client.put = AsyncMock(return_value=_FakeResponse({}))
        client.get = AsyncMock(side_effect=[fake_done_response, _FakeResponse({"not": "used"})])
        parser = MinerUPdfParser()
        return await parser.parse(
            raw_content="%PDF-1.4\x00\x00binary-stream",
            request=request,
        )


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload
        self.content = b""
        self.status_code = 200
        self.text = ""

    def json(self) -> dict[str, object]:
        return self._payload


def _fake_pdf_base64() -> str:
    pdf_bytes = b"%PDF-1.4\nBT /F1 12 Tf 72 720 Td (MinerU fallback PDF text) Tj ET\n%%EOF"
    return base64.b64encode(pdf_bytes).decode("ascii")


def _fake_pdf_base64_with_text(text: str) -> str:
    pdf_bytes = f"%PDF-1.4\nBT /F1 12 Tf 72 720 Td ({text}) Tj ET\n%%EOF".encode("utf-8")
    return base64.b64encode(pdf_bytes).decode("ascii")
