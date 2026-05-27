from app.core.constants import FileType
from app.rag.parsers.base import (
    BaseParser,
    DocxParser,
    HtmlParser,
    MinerUPdfParser,
    PlainTextParser,
    SpreadsheetParser,
)


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: dict[FileType, BaseParser] = {
            FileType.MARKDOWN: PlainTextParser(),
            FileType.TEXT: PlainTextParser(),
            FileType.HTML: HtmlParser(),
            FileType.DOCX: DocxParser(),
            FileType.PDF: MinerUPdfParser(),
            FileType.XLSX: SpreadsheetParser(),
            FileType.XLS: SpreadsheetParser(),
            FileType.CSV: SpreadsheetParser(),
        }

    def get_parser(self, file_type: FileType) -> BaseParser:
        return self._parsers[file_type]
