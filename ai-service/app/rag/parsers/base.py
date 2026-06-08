from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.ingest import DocumentIngestRequest
import base64
import io


@dataclass(slots=True)
class ParsedContent:
    text: str
    metadata: dict[str, object] = field(default_factory=dict)


class BaseParser:
    name = "base-parser"
    version = "v1"

    async def parse(self, *, raw_content: str, request: DocumentIngestRequest) -> ParsedContent:
        raise NotImplementedError


class PlainTextParser(BaseParser):
    name = "plain-text-parser"
    version = "v1"

    async def parse(self, *, raw_content: str, request: DocumentIngestRequest) -> ParsedContent:
        return ParsedContent(
            text=raw_content.strip(),
            metadata={
                "document_type": request.document_type,
                "file_type": request.file.file_type,
            },
        )


class HtmlParser(PlainTextParser):
    name = "html-parser"


class DocxParser(BaseParser):
    name = "docx-parser"
    version = "v2"

    async def parse(self, *, raw_content: str, request: DocumentIngestRequest) -> ParsedContent:
        text_parts: list[str] = []

        if raw_content:
            text_parts.append(raw_content.strip())

        content_b64 = request.file.content_base64 or ""
        if not content_b64 and request.file.content:
            content_b64 = request.file.content

        if content_b64:
            try:
                import docx
                decoded = base64.b64decode(content_b64)
                doc = docx.Document(io.BytesIO(decoded))

                for para in doc.paragraphs:
                    t = para.text.strip()
                    if t:
                        text_parts.append(t)

                for table in doc.tables:
                    for row in table.rows:
                        row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                        if row_texts:
                            text_parts.append(" | ".join(row_texts))
            except Exception:
                pass

        combined = "\n\n".join(text_parts).strip()
        return ParsedContent(
            text=combined,
            metadata={
                "document_type": request.document_type,
                "file_type": request.file.file_type,
                "parser": self.name,
                "parser_version": self.version,
            },
        )


class SpreadsheetParser(PlainTextParser):
    name = "spreadsheet-parser"


