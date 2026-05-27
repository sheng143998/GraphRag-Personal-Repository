from app.services.adapters.base import AdapterCallContext, EmbeddingAdapter


class BaseEmbeddingService:
    def __init__(self, *, adapter: EmbeddingAdapter) -> None:
        self.adapter = adapter

    async def embed(self, *, texts: list[str], context: AdapterCallContext) -> list[list[float]]:
        return await self.adapter.embed(texts=texts, context=context)
