from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.ingest import DocumentIngestRequest


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


class DocxParser(PlainTextParser):
    name = "docx-parser"


class SpreadsheetParser(PlainTextParser):
    name = "spreadsheet-parser"


class MinerUPdfParser(BaseParser):
    name = "mineru-pdf-adapter"
    version = "reserved-v1"

    async def parse(self, *, raw_content: str, request: DocumentIngestRequest) -> ParsedContent:
        return ParsedContent(
            text=raw_content.strip(),
            metadata={
                "adapter": "mineru",
                "status": "reserved",
                "file_type": request.file.file_type,
            },
        )
