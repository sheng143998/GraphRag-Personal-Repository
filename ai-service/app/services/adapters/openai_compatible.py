from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.services.adapters.base import AdapterCallContext, EmbeddingAdapter, LLMAdapter, RerankAdapter


class OpenAICompatibleLLMAdapter(LLMAdapter):
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        temperature: float,
        max_tokens: int,
        max_retries: int,
    ) -> None:
        self.base_url = _normalize_base_url(base_url)
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max(0, max_retries)

    async def generate(self, *, prompt: str, context: AdapterCallContext) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是本地知识库 RAG 助手。只能基于提供的上下文回答，并尽量保留来源线索。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        data = await _post_json(
            base_url=self.base_url,
            endpoint="/chat/completions",
            api_key=self.api_key,
            payload=payload,
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
        )
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("LLM response has no choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, list):
            return "".join(str(item.get("text") or item.get("content") or "") for item in content)
        if not isinstance(content, str):
            raise RuntimeError("LLM response message content is not a string")
        return content


class OpenAICompatibleEmbeddingAdapter(EmbeddingAdapter):
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        dimensions: int,
        batch_size: int,
        max_retries: int,
    ) -> None:
        self.base_url = _normalize_base_url(base_url)
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.dimensions = dimensions
        self.batch_size = max(1, batch_size)
        self.max_retries = max(0, max_retries)

    async def embed(self, *, texts: list[str], context: AdapterCallContext) -> list[list[float]]:
        results: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            payload = {
                "model": self.model,
                "input": batch,
                "dimensions": self.dimensions,
            }
            data = await _post_json(
                base_url=self.base_url,
                endpoint="/embeddings",
                api_key=self.api_key,
                payload=payload,
                timeout_seconds=self.timeout_seconds,
                max_retries=self.max_retries,
            )
            embeddings = _extract_embeddings(data)
            for embedding in embeddings:
                if len(embedding) != self.dimensions:
                    raise RuntimeError(
                        f"Embedding dimension mismatch: expected {self.dimensions}, got {len(embedding)}"
                    )
            results.extend(embeddings)
        if len(results) != len(texts):
            raise RuntimeError(f"Embedding count mismatch: expected {len(texts)}, got {len(results)}")
        return results


class OpenAICompatibleRerankAdapter(RerankAdapter):
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        top_n: int,
        max_retries: int,
    ) -> None:
        self.base_url = _normalize_base_url(base_url)
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.top_n = top_n
        self.max_retries = max(0, max_retries)

    async def rerank(
        self,
        *,
        query: str,
        documents: list[str],
        context: AdapterCallContext,
    ) -> list[float]:
        if not documents:
            return []
        payload = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "top_n": min(max(1, self.top_n), len(documents)),
        }
        data = await _post_json(
            base_url=self.base_url,
            endpoint="/reranks",
            api_key=self.api_key,
            payload=payload,
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
        )
        return _extract_rerank_scores(data, document_count=len(documents))


def _normalize_base_url(base_url: str) -> str:
    if not base_url:
        raise RuntimeError("OpenAI-compatible adapter base_url is required")
    return base_url.rstrip("/")


async def _post_json(
    *,
    base_url: str,
    endpoint: str,
    api_key: str,
    payload: dict[str, Any],
    timeout_seconds: float,
    max_retries: int = 2,
) -> dict[str, Any]:
    if not api_key:
        raise RuntimeError("OpenAI-compatible adapter api_key is required")

    last_error: Exception | None = None
    attempts = max(1, max_retries + 1)
    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(
                    f"{base_url}{endpoint}",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
            if response.status_code in {429, 500, 502, 503, 504} and attempt < attempts - 1:
                await asyncio.sleep(0.3 * (2**attempt))
                continue
            if response.status_code >= 400:
                raise RuntimeError(f"Model provider HTTP {response.status_code}: {response.text[:1000]}")
            data = response.json()
            if not isinstance(data, dict):
                raise RuntimeError("Model provider response is not a JSON object")
            return data
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
            last_error = exc
            if attempt >= attempts - 1:
                break
            await asyncio.sleep(0.3 * (2**attempt))
    raise RuntimeError(f"Model provider request failed after {attempts} attempts: {last_error}")


def _extract_embeddings(data: dict[str, Any]) -> list[list[float]]:
    items = data.get("data")
    if not isinstance(items, list):
        raise RuntimeError("Embedding response missing data list")
    sorted_items = sorted(items, key=lambda item: item.get("index", 0) if isinstance(item, dict) else 0)
    embeddings: list[list[float]] = []
    for item in sorted_items:
        if not isinstance(item, dict):
            raise RuntimeError("Embedding item is not an object")
        embedding = item.get("embedding")
        if not isinstance(embedding, list):
            raise RuntimeError("Embedding item missing embedding list")
        embeddings.append([float(value) for value in embedding])
    return embeddings


def _extract_rerank_scores(data: dict[str, Any], *, document_count: int) -> list[float]:
    direct_scores = data.get("scores")
    if isinstance(direct_scores, list):
        scores = [float(value) for value in direct_scores]
        return _pad_scores(scores, document_count)

    results = data.get("results") or data.get("data") or data.get("output", {}).get("results")
    if not isinstance(results, list):
        raise RuntimeError("Rerank response missing results or scores")

    scores = [0.0] * document_count
    fallback_index = 0
    for item in results:
        if not isinstance(item, dict):
            continue
        index = item.get("index", fallback_index)
        score = item.get("relevance_score", item.get("score", item.get("rerank_score", 0.0)))
        if isinstance(index, int) and 0 <= index < document_count:
            scores[index] = float(score)
        fallback_index += 1
    return scores


def _pad_scores(scores: list[float], document_count: int) -> list[float]:
    if len(scores) >= document_count:
        return scores[:document_count]
    return scores + [0.0] * (document_count - len(scores))