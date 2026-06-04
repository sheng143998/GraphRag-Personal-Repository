import asyncio
import base64
import sys
sys.path.insert(0, r"C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service")

from app.services.ingest_service import IngestService
from app.schemas.ingest import DocumentIngestRequest, DocumentPayload
from app.core.constants import DocumentType, FileType

PDF_PATH = r"C:\Users\admin\Desktop\11\fuchuang1\jianli\27万本科Java~.pdf"

async def main():
    print("[1] Reading PDF and encoding as base64...")
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()
    pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
    print(f"    File size: {len(pdf_bytes)} bytes, base64: {len(pdf_b64)} chars")

    print("[2] Building ingest request...")
    payload = DocumentPayload(
        filename="27万本科Java~.pdf",
        file_type=FileType.PDF,
        content_base64=pdf_b64,
    )
    request = DocumentIngestRequest(
        knowledge_base_id="test-kb-fullchain",
        document_id="test-doc-fullchain-001",
        title="27万本科Java简历",
        document_type=DocumentType.TECH_NOTE,
        file=payload,
    )

    print("[3] Calling IngestService.ingest_document()...")
    service = IngestService()
    response = await service.ingest_document(request)

    print(f"\n[4] Result:")
    print(f"    document_id: {response.document_id}")
    print(f"    chunk_count: {response.chunk_count}")
    print(f"    parser_name: {response.parser_name}")
    print(f"    file_type:   {response.file_type}")
    print(f"    trace_id:    {response.trace.trace_id}")

    print(f"\n[5] Checking parsed content from repository...")
    from app.db.repositories import repository
    doc = repository.get_document("test-doc-fullchain-001")
    if doc:
        text = doc.get("normalized_text", "") if isinstance(doc, dict) else getattr(doc, "normalized_text", "")
        print(f"    Parsed text length: {len(text)} chars")
        print(f"\n--- Parsed Markdown (first 1000 chars) ---")
        print(text[:1000])
    else:
        print("    Document not found in repository (may be InMemory/not persisted)")

asyncio.run(main())
