from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RagStrategyPreset:
    query_rewrite: bool = False
    multi_query: bool = False
    metadata_filter: bool = False
    parent_child: bool = False
    rerank: bool = True
    graph_expand: bool = False


PRESETS: dict[str, RagStrategyPreset] = {
    "hybrid-rerank": RagStrategyPreset(rerank=True),
    "metadata-filter": RagStrategyPreset(metadata_filter=True, rerank=True),
    "parent-child": RagStrategyPreset(parent_child=True, rerank=True),
    "advanced-rag": RagStrategyPreset(
        query_rewrite=True,
        multi_query=True,
        metadata_filter=True,
        parent_child=True,
        rerank=True,
    ),
    "graph-rag": RagStrategyPreset(
        query_rewrite=True,
        multi_query=True,
        metadata_filter=True,
        parent_child=True,
        rerank=True,
        graph_expand=True,
    ),
}


def resolve_rag_preset(strategy_name: str) -> RagStrategyPreset:
    try:
        return PRESETS[strategy_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported Advanced RAG preset: {strategy_name}") from exc
