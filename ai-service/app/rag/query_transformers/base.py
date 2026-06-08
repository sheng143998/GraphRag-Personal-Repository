from __future__ import annotations

import re

from app.services.adapters.base import AdapterCallContext, LLMAdapter


class QueryRewriter:
    def rewrite(self, query: str) -> str:
        raise NotImplementedError


class MultiQueryExpander:
    def expand(self, query: str, *, original_query: str | None = None, max_queries: int = 3) -> list[str]:
        raise NotImplementedError


class RuleBasedQueryRewriter(QueryRewriter):
    _synonyms: dict[str, tuple[str, ...]] = {
        "rag": ("retrieval augmented generation", "retrieval generation"),
        "llm": ("large language model",),
        "embedding": ("vector representation", "semantic embedding"),
        "vector": ("vector search", "pgvector"),
        "rerank": ("relevance ranking", "cross encoder ranking"),
        "hybrid": ("hybrid search", "vector search keyword search"),
        "chunk": ("text chunk", "document segment"),
        "parent-child": ("parent child chunking", "neighbor chunk context"),
        "metadata": ("metadata filter", "structured filter"),
        "fastapi": ("python ai service",),
        "spring": ("spring boot", "java backend"),
        "vue": ("frontend", "vue3"),
    }

    def rewrite(self, query: str) -> str:
        cleaned = _clean_query(query)
        if not cleaned:
            return query.strip()

        lowered = cleaned.lower()
        expansions: list[str] = []
        for term, synonyms in self._synonyms.items():
            if term in lowered:
                expansions.extend(item for item in synonyms if item.lower() not in lowered)

        if not expansions:
            return cleaned
        return f"{cleaned} {' '.join(dict.fromkeys(expansions))}"


class RuleBasedMultiQueryExpander(MultiQueryExpander):
    def expand(self, query: str, *, original_query: str | None = None, max_queries: int = 3) -> list[str]:
        variants: list[str] = []
        for candidate in [original_query, query, _technical_variant(query), _implementation_variant(query)]:
            normalized = _clean_query(candidate or "")
            if normalized and normalized not in variants:
                variants.append(normalized)
            if len(variants) >= max_queries:
                break
        return variants


class AdapterBackedQueryTransformer:
    def __init__(
        self,
        *,
        llm_adapter: LLMAdapter,
        fallback_rewriter: QueryRewriter,
        fallback_expander: MultiQueryExpander,
    ) -> None:
        self.llm_adapter = llm_adapter
        self.fallback_rewriter = fallback_rewriter
        self.fallback_expander = fallback_expander

    async def rewrite(
        self,
        query: str,
        *,
        context: AdapterCallContext,
    ) -> tuple[str, dict[str, object]]:
        fallback = self.fallback_rewriter.rewrite(query)
        try:
            output = await self.llm_adapter.generate(
                prompt=(
                    "Rewrite the user query for retrieval. "
                    "Return exactly one line in the format REWRITTEN_QUERY: <query>.\n"
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
                "provider": "rule-based-fallback",
                "fallback_used": True,
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
        fallback = self.fallback_expander.expand(query, original_query=original_query, max_queries=max_queries)
        try:
            output = await self.llm_adapter.generate(
                prompt=(
                    "Generate retrieval query variants. "
                    "Return one variant per line using QUERY: <variant>. "
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
                "provider": "rule-based-fallback",
                "fallback_used": True,
                "fallback_reason": str(exc),
                "query_count": len(fallback),
            }


def _clean_query(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip())


def _technical_variant(query: str) -> str:
    return f"{query} principles mechanism best practices"


def _implementation_variant(query: str) -> str:
    return f"{query} implementation configuration troubleshooting example"


def _extract_prefixed_line(output: str, prefix: str) -> str | None:
    prefix_with_colon = f"{prefix}:"
    for line in output.splitlines():
        stripped = _clean_query(line)
        if stripped.upper().startswith(prefix_with_colon):
            value = _clean_query(stripped[len(prefix_with_colon):])
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
