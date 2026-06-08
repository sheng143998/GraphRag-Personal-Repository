from __future__ import annotations

from app.db.repositories import repository
from app.schemas.common import SourceMetadata
from app.schemas.ingest import ChunkRecord


class BaseRetriever:
    async def retrieve(
        self,
        *,
        query: str,
        chunks: list[ChunkRecord],
        top_k: int,
        filters: dict[str, object],
    ) -> list[SourceMetadata]:
        raise NotImplementedError


class SimpleRetriever(BaseRetriever):
    async def retrieve(
        self,
        *,
        query: str,
        chunks: list[ChunkRecord],
        top_k: int,
        filters: dict[str, object],
    ) -> list[SourceMetadata]:
        lowered_query = query.lower()
        candidates: list[SourceMetadata] = []
        for chunk in chunks:
            if chunk.metadata.get("chunk_level") == "parent":
                continue
            if filters and any(chunk.metadata.get(key) != value for key, value in filters.items()):
                continue
            score = float(chunk.content.lower().count(lowered_query)) if lowered_query else 0.0
            candidates.append(
                SourceMetadata(
                    document_id=chunk.document_id,
                    chunk_id=chunk.chunk_id,
                    title=f"{chunk.document_id}#{chunk.chunk_index}",
                    score=score,
                    metadata=chunk.metadata,
                )
            )
        candidates.sort(key=lambda item: item.score or 0.0, reverse=True)
        return candidates[:top_k]

    @staticmethod
    def score_chunks(
        *,
        query: str,
        chunks: list[ChunkRecord],
        top_k: int,
        filters: dict[str, object],
    ) -> list[SourceMetadata]:
        lowered_query = query.lower()
        query_terms = set(lowered_query.split())
        candidates: list[SourceMetadata] = []
        for chunk in chunks:
            if chunk.metadata.get("chunk_level") == "parent":
                continue
            if filters and any(chunk.metadata.get(key) != value for key, value in filters.items()):
                continue
            content = chunk.content.lower()
            exact_hits = content.count(lowered_query) if lowered_query else 0
            term_hits = sum(content.count(term) for term in query_terms)
            score = float(exact_hits * 2 + term_hits)
            metadata = {**chunk.metadata, "content_preview": chunk.content[:600]}
            candidates.append(
                SourceMetadata(
                    document_id=chunk.document_id,
                    chunk_id=chunk.chunk_id,
                    title=chunk.title or f"{chunk.document_id}#{chunk.chunk_index}",
                    score=score,
                    metadata=metadata,
                )
            )
        candidates.sort(key=lambda item: item.score or 0.0, reverse=True)
        return candidates[:top_k]


class DatabaseRetriever(BaseRetriever):
    async def retrieve(
        self,
        *,
        query: str,
        chunks: list[ChunkRecord],
        top_k: int,
        filters: dict[str, object],
        knowledge_base_id: str | None = None,
        query_embedding: list[float] | None = None,
        embedding_model: str | None = None,
    ) -> list[SourceMetadata]:
        if not knowledge_base_id or query_embedding is None or not embedding_model:
            return SimpleRetriever.score_chunks(
                query=query,
                chunks=chunks,
                top_k=top_k,
                filters=filters,
            )
        return repository.search_chunks(
            query=query,
            query_embedding=query_embedding,
            embedding_model=embedding_model,
            knowledge_base_id=knowledge_base_id,
            top_k=top_k,
            filters=filters,
        )
