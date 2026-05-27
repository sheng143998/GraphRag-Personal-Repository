from app.schemas.common import SourceMetadata
from app.services.adapters.base import AdapterCallContext, RerankAdapter


class BaseReranker:
    async def rerank(
        self,
        *,
        query: str,
        sources: list[SourceMetadata],
        context: AdapterCallContext,
    ) -> list[SourceMetadata]:
        raise NotImplementedError


class AdapterReranker(BaseReranker):
    def __init__(self, *, rerank_adapter: RerankAdapter) -> None:
        self.rerank_adapter = rerank_adapter

    async def rerank(
        self,
        *,
        query: str,
        sources: list[SourceMetadata],
        context: AdapterCallContext,
    ) -> list[SourceMetadata]:
        if not sources:
            return []
        scores = await self.rerank_adapter.rerank(
            query=query,
            documents=[source.metadata.get("content_preview", "") for source in sources],
            context=context,
        )
        updated: list[SourceMetadata] = []
        for source, score in zip(sources, scores, strict=False):
            updated.append(source.copy(update={"rerank_score": score}))
        updated.sort(key=lambda item: item.rerank_score or 0.0, reverse=True)
        return updated
