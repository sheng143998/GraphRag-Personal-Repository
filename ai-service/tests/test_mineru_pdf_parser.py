import asyncio
import base64
import io
import json
import os
import zipfile
from dataclasses import replace
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
    assert put_called is True


def test_mineru_done_uses_local_pdf_fallback_when_markdown_missing() -> None:
    result = asyncio.run(_parse_done_missing_markdown_case())

    assert result.metadata["status"] == "completed"
    assert "Local MinerU fallback text" in result.text
    assert "\x00" not in result.text


def test_mineru_completed_markdown_records_block_metadata() -> None:
    result = asyncio.run(_parse_done_markdown_metadata_case())

    assert result.metadata["status"] == "completed"
    assert result.metadata["mineru_heading_count"] == 1
    assert result.metadata["mineru_image_count"] == 1
    assert result.metadata["mineru_table_count"] == 1
    assert result.metadata["mineru_formula_count"] == 1
    assert result.metadata["mineru_page_markers"] == [3]


def test_mineru_standard_file_batch_polls_batch_results_endpoint() -> None:
    result, poll_urls, client_options = asyncio.run(_parse_standard_batch_done_case())

    assert result.metadata["status"] == "completed"
    assert result.metadata["api"] == "standard"
    assert result.metadata["task_id"] == "batch-1"
    assert result.metadata["batch_id"] == "batch-1"
    assert "MinerU batch markdown" in result.text
    assert "https://mineru.net/api/v4/extract-results/batch/batch-1" in poll_urls
    assert "https://mineru.net/api/v4/extract/task/batch-1" not in poll_urls
    assert any(options.get("trust_env") is False for options in client_options)


def test_mineru_standard_file_batch_failed_state_returns_error() -> None:
    result = asyncio.run(_parse_standard_batch_failed_case())

    assert result.metadata["status"] == "failed"
    assert result.metadata["batch_id"] == "batch-failed"
    assert result.metadata["error"] == "parse failed"
    assert "MinerU fallback PDF text" in result.text


def test_mineru_standard_file_batch_reads_top_level_json_zip() -> None:
    result = asyncio.run(_parse_standard_batch_top_level_json_zip_case())

    assert result.metadata["status"] == "completed"
    assert result.metadata["result_source"] == "zip"
    assert "MinerU content list text" in result.text
    assert "| metric | value |" in result.text


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
    fake_submit_response = _submit_response("task-1", standard=False)

    test_settings = replace(settings, mineru_api_token="", mineru_poll_timeout_seconds=30, mineru_poll_interval_seconds=5)
    with patch("app.core.config.settings", test_settings), patch("httpx.AsyncClient") as client_cls, patch("asyncio.sleep", new=AsyncMock()):
        client = client_cls.return_value.__aenter__.return_value
        client.post = AsyncMock(side_effect=[fake_submit_response])
        client.put = AsyncMock(return_value=_FakeResponse({}))
        client.get = AsyncMock(side_effect=[fake_poll_response] * 10)
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

    fake_submit_response = _submit_response("task-done", standard=False)
    fake_done_response = _FakeResponse({"code": 0, "data": {"state": "done", "markdown_url": "https://cdn.local/missing.md"}})

    test_settings = replace(settings, mineru_api_token="")
    with patch("app.core.config.settings", test_settings), patch("httpx.AsyncClient") as client_cls, patch("asyncio.sleep", new=AsyncMock()):
        client = client_cls.return_value.__aenter__.return_value
        client.post = AsyncMock(return_value=fake_submit_response)
        client.put = AsyncMock(return_value=_FakeResponse({}))
        client.get = AsyncMock(side_effect=[fake_done_response, _FakeResponse({"not": "used"})])
        parser = MinerUPdfParser()
        return await parser.parse(
            raw_content="%PDF-1.4\x00\x00binary-stream",
            request=request,
        )