class MinerUPdfParser(BaseParser):
    name = "mineru-pdf-adapter"
    version = "v3"

    async def parse(self, *, raw_content: str, request: DocumentIngestRequest) -> ParsedContent:
        import asyncio
        import httpx
        import zipfile
        import io as _io
        from app.core.config import settings

        token = settings.mineru_api_token
        use_standard = bool(token)

        poll_timeout = 120
        poll_interval = 2

        file_name = request.file.filename or "document.pdf"
        content_b64 = request.file.content_base64 or ""
        source_url = request.file.source_path or request.file.content or raw_content
        if source_url and source_url.startswith(("http://", "https://")):
            source_url = source_url.strip()
        use_file = bool(content_b64)
        use_url = bool(source_url and source_url.startswith("https://"))

        print(f"[MinerU] mode={'standard' if use_standard else 'agent'} file={use_file} url={use_url} name={file_name}")

        if not use_file and not use_url:
            return ParsedContent(text="", metadata={"adapter": "mineru", "status": "skipped", "reason": "no_content_or_url", "file_type": request.file.file_type})

        api_mode = "standard" if use_standard else "agent"
        headers = {"Content-Type": "application/json"}
        if use_standard:
            headers["Authorization"] = f"Bearer {token}"

        # Use a single client with generous timeout for the whole flow
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            task_id = ""
            try:
                if use_file:
                    decoded_bytes = base64.b64decode(content_b64)
                    print(f"[MinerU] file size={len(decoded_bytes)} bytes")

                    if use_standard:
                        resp = await client.post(
                            "https://mineru.net/api/v4/file-urls/batch",
                            headers=headers,
                            json={"files": [{"name": file_name}]},
                        )
                        data = resp.json()
                        if data.get("code") != 0:
                            return ParsedContent(text="", metadata={"adapter": "mineru", "status": "submit_failed", "error": data.get("msg", "unknown"), "api": api_mode, "file_type": request.file.file_type})
                        batch_id = data["data"]["batch_id"]
                        upload_url = data["data"]["file_urls"][0]
                        put_resp = await client.put(upload_url, content=decoded_bytes)
                        print(f"[MinerU] PUT status={put_resp.status_code}")
                        await asyncio.sleep(2)
                        task_id = batch_id
                    else:
                        # Agent API: send file_content directly in JSON (inline mode)
                        resp = await client.post(
                            "https://mineru.net/api/v1/agent/parse/file",
                            headers=headers,
                            json={
                                "file_name": file_name,
                                "language": "ch",
                                "enable_table": True,
                                "file_content": content_b64,
                            },
                        )
                        data = resp.json()
                        print(f"[MinerU] parse/file: code={data.get('code')} msg={data.get('msg')}")
                        if data.get("code") != 0:
                            return ParsedContent(text="", metadata={"adapter": "mineru", "status": "submit_failed", "error": data.get("msg", "unknown"), "api": api_mode, "file_type": request.file.file_type})
                        task_id = data["data"]["task_id"]
                        print(f"[MinerU] task_id={task_id}")
                elif use_url and use_standard:
                    resp = await client.post(
                        f"{settings.mineru_api_base_url}/extract/task",
                        headers=headers,
                        json={"url": source_url, "model_version": "vlm"},
                    )
                    data = resp.json()
                    if data.get("code") != 0:
                        return ParsedContent(text="", metadata={"adapter": "mineru", "status": "submit_failed", "error": data.get("msg", "unknown"), "api": api_mode, "file_type": request.file.file_type})
                    task_id = data["data"]["task_id"]
                else:
                    resp = await client.post(
                        "https://mineru.net/api/v1/agent/parse/url",
                        headers=headers,
                        json={"url": source_url, "language": "ch", "enable_table": True},
                    )
                    data = resp.json()
                    if data.get("code") != 0:
                        return ParsedContent(text="", metadata={"adapter": "mineru", "status": "submit_failed", "error": data.get("msg", "unknown"), "api": api_mode, "file_type": request.file.file_type})
                    task_id = data["data"]["task_id"]
            except Exception as e:
                print(f"[MinerU] submit error: {type(e).__name__}: {e}")
                return ParsedContent(text="", metadata={"adapter": "mineru", "status": "submit_error", "error": str(e), "api": api_mode, "file_type": request.file.file_type})

            # Poll for result
            elapsed = 0
            while elapsed < poll_timeout:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                try:
                    if use_standard:
                        poll_url = f"https://mineru.net/api/v4/extract/task/{task_id}"
                        poll_resp = await client.get(poll_url, headers=headers)
                    else:
                        poll_resp = await client.get(
                            f"https://mineru.net/api/v1/agent/parse/{task_id}",
                            headers=headers,
                        )
                    poll = poll_resp.json()
                    if poll.get("code") != 0:
                        continue
                    state = poll["data"]["state"]
                    if elapsed % 10 <= poll_interval:
                        print(f"[MinerU] poll {elapsed}s: {state}")
                    if state == "done":
                        if use_standard:
                            md_text = ""
                            zip_url = poll["data"].get("full_zip_url", "")
                            if zip_url:
                                try:
                                    zip_resp = await client.get(zip_url)
                                    with zipfile.ZipFile(_io.BytesIO(zip_resp.content)) as zf:
                                        for name in zf.namelist():
                                            if name.endswith(".md"):
                                                md_text = zf.read(name).decode("utf-8", errors="replace")
                                                if "full" in name.lower():
                                                    break
                                except Exception:
                                    pass
                            if not md_text:
                                md_url = poll["data"].get("markdown_url", "")
                                if md_url:
                                    try:
                                        md_text = (await client.get(md_url)).text
                                    except Exception:
                                        pass
                        else:
                            md_url = poll["data"].get("markdown_url") or poll["data"].get("full_md_url", "")
                            if md_url:
                                try:
                                    md_resp = await client.get(md_url)
                                    md_text = md_resp.text
                                    print(f"[MinerU] DONE! md={len(md_text)} chars")
                                except Exception as e2:
                                    print(f"[MinerU] md download error: {e2}")
                                    md_text = ""
                            else:
                                print(f"[MinerU] DONE but no md_url in response")
                                md_text = ""
                        return ParsedContent(
                            text=md_text.strip(),
                            metadata={
                                "adapter": "mineru",
                                "status": "completed",
                                "task_id": task_id,
                                "elapsed_seconds": elapsed,
                                "api": api_mode,
                                "file_type": request.file.file_type,
                            },
                        )
                    if state == "failed":
                        err = poll["data"].get("err_msg", "unknown")
                        print(f"[MinerU] FAILED: {err}")
                        return ParsedContent(text="", metadata={"adapter": "mineru", "status": "failed", "task_id": task_id, "error": err, "api": api_mode, "file_type": request.file.file_type})
                except Exception:
                    continue
            print(f"[MinerU] TIMEOUT after {elapsed}s")
            return ParsedContent(text="", metadata={"adapter": "mineru", "status": "timeout", "task_id": task_id, "elapsed_seconds": elapsed, "api": api_mode, "file_type": request.file.file_type})