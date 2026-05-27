from app.core.tracing import TraceBuilder
from app.db.repositories import repository
from app.rag.generators.base import BaseGenerator
from app.rag.rerankers.base import BaseReranker
from app.rag.retrievers.base import BaseRetriever
from app.schemas.common import SourceMetadata
from app.services.adapters.base import AdapterCallContext
from app.services.adapters.registry import get_rerank_model_name


class BaseRagStrategy:
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
        raise NotImplementedError


class BasicRagStrategy(BaseRagStrategy):
    def __init__(
        self,
        *,
        retriever: BaseRetriever,
        reranker: BaseReranker,
        generator: BaseGenerator,
    ) -> None:
        self.retriever = retriever
        self.reranker = reranker
        self.generator = generator

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
        candidates = await self.retriever.retrieve(
            query=query,
            chunks=repository.list_chunks(knowledge_base_id),
            top_k=top_k,
            filters=filters,
            knowledge_base_id=knowledge_base_id,
            query_embedding=query_embedding,
            embedding_model=embedding_model,
        )
        trace_builder.add_step(
            name="retrieve",
            status="completed",
            detail="Retrieved candidate chunks.",
            payload={"result_count": len(candidates)},
        )
        reranked = await self.reranker.rerank(
            query=query,
            sources=candidates,
            context=AdapterCallContext(
                trace_id=trace_builder.trace.trace_id,
                run_id=trace_builder.trace.run_id,
                operation="rerank",
                model_name=get_rerank_model_name(),
                strategy_name=trace_builder.trace.strategy_name,
            ),
        )
        trace_builder.add_step(
            name="rerank",
            status="completed",
            detail="Reranked retrieved chunks.",
            model_name=get_rerank_model_name(),
            payload={"result_count": len(reranked)},
        )
        return reranked