async def _parse_done_markdown_metadata_case():
    request = DocumentIngestRequest(
        knowledge_base_id="kb-pdf",
        document_id="doc-pdf-md",
        title="MinerU PDF Markdown",
        document_type=DocumentType.TECH_NOTE,
        file=DocumentPayload(
            filename="mineru-md.pdf",
            file_type=FileType.PDF,
            content_base64=_fake_pdf_base64_with_text("PDF fallback should not be used"),
        ),
    )

    markdown = (
        "# RAG Page\n\n"
        "Page: 3\n\n"
        "![architecture](images/page-3.png)\n\n"
        "| metric | meaning |\n"
        "| --- | --- |\n"
        "| recall | hit expected evidence |\n\n"
        "$$recall = hit / total$$"
    )
    fake_submit_response = _submit_response("task-md", standard=False)
    fake_done_response = _FakeResponse({"code": 0, "data": {"state": "done", "markdown_url": "https://cdn.local/full.md"}})

    test_settings = replace(settings, mineru_api_token="")
    with patch("app.core.config.settings", test_settings), patch("httpx.AsyncClient") as client_cls, patch("asyncio.sleep", new=AsyncMock()):
        client = client_cls.return_value.__aenter__.return_value
        client.post = AsyncMock(return_value=fake_submit_response)
        client.put = AsyncMock(return_value=_FakeResponse({}))
        client.get = AsyncMock(side_effect=[fake_done_response, _FakeResponse({}, text=markdown)])
        parser = MinerUPdfParser()
        return await parser.parse(
            raw_content="%PDF-1.4\x00\x00binary-stream",
            request=request,
        )


async def _parse_standard_batch_done_case():
    request = DocumentIngestRequest(
        knowledge_base_id="kb-pdf",
        document_id="doc-pdf-standard-batch",
        title="MinerU PDF Standard Batch",
        document_type=DocumentType.TECH_NOTE,
        file=DocumentPayload(
            filename="mineru-batch.pdf",
            file_type=FileType.PDF,
            content_base64=_fake_pdf_base64_with_text("PDF fallback should not be used"),
        ),
    )

    fake_submit_response = _submit_response("batch-1", standard=True)
    fake_done_response = _FakeResponse(
        {
            "code": 0,
            "data": {
                "extract_result": [
                    {
                        "file_name": "mineru-batch.pdf",
                        "state": "done",
                        "full_zip_url": "https://cdn.local/result.zip",
                    }
                ]
            },
        }
    )
    zip_response = _FakeResponse({}, content=_zip_markdown({"full.md": "# MinerU batch markdown\n\nDone."}))

    test_settings = replace(settings, mineru_api_token="token", mineru_poll_timeout_seconds=30, mineru_poll_interval_seconds=5)
    with patch("app.core.config.settings", test_settings), patch("httpx.AsyncClient") as client_cls, patch("asyncio.sleep", new=AsyncMock()):
        client = client_cls.return_value.__aenter__.return_value
        client.post = AsyncMock(return_value=fake_submit_response)
        client.put = AsyncMock(return_value=_FakeResponse({}))
        client.get = AsyncMock(side_effect=[fake_done_response, zip_response])
        parser = MinerUPdfParser()
        result = await parser.parse(
            raw_content="%PDF-1.4\x00\x00binary-stream",
            request=request,
        )
        poll_urls = [call.args[0] for call in client.get.call_args_list]
        client_options = [call.kwargs for call in client_cls.call_args_list]
        return result, poll_urls, client_options


