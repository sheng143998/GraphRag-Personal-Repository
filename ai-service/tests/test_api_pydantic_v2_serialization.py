import asyncio
import os

os.environ["AI_RAG_USE_DATABASE"] = "false"
os.environ["MODEL_PROVIDER"] = "stub"
os.environ["LLM_PROVIDER"] = "stub"
os.environ["EMBEDDING_PROVIDER"] = "stub"
os.environ["RERANK_PROVIDER"] = "stub"
os.environ["AI_AGENT_SUPPORT_WORKFLOW_RUNTIME"] = "local"

import httpx

from app.main import app


def test_health_response_serializes_with_fastapi_pydantic_v2() -> None:
    response = asyncio.run(_get("/ai/health", headers={"X-Trace-Id": "trace-http-health"}))

    assert response.status_code == 200
    assert response.headers["X-Trace-Id"] == "trace-http-health"
    assert response.json() == {"status": "ok", "service": "ai-service"}


def test_rag_evaluate_response_serializes_nested_trace_payload() -> None:
    response = asyncio.run(
        _post(
            "/ai/rag/evaluate",
            headers={"X-Trace-Id": "trace-http-rag-evaluate"},
            json={
                "question": "如何评估 RAG 回答是否有依据？",
                "expected_answer": "需要检查答案是否被检索证据支撑。",
                "generated_answer": "答案需要引用检索证据，并对齐标准答案。",
                "citations": [
                    {
                        "document_id": "doc-1",
                        "chunk_id": "chunk-1",
                        "title": "RAG 评估说明",
                        "score": 0.92,
                        "metadata": {"content_preview": "答案需要引用检索证据。"},
                    }
                ],
                "strategy_name": "advanced-rag",
                "context": {"knowledge_base_id": "kb-http-evaluate"},
            },
        )
    )

    body = response.json()

    assert response.status_code == 200
    assert response.headers["X-Trace-Id"] == "trace-http-rag-evaluate"
    assert body["result"]["grounded_score"] >= 0
    assert body["trace"]["trace_id"] == "trace-http-rag-evaluate"
    assert body["trace"]["steps"][0]["payload"]["grounded_score"] >= 0
    assert "T" in body["trace"]["started_at"]


async def _get(path: str, *, headers: dict[str, str]) -> httpx.Response:
    async with _client() as client:
        return await client.get(path, headers=headers)


async def _post(path: str, *, headers: dict[str, str], json: dict[str, object]) -> httpx.Response:
    async with _client() as client:
        return await client.post(path, headers=headers, json=json)


def _client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")
