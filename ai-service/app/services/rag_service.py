from __future__ import annotations

from time import perf_counter

from app.core.config import settings
from app.core.tracing import TraceBuilder
from app.prompts.registry import prompt_registry
from app.rag.evaluators.base import SimpleRagEvaluator
from app.rag.generators.base import SimpleGenerator
from app.rag.retrievers.base import DatabaseRetriever
from app.rag.rerankers.base import AdapterReranker
from app.rag.strategies.advanced import AdvancedRagStrategy
from app.rag.strategies.base import BasicRagStrategy
from app.schemas.rag import (
    RagEvaluateRequest,
    RagEvaluateResponse,
    RagQueryRequest,
    RagQueryResponse,
    RagRetrieveRequest,
    RagRetrieveResponse,
)
from app.services.adapters.base import AdapterCallContext
from app.services.adapters.registry import (
    get_llm_model_name,
    get_embedding_model_name,
    embedding_adapter,
    llm_adapter,
    rerank_adapter,
)


class RagService:
    def __init__(self) -> None:
        self.retriever = DatabaseRetriever()
        self.reranker = AdapterReranker(rerank_adapter=rerank_adapter)
        self.generator = SimpleGenerator(llm_adapter=llm_adapter)
        self.evaluator = SimpleRagEvaluator()
        self.basic_strategy = BasicRagStrategy(
            retriever=self.retriever,
            reranker=self.reranker,
            generator=self.generator,
        )
        self.advanced_strategy = AdvancedRagStrategy(
            retriever=self.retriever,
            reranker=self.reranker,
            embedding_adapter=embedding_adapter,
            llm_adapter=llm_adapter,
        )

    async def retrieve(self, payload: RagRetrieveRequest) -> RagRetrieveResponse:
        trace_builder = TraceBuilder(
            operation="rag_retrieve",
            strategy_name=payload.strategy_name,
            model_name=get_embedding_model_name(),
        )
        retrieval_options = _route_retrieval_options(
            question=payload.query,
            retrieval_options=payload.context.retrieval_options,
        )
        trace_builder.set_attribute("question_type", retrieval_options["question_type"])
        trace_builder.set_attribute(
            "enable_parent_child_context",
            retrieval_options["enable_parent_child_context"],
        )
        embed_context = AdapterCallContext(
            trace_id=trace_builder.trace.trace_id,
            run_id=trace_builder.trace.run_id,
            operation="embed_query",
            model_name=get_embedding_model_name(),
            strategy_name=payload.strategy_name,
        )
        query_embeddings = await embedding_adapter.embed(
            texts=[payload.query],
            context=embed_context,
        )
        trace_builder.record_adapter_metadata(embed_context.metadata)
        strategy = self._select_strategy(payload.strategy_name)
        reranked = await strategy.run(
            query=payload.query,
            top_k=payload.top_k,
            trace_builder=trace_builder,
            filters=payload.context.metadata_filters,
            retrieval_options=retrieval_options,
            knowledge_base_id=payload.context.knowledge_base_id,
            query_embedding=query_embeddings[0],
            embedding_model=get_embedding_model_name(),
        )
        trace = trace_builder.finalize(status="completed")
        return RagRetrieveResponse(
            query=payload.query,
            strategy_name=payload.strategy_name,
            results=reranked,
            trace=trace,
        )

    async def query(self, payload: RagQueryRequest) -> RagQueryResponse:
        trace_builder = TraceBuilder(
            operation="rag_query",
            strategy_name=payload.strategy_name,
            prompt_name=settings.default_prompt_name,
            prompt_version=settings.default_prompt_version,
            model_name=get_llm_model_name(),
        )
        retrieval_options = _route_retrieval_options(
            question=payload.question,
            retrieval_options=payload.context.retrieval_options,
        )
        trace_builder.set_attribute("question_type", retrieval_options["question_type"])
        trace_builder.set_attribute(
            "enable_parent_child_context",
            retrieval_options["enable_parent_child_context"],
        )
        embed_context = AdapterCallContext(
            trace_id=trace_builder.trace.trace_id,
            run_id=trace_builder.trace.run_id,
            operation="embed_query",
            model_name=get_embedding_model_name(),
            strategy_name=payload.strategy_name,
        )
        fallback_embed_started_at = perf_counter()
        query_embeddings = await embedding_adapter.embed(
            texts=[payload.question],
            context=embed_context,
        )
        embed_metadata = trace_builder.record_adapter_metadata(embed_context.metadata)
        embed_latency_ms = embed_metadata.get("latency_ms")
        if embed_latency_ms is None:
            embed_latency_ms = round((perf_counter() - fallback_embed_started_at) * 1000, 3)
        trace_builder.add_step(
            name="embed_query",
            status="completed",
            detail="Embedded query for vector retrieval.",
            model_name=get_embedding_model_name(),
            payload={"latency_ms": embed_latency_ms},
        )
        strategy = self._select_strategy(payload.strategy_name)
        citations = await strategy.run(
            query=payload.question,
            top_k=payload.top_k,
            trace_builder=trace_builder,
            filters=payload.context.metadata_filters,
            retrieval_options=retrieval_options,
            knowledge_base_id=payload.context.knowledge_base_id,
            query_embedding=query_embeddings[0],
            embedding_model=get_embedding_model_name(),
        )
        prompt = prompt_registry.render(
            name=settings.default_prompt_name,
            version=settings.default_prompt_version,
            variables={
                "query": payload.question,
                "context_str": _build_context_str(citations),
            },
        )
        generate_context = AdapterCallContext(
            trace_id=trace_builder.trace.trace_id,
            run_id=trace_builder.trace.run_id,
            operation="generate_answer",
            model_name=get_llm_model_name(),
            prompt_name=settings.default_prompt_name,
            prompt_version=settings.default_prompt_version,
            strategy_name=payload.strategy_name,
        )
        fallback_generate_started_at = perf_counter()
        answer = await self.generator.generate(
            prompt=prompt,
            context=generate_context,
        )
        generate_metadata = trace_builder.record_adapter_metadata(generate_context.metadata)
        generate_latency_ms = generate_metadata.get("latency_ms")
        if generate_latency_ms is None:
            generate_latency_ms = round((perf_counter() - fallback_generate_started_at) * 1000, 3)
        trace_builder.add_step(
            name="generate",
            status="completed",
            detail="Generated answer from retrieved context.",
            model_name=get_llm_model_name(),
            payload={"citation_count": len(citations), "latency_ms": generate_latency_ms},
        )
        trace = trace_builder.finalize(status="completed")
        return RagQueryResponse(
            question=payload.question,
            answer=answer,
            citations=citations,
            trace=trace,
        )

    def _select_strategy(self, strategy_name: str) -> BasicRagStrategy | AdvancedRagStrategy:
        if strategy_name == "basic-rag":
            return self.basic_strategy
        if strategy_name in AdvancedRagStrategy.supported_strategy_names:
            return self.advanced_strategy
        raise ValueError(f"Unsupported RAG strategy: {strategy_name}")

    async def evaluate(self, payload: RagEvaluateRequest) -> RagEvaluateResponse:
        trace_builder = TraceBuilder(
            operation="rag_evaluate",
            strategy_name=payload.strategy_name,
            model_name="rule-evaluator",
        )
        result = await self.evaluator.evaluate(payload)
        trace_builder.add_step(
            name="evaluate",
            status="completed",
            detail="Evaluated groundedness and retrieval quality.",
            payload=result.dict(),
        )
        trace = trace_builder.finalize(status="completed")
        return RagEvaluateResponse(result=result, trace=trace)


