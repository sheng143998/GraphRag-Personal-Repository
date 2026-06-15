from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AdapterCallContext:
    trace_id: str
    run_id: str
    operation: str
    model_name: str
    prompt_name: str | None = None
    prompt_version: str | None = None
    strategy_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMAdapter:
    async def generate(self, *, prompt: str, context: AdapterCallContext) -> str:
        raise NotImplementedError


class EmbeddingAdapter:
    async def embed(self, *, texts: list[str], context: AdapterCallContext) -> list[list[float]]:
        raise NotImplementedError


class RerankAdapter:
    async def rerank(
        self,
        *,
        query: str,
        documents: list[str],
        context: AdapterCallContext,
    ) -> list[float]:
        raise NotImplementedError
