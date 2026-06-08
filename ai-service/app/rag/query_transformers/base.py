from __future__ import annotations

import re


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


def _clean_query(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip())


def _technical_variant(query: str) -> str:
    return f"{query} principles mechanism best practices"


def _implementation_variant(query: str) -> str:
    return f"{query} implementation configuration troubleshooting example"
