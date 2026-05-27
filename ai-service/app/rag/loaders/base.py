from app.schemas.ingest import DocumentPayload


class BaseLoader:
    async def load(self, payload: DocumentPayload) -> str:
        raise NotImplementedError


class InlineContentLoader(BaseLoader):
    async def load(self, payload: DocumentPayload) -> str:
        return payload.content or ""
