from __future__ import annotations

import asyncio
import os

os.environ["AI_RAG_USE_DATABASE"] = "false"
os.environ["MODEL_PROVIDER"] = "stub"
os.environ["LLM_PROVIDER"] = "stub"
os.environ["EMBEDDING_PROVIDER"] = "stub"
os.environ["RERANK_PROVIDER"] = "stub"

from app.schemas.common import SourceMetadata  # noqa: E402
from app.schemas.rag import RagQueryRequest, RagRequestContext  # noqa: E402
from app.services.rag_service import RagService  # noqa: E402
from app.services.adapters.base import LLMAdapter, AdapterCallContext  # noqa: E402


class _CaptureLLMAdapter(LLMAdapter):
    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def generate(self, *, prompt: str, context: AdapterCallContext) -> str:
        self.prompts.append(prompt)
        return "ok"


class _FakeRetriever:
    async def retrieve(self, *args, **kwargs):  # pragma: no cover
        return []


def test_rag_prompt_uses_query_and_context_str_template() -> None:
    adapter = _CaptureLLMAdapter()
    service = RagService()
    service.generator = type("Gen", (), {"generate": adapter.generate})()
    service.advanced_strategy = service.basic_strategy

    async def _run():
        service.retriever = _FakeRetriever()
        service.basic_strategy.run = _fake_strategy_run
        return await service.query(
            RagQueryRequest(
                question="What is REQUIRES_NEW?",
                top_k=2,
                strategy_name="basic-rag",
                context=RagRequestContext(knowledge_base_id="kb-1"),
            )
        )

    asyncio.run(_run())

    assert adapter.prompts
    prompt = adapter.prompts[0]
    assert "## 检索上下文：" in prompt
    assert "## 用户问题：" in prompt
    assert "What is REQUIRES_NEW?" in prompt


async def _fake_strategy_run(*args, **kwargs):
    return [
        SourceMetadata(
            document_id="doc-1",
            chunk_id="chunk-1",
            title="Spring Tx Notes",
            source_path="/docs/spring.md",
            metadata={"content_preview": "REQUIRES_NEW suspends the current transaction."},
        )
    ]
