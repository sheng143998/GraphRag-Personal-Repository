from __future__ import annotations

from time import perf_counter

from app.core.tracing import TraceBuilder
from app.db.repositories import repository
from app.rag.graph import RuleBasedGraphExtractor
from app.rag.query_transformers.base import AdapterBackedQueryTransformer
from app.rag.rerankers.base import BaseReranker
from app.rag.retrievers.base import BaseRetriever
from app.rag.strategies.presets import PRESETS, resolve_rag_preset
from app.schemas.common import SourceMetadata
from app.services.adapters.base import AdapterCallContext, EmbeddingAdapter, LLMAdapter
from app.services.adapters.registry import get_embedding_model_name, get_llm_model_name, get_rerank_model_name


class AdvancedRagStrategy:
    supported_strategy_names = set(PRESETS.keys())

    def __init__(
        self,
        *,
        retriever: BaseRetriever,
        reranker: BaseReranker,
        embedding_adapter: EmbeddingAdapter,
        llm_adapter: LLMAdapter,
    ) -> None:
        self.retriever = retriever
        self.reranker = reranker
        self.embedding_adapter = embedding_adapter
        self.adapter_query_transformer = AdapterBackedQueryTransformer(llm_adapter=llm_adapter)
        self.graph_extractor = RuleBasedGraphExtractor()

    async def run(
        self,
        *,
        query: str,
        top_k: int,
        trace_builder: TraceBuilder,
        filters: dict[str, object],
        retrieval_options: dict[str, object] | None = None,
        knowledge_base_id: str | None = None,
        query_embedding: list[float] | None = None,
        embedding_model: str | None = None,
    ) -> list[SourceMetadata]:
        strategy_name = trace_builder.trace.strategy_name
        preset = resolve_rag_preset(strategy_name)
        use_rewrite = preset.query_rewrite
        use_multi_query = preset.multi_query
        use_graph = preset.graph_expand
        active_filters = filters if preset.metadata_filter else {}
        active_retrieval_options = retrieval_options or {}
        use_parent_child = preset.parent_child and _parent_child_context_enabled(active_retrieval_options)
        trace_builder.set_attribute(
            "rag_preset",
            {
                "query_rewrite": preset.query_rewrite,
                "multi_query": preset.multi_query,
                "metadata_filter": preset.metadata_filter,
                "parent_child": preset.parent_child,
                "rerank": preset.rerank,
                "graph_expand": preset.graph_expand,
            },
        )
        if active_retrieval_options:
            trace_builder.set_attribute("retrieval_options", active_retrieval_options)
            trace_builder.set_attribute(
                "enable_parent_child_context",
                use_parent_child,
            )

        rewrite_payload: dict[str, object] = {"original_query": query}
        if use_rewrite:
            rewrite_context = AdapterCallContext(
                trace_id=trace_builder.trace.trace_id,
                run_id=trace_builder.trace.run_id,
                operation="rewrite_query",
                model_name=get_llm_model_name(),
                strategy_name=strategy_name,
            )
            rewrite_started_at = perf_counter()
            rewritten_query, rewrite_metadata = await self.adapter_query_transformer.rewrite(
                query,
                context=rewrite_context,
            )
            rewrite_payload.update(rewrite_metadata)
            rewrite_call_metadata = trace_builder.record_adapter_metadata(rewrite_context.metadata)
            rewrite_payload["latency_ms"] = rewrite_call_metadata.get("latency_ms") or round(
                (perf_counter() - rewrite_started_at) * 1000,
                3,
            )
        else:
            rewritten_query = query
            rewrite_payload["provider"] = "none"
        trace_builder.set_attribute("rewritten_query", rewritten_query)
        trace_builder.add_step(
            name="query_rewrite",
            status="completed" if use_rewrite else "skipped",
            detail="Query rewrite completed." if use_rewrite else "Query rewrite is not enabled for this strategy.",
            model_name=get_llm_model_name() if use_rewrite else None,
            payload={**rewrite_payload, "rewritten_query": rewritten_query},
        )

        graph_entities = self.graph_extractor.extract_entities(rewritten_query) if use_graph else []
        graph_relationships = self.graph_extractor.extract_relationships(graph_entities) if use_graph else []
        graph_query = self.graph_extractor.augment_query(rewritten_query, graph_entities) if use_graph else rewritten_query
        persisted_graph_facts = (
            repository.find_graph_facts(
                knowledge_base_id=knowledge_base_id,
                entity_names=[entity.name for entity in graph_entities],
            )
            if use_graph
            else {"matched_entities": [], "relationship_count": 0, "relationships": [], "expansion_terms": []}
        )
        graph_query = (
            _append_graph_expansion_terms(graph_query, persisted_graph_facts.get("expansion_terms", []))
            if use_graph
            else graph_query
        )
        if use_graph:
            trace_builder.set_attribute("graph_entities", [entity.__dict__ for entity in graph_entities])
            trace_builder.set_attribute("graph_relationships", [relationship.__dict__ for relationship in graph_relationships])
            trace_builder.set_attribute("graph_augmented_query", graph_query)
            trace_builder.set_attribute("persisted_graph_matches", persisted_graph_facts)
            trace_builder.set_attribute("graph_expansion_terms", persisted_graph_facts.get("expansion_terms", []))
            trace_builder.set_attribute("graph_traversal_relationships", persisted_graph_facts.get("relationships", []))
        trace_builder.add_step(
            name="graph_extract",
            status="completed" if use_graph else "skipped",
            detail="Extracted query entities and relationships." if use_graph else "Graph extraction is not enabled.",
            payload={
                "entity_count": len(graph_entities),
                "relationship_count": len(graph_relationships),
                "graph_augmented_query": graph_query,
                "persisted_match_count": len(persisted_graph_facts.get("matched_entities", [])),
                "persisted_relationship_count": persisted_graph_facts.get("relationship_count", 0),
                "graph_expansion_terms": persisted_graph_facts.get("expansion_terms", []),
            },
        )

        expand_payload: dict[str, object] = {}
        if use_multi_query:
            expand_context = AdapterCallContext(
                trace_id=trace_builder.trace.trace_id,
                run_id=trace_builder.trace.run_id,
                operation="expand_retrieval_queries",
                model_name=get_llm_model_name(),
                strategy_name=strategy_name,
            )
            expand_started_at = perf_counter()
            retrieve_queries, expand_payload = await self.adapter_query_transformer.expand(
                rewritten_query,
                original_query=query,
                max_queries=3,
                context=expand_context,
            )
            expand_call_metadata = trace_builder.record_adapter_metadata(expand_context.metadata)
            expand_payload["latency_ms"] = expand_call_metadata.get("latency_ms") or round(
                (perf_counter() - expand_started_at) * 1000,
                3,
            )
        else:
            retrieve_queries = [graph_query]
            expand_payload["provider"] = "none"
        if use_rewrite and rewritten_query in retrieve_queries:
            retrieve_queries = [rewritten_query] + [item for item in retrieve_queries if item != rewritten_query]
        trace_builder.add_step(
            name="multi_query_expand",
            status="completed" if use_multi_query else "skipped",
            detail="Generated query variants." if use_multi_query else "Multi-query expansion is not enabled for this strategy.",
            model_name=get_llm_model_name() if use_multi_query else None,
            payload={**expand_payload, "query_count": len(retrieve_queries), "queries": retrieve_queries},
        )

        per_query_limit = max(top_k * 2, top_k)
        retrieved: list[SourceMetadata] = []
        retrieve_latency_ms = 0.0
        embedding_latency_ms = 0.0
        for retrieve_query in retrieve_queries:
            embedding = query_embedding if retrieve_query == query else None
            if embedding is None:
                embedding_context = AdapterCallContext(
                    trace_id=trace_builder.trace.trace_id,
                    run_id=trace_builder.trace.run_id,
                    operation="embed_retrieval_query",
                    model_name=embedding_model or get_embedding_model_name(),
                    strategy_name=strategy_name,
                )
                embedding_started_at = perf_counter()
                embeddings = await self.embedding_adapter.embed(
                    texts=[retrieve_query],
                    context=embedding_context,
                )
                embedding_call_metadata = trace_builder.record_adapter_metadata(embedding_context.metadata)
                embedding_latency_ms += float(
                    embedding_call_metadata.get("latency_ms")
                    or round((perf_counter() - embedding_started_at) * 1000, 3)
                )
                embedding = embeddings[0]

            retrieve_started_at = perf_counter()
            sources = await self.retriever.retrieve(
                query=retrieve_query,
                chunks=repository.list_chunks(knowledge_base_id),
                top_k=per_query_limit,
                filters=active_filters,
                retrieval_options=active_retrieval_options,
                knowledge_base_id=knowledge_base_id,
                query_embedding=embedding,
                embedding_model=embedding_model,
            )
            retrieve_latency_ms += round((perf_counter() - retrieve_started_at) * 1000, 3)
            retrieved.extend(_with_graph_metadata(
                _with_matched_query(sources, retrieve_query),
                entity_names=[entity.name for entity in graph_entities],
                relationship_count=len(graph_relationships),
                persisted_graph_facts=persisted_graph_facts,
            ))

        trace_builder.add_step(
            name="retrieve",
            status="completed",
            detail="Retrieved candidate chunks.",
            payload={
                "query_count": len(retrieve_queries),
                "result_count": len(retrieved),
                "metadata_filter_enabled": bool(active_filters),
                "retrieval_options_enabled": bool(active_retrieval_options),
                "latency_ms": round(retrieve_latency_ms, 3),
                "embedding_latency_ms": round(embedding_latency_ms, 3),
            },
        )

        fused = (
            _fuse_by_parent_group(retrieved)
            if use_parent_child
            else _fuse_by_chunk_id(retrieved)
        )[:per_query_limit]
        trace_builder.add_step(
            name="fusion",
            status="completed" if use_multi_query or use_parent_child else "skipped",
            detail=(
                "Fused retrieval results by parent group."
                if use_parent_child
                else "Fused multi-query retrieval results."
                if use_multi_query
                else "Single-query retrieval does not need fusion."
            ),
            payload={
                "input_count": len(retrieved),
                "result_count": len(fused),
                "fusion_method": "parent_group_score" if use_parent_child else "chunk_id_max_score",
            },
        )

        contextualized = repository.hydrate_parent_context(fused) if use_parent_child else fused
        compression_stats = _context_compression_stats(contextualized)
        trace_builder.add_step(
            name="parent_child_context",
            status="completed" if use_parent_child else "skipped",
            detail=(
                "Hydrated parent or neighbor chunk context."
                if use_parent_child
                else "Parent-child context is not enabled for this strategy."
            ),
            payload={"result_count": len(contextualized), **compression_stats},
        )

        if preset.rerank:
            rerank_context = AdapterCallContext(
                trace_id=trace_builder.trace.trace_id,
                run_id=trace_builder.trace.run_id,
                operation="rerank",
                model_name=get_rerank_model_name(),
                strategy_name=strategy_name,
            )
            rerank_started_at = perf_counter()
            reranked = await self.reranker.rerank(
                query=rewritten_query,
                sources=contextualized,
                context=rerank_context,
            )
            rerank_call_metadata = trace_builder.record_adapter_metadata(rerank_context.metadata)
            rerank_latency_ms = rerank_call_metadata.get("latency_ms") or round(
                (perf_counter() - rerank_started_at) * 1000,
                3,
            )
        else:
            reranked = contextualized
            rerank_latency_ms = None
        trace_builder.add_step(
            name="rerank",
            status="completed" if preset.rerank else "skipped",
            detail="Reranked retrieved chunks." if preset.rerank else "Rerank is disabled for this preset.",
            model_name=get_rerank_model_name() if preset.rerank else None,
            payload={"result_count": len(reranked), "latency_ms": rerank_latency_ms},
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


def _with_graph_metadata(
    sources: list[SourceMetadata],
    *,
    entity_names: list[str],
    relationship_count: int,
    persisted_graph_facts: dict[str, object],
) -> list[SourceMetadata]:
    if not entity_names:
        return sources
    updated: list[SourceMetadata] = []
    for source in sources:
        content_preview = str(source.metadata.get("content_preview", ""))
        matched_entities = [
            entity_name
            for entity_name in entity_names
            if entity_name.lower() in content_preview.lower() or entity_name.lower() in source.title.lower()
        ]
        metadata = {
            **source.metadata,
            "graph_entities": entity_names,
            "graph_matched_entities": matched_entities,
            "graph_relationship_count": relationship_count,
            "persisted_graph_matched_entities": persisted_graph_facts.get("matched_entities", []),
            "persisted_graph_relationship_count": persisted_graph_facts.get("relationship_count", 0),
            "graph_expansion_terms": persisted_graph_facts.get("expansion_terms", []),
            "graph_traversal_relationships": persisted_graph_facts.get("relationships", []),
        }
        updated.append(source.copy(update={"metadata": metadata}))
    return updated


def _append_graph_expansion_terms(query: str, expansion_terms: object) -> str:
    if not isinstance(expansion_terms, list):
        return query
    terms: list[str] = []
    query_lower = query.lower()
    for value in expansion_terms:
        term = str(value).strip()
        if not term or term.lower() in query_lower or term in terms:
            continue
        terms.append(term)
        if len(terms) >= 5:
            break
    if not terms:
        return query
    return f"{query} {' '.join(terms)}"


def _context_compression_stats(sources: list[SourceMetadata]) -> dict[str, object]:
    compressed_sources = [
        source
        for source in sources
        if source.metadata.get("context_compression_mode") == "query-aware-sentence-pack"
    ]
    original_chars = sum(int(source.metadata.get("context_original_chars") or 0) for source in compressed_sources)
    compressed_chars = sum(int(source.metadata.get("context_compressed_chars") or 0) for source in compressed_sources)
    return {
        "context_compression_enabled": bool(compressed_sources),
        "compressed_result_count": len(compressed_sources),
        "context_original_chars": original_chars,
        "context_compressed_chars": compressed_chars,
    }


def _parent_child_context_enabled(retrieval_options: dict[str, object]) -> bool:
    value = retrieval_options.get(
        "enable_parent_child_context",
        retrieval_options.get("enableParentChildContext", True),
    )
    return _bool_option(value, default=True)


def _bool_option(value: object, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
    return default

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


def _fuse_by_parent_group(sources: list[SourceMetadata]) -> list[SourceMetadata]:
    grouped: dict[str, list[SourceMetadata]] = {}
    for source in sources:
        parent_chunk_id = source.metadata.get("parent_chunk_id")
        group_key = str(parent_chunk_id or source.chunk_id)
        grouped.setdefault(group_key, []).append(source)

    fused: list[SourceMetadata] = []
    for group_key, group_sources in grouped.items():
        best = max(group_sources, key=lambda item: item.score or 0.0)
        matched_queries: list[str] = []
        child_ids: list[str] = []
        for source in group_sources:
            if source.chunk_id not in child_ids:
                child_ids.append(source.chunk_id)
            for query in source.metadata.get("matched_queries") or []:
                if query not in matched_queries:
                    matched_queries.append(str(query))

        max_score = best.score or 0.0
        aggregate_bonus = 0.05 * max(0, len(child_ids) - 1)
        metadata = {
            **best.metadata,
            "matched_queries": matched_queries,
            "fusion_method": "parent_group_score",
            "parent_group_id": group_key,
            "parent_child_matched_child_count": len(child_ids),
            "parent_child_matched_child_chunk_ids": child_ids,
            "parent_child_aggregate_bonus": round(aggregate_bonus, 6),
        }
        fused.append(best.copy(update={"score": round(max_score + aggregate_bonus, 6), "metadata": metadata}))

    return sorted(fused, key=lambda item: item.score or 0.0, reverse=True)
