from __future__ import annotations

import re

from app.services.adapters.base import AdapterCallContext, LLMAdapter


class AdapterBackedQueryTransformer:
    def __init__(self, *, llm_adapter: LLMAdapter) -> None:
        self.llm_adapter = llm_adapter

    async def rewrite(
        self,
        query: str,
        *,
        context: AdapterCallContext,
    ) -> tuple[str, dict[str, object]]:
        fallback = _clean_query(query)
        try:
            output = await self.llm_adapter.generate(
                prompt=(
                    "Rewrite the user query into one fluent, natural, complete question for a RAG retriever. "
                    "Keep the original intent and make the query clearer, but do not append standalone "
                    "keywords, synonym lists, or unrelated expansion terms. Put semantic expansion terms "
                    "in the later multi-query variants, not in this rewritten query. If the user query is "
                    "Chinese, return a natural Chinese question and only keep acronyms in parentheses when useful. "
                    "Do not answer the question. Return exactly one line in this format: "
                    "REWRITTEN_QUERY: <query>.\n"
                    f"User query: {query}"
                ),
                context=context,
            )
            rewritten = _extract_prefixed_line(output, "REWRITTEN_QUERY")
            if not rewritten:
                raise ValueError("missing REWRITTEN_QUERY")
            return rewritten, {"provider": "llm", "fallback_used": False}
        except Exception as exc:
            return fallback, {
                "provider": "llm",
                "fallback_used": True,
                "fallback_strategy": "original_query",
                "fallback_reason": str(exc),
            }

    async def expand(
        self,
        query: str,
        *,
        original_query: str | None,
        max_queries: int,
        context: AdapterCallContext,
    ) -> tuple[list[str], dict[str, object]]:
        fallback = _fallback_queries(query, original_query=original_query, max_queries=max_queries)
        try:
            output = await self.llm_adapter.generate(
                prompt=(
                    "Generate retrieval query variants for a RAG retriever. Create variants "
                    "from different angles of the original question, and/or expand semantic "
                    "coverage with synonyms, related terms, broader concepts, abbreviations, "
                    "and domain terms. Keep every variant faithful to the original intent. "
                    "Each variant should still be a readable search query, not a loose keyword list. "
                    "Do not answer the question. Return one variant per line using "
                    "QUERY: <variant>. "
                    f"Return at most {max_queries} variants.\n"
                    f"Original query: {original_query or query}\n"
                    f"Rewritten query: {query}"
                ),
                context=context,
            )
            queries = _extract_query_lines(output, max_queries=max_queries)
            if not queries:
                raise ValueError("missing QUERY lines")
            return queries, {"provider": "llm", "fallback_used": False, "query_count": len(queries)}
        except Exception as exc:
            return fallback, {
                "provider": "llm",
                "fallback_used": True,
                "fallback_strategy": "original_queries",
                "fallback_reason": str(exc),
                "query_count": len(fallback),
            }


def _clean_query(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip())


def _fallback_queries(query: str, *, original_query: str | None, max_queries: int) -> list[str]:
    return _unique_non_empty([query, original_query], max_items=max_queries)


def _unique_non_empty(values: list[str | None], *, max_items: int) -> list[str]:
    items: list[str] = []
    for value in values:
        normalized = _clean_query(value or "")
        if normalized and normalized not in items:
            items.append(normalized)
        if len(items) >= max_items:
            break
    return items


def _extract_prefixed_line(output: str, prefix: str) -> str | None:
    prefixes = [f"{prefix}:", f"{prefix}："]
    for line in output.splitlines():
        stripped = _clean_query(line)
        stripped = stripped.lstrip("-* ")
        for prefix_value in prefixes:
            if stripped.upper().startswith(prefix_value):
                value = _clean_query(stripped[len(prefix_value):])
                return value or None
    return None


def _extract_query_lines(output: str, *, max_queries: int) -> list[str]:
    queries: list[str] = []
    for line in output.splitlines():
        value = _extract_prefixed_line(line, "QUERY")
        if value and value not in queries:
            queries.append(value)
        if len(queries) >= max_queries:
            break
    return queries