async def _parse_standard_batch_failed_case():
    request = DocumentIngestRequest(
        knowledge_base_id="kb-pdf",
        document_id="doc-pdf-standard-batch-failed",
        title="MinerU PDF Standard Batch Failed",
        document_type=DocumentType.TECH_NOTE,
        file=DocumentPayload(
            filename="mineru-batch-failed.pdf",
            file_type=FileType.PDF,
            content_base64=_fake_pdf_base64(),
        ),
    )

    fake_submit_response = _submit_response("batch-failed", standard=True)
    fake_failed_response = _FakeResponse(
        {
            "code": 0,
            "data": {
                "extract_result": [
                    {
                        "file_name": "mineru-batch-failed.pdf",
                        "state": "failed",
                        "err_msg": "parse failed",
                    }
                ]
            },
        }
    )

    test_settings = replace(settings, mineru_api_token="token", mineru_poll_timeout_seconds=30, mineru_poll_interval_seconds=5)
    with patch("app.core.config.settings", test_settings), patch("httpx.AsyncClient") as client_cls, patch("asyncio.sleep", new=AsyncMock()):
        client = client_cls.return_value.__aenter__.return_value
        client.post = AsyncMock(return_value=fake_submit_response)
        client.put = AsyncMock(return_value=_FakeResponse({}))
        client.get = AsyncMock(return_value=fake_failed_response)
        parser = MinerUPdfParser()
        return await parser.parse(
            raw_content="%PDF-1.4\x00\x00binary-stream",
            request=request,
        )


async def _parse_standard_batch_top_level_json_zip_case():
    request = DocumentIngestRequest(
        knowledge_base_id="kb-pdf",
        document_id="doc-pdf-standard-top-level-json",
        title="MinerU PDF Standard Batch Top Level Json",
        document_type=DocumentType.TECH_NOTE,
        file=DocumentPayload(
            filename="mineru-json.zip.pdf",
            file_type=FileType.PDF,
            content_base64=_fake_pdf_base64_with_text("PDF fallback should not be used"),
        ),
    )

    fake_submit_response = _submit_response("batch-json", standard=True)
    fake_done_response = _FakeResponse(
        {
            "code": 0,
            "data": {
                "full_zip_url": "https://cdn.local/json-result.zip",
                "extract_result": [
                    {
                        "file_name": "mineru-json.zip.pdf",
                        "state": "done",
                    }
                ],
            },
        }
    )
    zip_response = _FakeResponse(
        {},
        content=_zip_json(
            {
                "content_list.json": [
                    {"type": "text", "text": "MinerU content list text"},
                    {"type": "table", "table_body": "| metric | value |\n| --- | --- |\n| recall | 0.8 |"},
                ]
            }
        ),
    )

    test_settings = replace(settings, mineru_api_token="token", mineru_poll_timeout_seconds=30, mineru_poll_interval_seconds=5)
    with patch("app.core.config.settings", test_settings), patch("httpx.AsyncClient") as client_cls, patch("asyncio.sleep", new=AsyncMock()):
        client = client_cls.return_value.__aenter__.return_value
        client.post = AsyncMock(return_value=fake_submit_response)
        client.put = AsyncMock(return_value=_FakeResponse({}))
        client.get = AsyncMock(side_effect=[fake_done_response, zip_response])
        parser = MinerUPdfParser()
        return await parser.parse(
            raw_content="%PDF-1.4\x00\x00binary-stream",
            request=request,
        )


class _FakeResponse:
    def __init__(self, payload: dict[str, object], text: str = "", content: bytes = b"") -> None:
        self._payload = payload
        self.content = content
        self.status_code = 200
        self.text = text

    def json(self) -> dict[str, object]:
        return self._payload


def _submit_response(task_id: str, *, standard: bool) -> _FakeResponse:
    if standard:
        return _FakeResponse({"code": 0, "data": {"batch_id": task_id, "file_urls": ["https://upload.local/pdf"]}})
    return _FakeResponse({"code": 0, "data": {"task_id": task_id, "file_url": "https://upload.local/pdf"}})


def _fake_pdf_base64() -> str:
    pdf_bytes = b"%PDF-1.4\nBT /F1 12 Tf 72 720 Td (MinerU fallback PDF text) Tj ET\n%%EOF"
    return base64.b64encode(pdf_bytes).decode("ascii")


def _fake_pdf_base64_with_text(text: str) -> str:
    pdf_bytes = f"%PDF-1.4\nBT /F1 12 Tf 72 720 Td ({text}) Tj ET\n%%EOF".encode("utf-8")
    return base64.b64encode(pdf_bytes).decode("ascii")


def _zip_markdown(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buffer.getvalue()


def _zip_json(files: dict[str, object]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, json.dumps(content, ensure_ascii=False))
    return buffer.getvalue()
