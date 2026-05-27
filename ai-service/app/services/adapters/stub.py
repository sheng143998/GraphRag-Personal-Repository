from __future__ import annotations

import hashlib
import math

from app.services.adapters.base import (
    AdapterCallContext,
    EmbeddingAdapter,
    LLMAdapter,
    RerankAdapter,
)


class StubLLMAdapter(LLMAdapter):
    async def generate(self, *, prompt: str, context: AdapterCallContext) -> str:
        return (
            f"[stub-answer] model={context.model_name} strategy={context.strategy_name} "
            f"prompt={context.prompt_name}:{context.prompt_version}\n{prompt[:400]}"
        )


class StubEmbeddingAdapter(EmbeddingAdapter):
    async def embed(self, *, texts: list[str], context: AdapterCallContext) -> list[list[float]]:
        return [_hash_embedding(text) for text in texts]


class StubRerankAdapter(RerankAdapter):
    async def rerank(
        self,
        *,
        query: str,
        documents: list[str],
        context: AdapterCallContext,
    ) -> list[float]:
        query_terms = set(query.lower().split())
        scores: list[float] = []
        for document in documents:
            overlap = len(query_terms.intersection(document.lower().split()))
            scores.append(float(overlap))
        return scores


def _hash_embedding(text: str, dimensions: int = 1536) -> list[float]:
    vector = [0.0] * dimensions
    tokens = _tokens(text)
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [round(value / norm, 6) for value in vector]


def _tokens(text: str) -> list[str]:
    lowered = text.lower()
    words = [item for item in lowered.split() if item]
    chars = [char for char in lowered if not char.isspace()]
    bigrams = [lowered[index : index + 2] for index in range(max(0, len(lowered) - 1))]
    return words + chars + bigrams
