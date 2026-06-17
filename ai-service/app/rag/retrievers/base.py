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
        retrieval_options: dict[str, object] | None = None,
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
        retrieval_options: dict[str, object] | None = None,
    ) -> list[SourceMetadata]:
        lowered_query = query.lower()
        candidates: list[SourceMetadata] = []
        for chunk in chunks:
            if chunk.metadata.get("chunk_level") == "parent":
                continue
            if filters and any(chunk.metadata.get(key) != value for key, value in filters.items()):
                continue
            search_text = _search_text(chunk)
            score = float(search_text.lower().count(lowered_query)) if lowered_query else 0.0
            score *= _quality_score(chunk.metadata)
            candidates.append(
                SourceMetadata(
                    document_id=chunk.document_id,
                    chunk_id=chunk.chunk_id,
                    title=f"{chunk.document_id}#{chunk.chunk_index}",
                    score=score,
                    metadata=_source_metadata(chunk),
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
            search_text = _search_text(chunk)
            content = search_text.lower()
            exact_hits = content.count(lowered_query) if lowered_query else 0
            term_hits = sum(content.count(term) for term in query_terms)
            score = float(exact_hits * 2 + term_hits) * _quality_score(chunk.metadata)
            metadata = _source_metadata(chunk)
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
        retrieval_options: dict[str, object] | None = None,
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
            retrieval_options=retrieval_options or {},
        )


def _search_text(chunk: ChunkRecord) -> str:
    value = chunk.metadata.get("embedding_text")
    return str(value) if isinstance(value, str) and value.strip() else chunk.content


def _source_metadata(chunk: ChunkRecord) -> dict[str, object]:
    metadata = {**chunk.metadata, "content_preview": chunk.content[:600]}
    if chunk.parent_chunk_id:
        metadata["parent_chunk_id"] = chunk.parent_chunk_id
    return metadata


def _quality_score(metadata: dict[str, object]) -> float:
    try:
        score = float(metadata.get("quality_score", 1.0))
    except (TypeError, ValueError):
        return 1.0
    return max(0.05, min(score, 1.0))
