from __future__ import annotations

from app.core.tracing import TraceBuilder
from app.db.repositories import repository
from app.rag.query_transformers.base import RuleBasedMultiQueryExpander, RuleBasedQueryRewriter
from app.rag.rerankers.base import BaseReranker
from app.rag.retrievers.base import BaseRetriever
from app.schemas.common import SourceMetadata
from app.services.adapters.base import AdapterCallContext, EmbeddingAdapter
from app.services.adapters.registry import get_embedding_model_name, get_rerank_model_name


class AdvancedRagStrategy:
    supported_strategy_names = {"hybrid-rerank", "metadata-filter", "parent-child", "advanced-rag"}

    def __init__(
        self,
        *,
        retriever: BaseRetriever,
        reranker: BaseReranker,
        embedding_adapter: EmbeddingAdapter,
    ) -> None:
        self.retriever = retriever
        self.reranker = reranker
        self.embedding_adapter = embedding_adapter
        self.query_rewriter = RuleBasedQueryRewriter()
        self.multi_query_expander = RuleBasedMultiQueryExpander()

    async def run(
        self,
        *,
        query: str,
        top_k: int,
        trace_builder: TraceBuilder,
        filters: dict[str, object],
        knowledge_base_id: str | None = None,
        query_embedding: list[float] | None = None,
        embedding_model: str | None = None,
    ) -> list[SourceMetadata]:
        strategy_name = trace_builder.trace.strategy_name
        use_rewrite = strategy_name == "advanced-rag"
        use_multi_query = strategy_name == "advanced-rag"
        use_parent_child = strategy_name in {"parent-child", "advanced-rag"}
        active_filters = filters if strategy_name in {"metadata-filter", "advanced-rag"} else {}

        rewritten_query = self.query_rewriter.rewrite(query) if use_rewrite else query
        trace_builder.set_attribute("rewritten_query", rewritten_query)
        trace_builder.add_step(
            name="query_rewrite",
            status="completed" if use_rewrite else "skipped",
            detail="Rule-based query rewrite completed." if use_rewrite else "Query rewrite is not enabled for this strategy.",
            payload={"original_query": query, "rewritten_query": rewritten_query},
        )

        retrieve_queries = (
            self.multi_query_expander.expand(rewritten_query, original_query=query, max_queries=3)
            if use_multi_query
            else [rewritten_query]
        )
        if use_rewrite and rewritten_query in retrieve_queries:
            retrieve_queries = [rewritten_query] + [item for item in retrieve_queries if item != rewritten_query]
        trace_builder.add_step(
            name="multi_query_expand",
            status="completed" if use_multi_query else "skipped",
            detail="Generated query variants." if use_multi_query else "Multi-query expansion is not enabled for this strategy.",
            payload={"query_count": len(retrieve_queries), "queries": retrieve_queries},
        )

        per_query_limit = max(top_k * 2, top_k)
        retrieved: list[SourceMetadata] = []
        for retrieve_query in retrieve_queries:
            embedding = query_embedding if retrieve_query == query else None
            if embedding is None:
                embeddings = await self.embedding_adapter.embed(
                    texts=[retrieve_query],
                    context=AdapterCallContext(
                        trace_id=trace_builder.trace.trace_id,
                        run_id=trace_builder.trace.run_id,
                        operation="embed_retrieval_query",
                        model_name=embedding_model or get_embedding_model_name(),
                        strategy_name=strategy_name,
                    ),
                )
                embedding = embeddings[0]

            sources = await self.retriever.retrieve(
                query=retrieve_query,
                chunks=repository.list_chunks(knowledge_base_id),
                top_k=per_query_limit,
                filters=active_filters,
                knowledge_base_id=knowledge_base_id,
                query_embedding=embedding,
                embedding_model=embedding_model,
            )
            retrieved.extend(_with_matched_query(sources, retrieve_query))

        trace_builder.add_step(
            name="retrieve",
            status="completed",
            detail="Retrieved candidate chunks.",
            payload={
                "query_count": len(retrieve_queries),
                "result_count": len(retrieved),
                "metadata_filter_enabled": bool(active_filters),
            },
        )

        fused = _fuse_by_chunk_id(retrieved)[:per_query_limit]
        trace_builder.add_step(
            name="fusion",
            status="completed" if use_multi_query else "skipped",
            detail="Fused multi-query retrieval results." if use_multi_query else "Single-query retrieval does not need fusion.",
            payload={"input_count": len(retrieved), "result_count": len(fused), "fusion_method": "chunk_id_max_score"},
        )

        contextualized = repository.hydrate_parent_context(fused) if use_parent_child else fused
        trace_builder.add_step(
            name="parent_child_context",
            status="completed" if use_parent_child else "skipped",
            detail=(
                "Hydrated parent or neighbor chunk context."
                if use_parent_child
                else "Parent-child context is not enabled for this strategy."
            ),
            payload={"result_count": len(contextualized)},
        )

        reranked = await self.reranker.rerank(
            query=rewritten_query,
            sources=contextualized,
            context=AdapterCallContext(
                trace_id=trace_builder.trace.trace_id,
                run_id=trace_builder.trace.run_id,
                operation="rerank",
                model_name=get_rerank_model_name(),
                strategy_name=strategy_name,
            ),
        )
        trace_builder.add_step(
            name="rerank",
            status="completed",
            detail="Reranked retrieved chunks.",
            model_name=get_rerank_model_name(),
            payload={"result_count": len(reranked)},
        )
        return reranked[:top_k]


def _with_matched_query(sources: list[SourceMetadata], query: str) -> list[SourceMetadata]:
    updated: list[SourceMetadata] = []
    for source in sources:
        metadata = {**source.metadata}
        matched_queries = list(metadata.get("matched_queries") or [])
        if query not in matched_queries:
            matched_queries.append(query)
        metadata["matched_queries"] = matched_queries
        updated.append(source.copy(update={"metadata": metadata}))
    return updated


def _fuse_by_chunk_id(sources: list[SourceMetadata]) -> list[SourceMetadata]:
    fused: dict[str, SourceMetadata] = {}
    for source in sources:
        existing = fused.get(source.chunk_id)
        matched_queries = list(source.metadata.get("matched_queries") or [])
        if existing is not None:
            for query in existing.metadata.get("matched_queries") or []:
                if query not in matched_queries:
                    matched_queries.append(query)
        if existing is None or (source.score or 0.0) > (existing.score or 0.0):
            fused[source.chunk_id] = source
            existing = source
        metadata = {**existing.metadata}
        metadata["matched_queries"] = matched_queries
        metadata["fusion_method"] = "chunk_id_max_score"
        fused[source.chunk_id] = existing.copy(update={"metadata": metadata})
    return sorted(fused.values(), key=lambda item: item.score or 0.0, reverse=True)
