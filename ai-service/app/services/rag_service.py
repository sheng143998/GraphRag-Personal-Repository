from __future__ import annotations

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
        )

    async def retrieve(self, payload: RagRetrieveRequest) -> RagRetrieveResponse:
        trace_builder = TraceBuilder(
            operation="rag_retrieve",
            strategy_name=payload.strategy_name,
            model_name=get_embedding_model_name(),
        )
        query_embeddings = await embedding_adapter.embed(
            texts=[payload.query],
            context=AdapterCallContext(
                trace_id=trace_builder.trace.trace_id,
                run_id=trace_builder.trace.run_id,
                operation="embed_query",
                model_name=get_embedding_model_name(),
                strategy_name=payload.strategy_name,
            ),
        )
        strategy = self._select_strategy(payload.strategy_name)
        reranked = await strategy.run(
            query=payload.query,
            top_k=payload.top_k,
            trace_builder=trace_builder,
            filters=payload.context.metadata_filters,
            retrieval_options=payload.context.retrieval_options,
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
        query_embeddings = await embedding_adapter.embed(
            texts=[payload.question],
            context=AdapterCallContext(
                trace_id=trace_builder.trace.trace_id,
                run_id=trace_builder.trace.run_id,
                operation="embed_query",
                model_name=get_embedding_model_name(),
                strategy_name=payload.strategy_name,
            ),
        )
        trace_builder.add_step(
            name="embed_query",
            status="completed",
            detail="Embedded query for vector retrieval.",
            model_name=get_embedding_model_name(),
        )
        strategy = self._select_strategy(payload.strategy_name)
        citations = await strategy.run(
            query=payload.question,
            top_k=payload.top_k,
            trace_builder=trace_builder,
            filters=payload.context.metadata_filters,
            retrieval_options=payload.context.retrieval_options,
            knowledge_base_id=payload.context.knowledge_base_id,
            query_embedding=query_embeddings[0],
            embedding_model=get_embedding_model_name(),
        )
        prompt = prompt_registry.render(
            name=settings.default_prompt_name,
            version=settings.default_prompt_version,
            variables={
                "question": payload.question,
                "context": "\n\n".join(item.metadata.get("content_preview", "") for item in citations),
            },
        )
        answer = await self.generator.generate(
            prompt=prompt,
            context=AdapterCallContext(
                trace_id=trace_builder.trace.trace_id,
                run_id=trace_builder.trace.run_id,
                operation="generate_answer",
                model_name=get_llm_model_name(),
                prompt_name=settings.default_prompt_name,
                prompt_version=settings.default_prompt_version,
                strategy_name=payload.strategy_name,
            ),
        )
        trace_builder.add_step(
            name="generate",
            status="completed",
            detail="Generated answer from retrieved context.",
            model_name=get_llm_model_name(),
            payload={"citation_count": len(citations)},
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
