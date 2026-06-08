from __future__ import annotations

from app.core.tracing import TraceBuilder
from app.db.repositories import repository
from app.rag.graph import RuleBasedGraphExtractor
from app.rag.query_transformers.base import AdapterBackedQueryTransformer, RuleBasedMultiQueryExpander, RuleBasedQueryRewriter
from app.rag.rerankers.base import BaseReranker
from app.rag.retrievers.base import BaseRetriever
from app.schemas.common import SourceMetadata
from app.services.adapters.base import AdapterCallContext, EmbeddingAdapter, LLMAdapter
from app.services.adapters.registry import get_embedding_model_name, get_llm_model_name, get_rerank_model_name


class AdvancedRagStrategy:
    supported_strategy_names = {"hybrid-rerank", "metadata-filter", "parent-child", "advanced-rag", "graph-rag"}

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
        self.query_rewriter = RuleBasedQueryRewriter()
        self.multi_query_expander = RuleBasedMultiQueryExpander()
        self.adapter_query_transformer = AdapterBackedQueryTransformer(
            llm_adapter=llm_adapter,
            fallback_rewriter=self.query_rewriter,
            fallback_expander=self.multi_query_expander,
        )
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
        use_rewrite = strategy_name == "advanced-rag"
        use_multi_query = strategy_name == "advanced-rag"
        use_parent_child = strategy_name in {"parent-child", "advanced-rag", "graph-rag"}
        use_graph = strategy_name == "graph-rag"
        active_filters = filters if strategy_name in {"metadata-filter", "advanced-rag", "graph-rag"} else {}
        active_retrieval_options = retrieval_options or {}
        use_llm_query_transform = _bool_option(
            active_retrieval_options,
            "enable_llm_query_transform",
            "enableLlmQueryTransform",
        )
        if active_retrieval_options:
            trace_builder.set_attribute("retrieval_options", active_retrieval_options)

        rewrite_payload: dict[str, object] = {"original_query": query}
        if use_rewrite and use_llm_query_transform:
            rewritten_query, rewrite_metadata = await self.adapter_query_transformer.rewrite(
                query,
                context=AdapterCallContext(
                    trace_id=trace_builder.trace.trace_id,
                    run_id=trace_builder.trace.run_id,
                    operation="rewrite_query",
                    model_name=get_llm_model_name(),
                    strategy_name=strategy_name,
                ),
            )
            rewrite_payload.update(rewrite_metadata)
        else:
            rewritten_query = self.query_rewriter.rewrite(query) if use_rewrite else query
            rewrite_payload["provider"] = "rule-based" if use_rewrite else "none"
        trace_builder.set_attribute("rewritten_query", rewritten_query)
        trace_builder.add_step(
            name="query_rewrite",
            status="completed" if use_rewrite else "skipped",
            detail="Query rewrite completed." if use_rewrite else "Query rewrite is not enabled for this strategy.",
            model_name=get_llm_model_name() if use_rewrite and use_llm_query_transform else None,
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
        if use_multi_query and use_llm_query_transform:
            retrieve_queries, expand_payload = await self.adapter_query_transformer.expand(
                rewritten_query,
                original_query=query,
                max_queries=3,
                context=AdapterCallContext(
                    trace_id=trace_builder.trace.trace_id,
                    run_id=trace_builder.trace.run_id,
                    operation="expand_retrieval_queries",
                    model_name=get_llm_model_name(),
                    strategy_name=strategy_name,
                ),
            )
        else:
            retrieve_queries = (
                self.multi_query_expander.expand(rewritten_query, original_query=query, max_queries=3)
                if use_multi_query
                else [graph_query]
            )
            expand_payload["provider"] = "rule-based" if use_multi_query else "none"
        if use_rewrite and rewritten_query in retrieve_queries:
            retrieve_queries = [rewritten_query] + [item for item in retrieve_queries if item != rewritten_query]
        trace_builder.add_step(
            name="multi_query_expand",
            status="completed" if use_multi_query else "skipped",
            detail="Generated query variants." if use_multi_query else "Multi-query expansion is not enabled for this strategy.",
            model_name=get_llm_model_name() if use_multi_query and use_llm_query_transform else None,
            payload={**expand_payload, "query_count": len(retrieve_queries), "queries": retrieve_queries},
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
                retrieval_options=active_retrieval_options,
                knowledge_base_id=knowledge_base_id,
                query_embedding=embedding,
                embedding_model=embedding_model,
            )
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


def _bool_option(options: dict[str, object], snake_key: str, camel_key: str) -> bool:
    value = options.get(snake_key, options.get(camel_key, False))
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


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
