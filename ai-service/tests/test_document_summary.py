from __future__ import annotations

import os

os.environ["AI_RAG_USE_DATABASE"] = "false"

from app.core.constants import DocumentType, FileType  # noqa: E402
from app.db.repositories import BaseDocumentRepository  # noqa: E402
from app.schemas.ingest import DocumentIngestRequest, DocumentPayload, ParsedDocument  # noqa: E402


class _DummyRepo(BaseDocumentRepository):
    def __init__(self) -> None:
        self.saved_summary: str | None = None

    def save_document(self, parsed_document: ParsedDocument, *, request=None, preserve_summary: bool = False) -> None:
        self.saved_summary = request.summary if preserve_summary else parsed_document.normalized_text[:1000]

    def save_chunks(self, document_id: str, knowledge_base_id: str, chunks: list):  # pragma: no cover
        raise NotImplementedError

    def save_embeddings(self, *, chunks: list, embeddings: list, embedding_model: str):  # pragma: no cover
        raise NotImplementedError

    def get_chunks(self, document_id: str):  # pragma: no cover
        raise NotImplementedError

    def list_chunks(self, knowledge_base_id: str | None = None):  # pragma: no cover
        raise NotImplementedError

    def delete_document_chunks(self, document_id: str) -> None:  # pragma: no cover
        raise NotImplementedError

    def save_graph_facts(self, **kwargs):  # pragma: no cover
        raise NotImplementedError


def test_preserve_summary_uses_document_ingest_request_summary() -> None:
    repo = _DummyRepo()
    request = DocumentIngestRequest(
        knowledge_base_id="kb-1",
        document_id="doc-1",
        title="Demo",
        document_type=DocumentType.TECH_NOTE,
        summary="file.pdf | uploaded at: 2026-06-10 12:00:00",
        file=DocumentPayload(filename="file.pdf", file_type=FileType.PDF),
    )
    parsed = ParsedDocument(
        document_id="doc-1",
        title="Demo",
        normalized_text="parsed text" * 500,
        parser_name="mineru",
        parser_version="v1",
        metadata={},
    )

    repo.save_document(parsed, request=request, preserve_summary=True)

    assert repo.saved_summary == "file.pdf | uploaded at: 2026-06-10 12:00:00"