def _build_context_str(citations) -> str:
    if not citations:
        return "无检索上下文。"
    blocks: list[str] = []
    for index, item in enumerate(citations, start=1):
        title = item.title or "未命名来源"
        source_path = item.source_path or "无来源链接"
        snippet = str(item.metadata.get("content_preview", "")).strip() or "无摘要"
        blocks.append(
            f"[{index}] 标题: {title}\n"
            f"来源: {source_path}\n"
            f"摘要: {snippet}"
        )
    return "\n\n".join(blocks)


def _route_retrieval_options(
    *,
    question: str,
    retrieval_options: dict[str, object] | None,
) -> dict[str, object]:
    routed = dict(retrieval_options or {})
    question_type = str(
        routed.get("question_type")
        or routed.get("questionType")
        or _classify_question_type(question)
    ).strip().lower()
    routed["question_type"] = question_type
    if "enable_parent_child_context" not in routed and "enableParentChildContext" not in routed:
        routed["enable_parent_child_context"] = question_type in {
            "conceptual",
            "implementation",
            "troubleshooting",
            "interview",
            "summary",
            "comparison",
        }
    elif "enable_parent_child_context" not in routed:
        routed["enable_parent_child_context"] = _bool_option(
            routed.get("enableParentChildContext"),
            default=True,
        )
    else:
        routed["enable_parent_child_context"] = _bool_option(
            routed.get("enable_parent_child_context"),
            default=True,
        )
    return routed


def _classify_question_type(question: str) -> str:
    lowered = question.lower()
    if any(term in lowered for term in ("compare", "difference", "vs", "对比", "区别", "差异")):
        return "comparison"
    if any(term in lowered for term in ("summary", "overview", "summarize", "总结", "概括", "梳理")):
        return "summary"
    if any(term in lowered for term in ("bug", "error", "exception", "traceback", "报错", "异常", "失败", "排查")):
        return "troubleshooting"
    if any(term in lowered for term in ("implement", "code", "class", "function", "api", "实现", "代码", "接口")):
        return "implementation"
    if any(term in lowered for term in ("interview", "面试", "八股")):
        return "interview"
    if any(term in lowered for term in ("what", "why", "how", "原理", "什么", "为什么", "如何", "怎么")):
        return "conceptual"
    return "fact_lookup"


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
