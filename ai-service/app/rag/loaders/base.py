from app.schemas.ingest import DocumentPayload


class BaseLoader:
    async def load(self, payload: DocumentPayload) -> str:
        raise NotImplementedError


class InlineContentLoader(BaseLoader):
    async def load(self, payload: DocumentPayload) -> str:
        if payload.content_base64:
            try:
                import base64 as _b64
                decoded = _b64.b64decode(payload.content_base64)
                return decoded.decode("utf-8", errors="replace")
            except Exception:
                pass
        return payload.content or ""
