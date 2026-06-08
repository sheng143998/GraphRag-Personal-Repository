from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import unquote, urlparse

from app.core.config import settings
from app.schemas.common import SourceMetadata
from app.schemas.ingest import ChunkRecord, ParsedDocument
from app.rag.graph import GraphEntity, GraphRelationship

try:
    import pg8000.dbapi
except ImportError:  # pragma: no cover - only hit before dependencies are installed
    pg8000 = None


class BaseDocumentRepository:
    def save_document(self, parsed_document: ParsedDocument, *, request: Any | None = None) -> None:
        raise NotImplementedError

    def save_chunks(self, document_id: str, knowledge_base_id: str, chunks: list[ChunkRecord]) -> None:
        raise NotImplementedError

    def save_embeddings(
        self,
        *,
        chunks: list[ChunkRecord],
        embeddings: list[list[float]],
        embedding_model: str,
    ) -> None:
        raise NotImplementedError

    def get_chunks(self, document_id: str) -> list[ChunkRecord]:
        raise NotImplementedError

    def list_chunks(self, knowledge_base_id: str | None = None) -> list[ChunkRecord]:
        raise NotImplementedError

    def search_chunks(
        self,
        *,
        query: str,
        query_embedding: list[float],
        embedding_model: str,
        knowledge_base_id: str,
        top_k: int,
        filters: dict[str, object],
    ) -> list[SourceMetadata]:
        raise NotImplementedError

    def hydrate_parent_context(self, sources: list[SourceMetadata]) -> list[SourceMetadata]:
        return [_mark_parent_child_unsupported(source) for source in sources]

    def save_graph_facts(
        self,
        *,
        knowledge_base_id: str,
        document_id: str,
        chunk_id: str,
        entities: list[GraphEntity],
        relationships: list[GraphRelationship],
    ) -> None:
        raise NotImplementedError

    def find_graph_facts(
        self,
        *,
        knowledge_base_id: str | None,
        entity_names: list[str],
    ) -> dict[str, object]:
        raise NotImplementedError


@dataclass
class InMemoryDocumentRepository(BaseDocumentRepository):
    documents: dict[str, ParsedDocument] = field(default_factory=dict)
    chunks: dict[str, list[ChunkRecord]] = field(default_factory=dict)
    graph_entities: dict[str, list[GraphEntity]] = field(default_factory=dict)
    graph_relationships: dict[str, list[GraphRelationship]] = field(default_factory=dict)

    def save_document(self, parsed_document: ParsedDocument, *, request: Any | None = None) -> None:
        self.documents[parsed_document.document_id] = parsed_document

    def save_chunks(self, document_id: str, knowledge_base_id: str, chunks: list[ChunkRecord]) -> None:
        self.chunks[document_id] = chunks

    def save_embeddings(
        self,
        *,
        chunks: list[ChunkRecord],
        embeddings: list[list[float]],
        embedding_model: str,
    ) -> None:
        return None

    def get_chunks(self, document_id: str) -> list[ChunkRecord]:
        return self.chunks.get(document_id, [])

    def list_chunks(self, knowledge_base_id: str | None = None) -> list[ChunkRecord]:
        results: list[ChunkRecord] = []
        for chunk_list in self.chunks.values():
            results.extend(
                chunk
                for chunk in chunk_list
                if knowledge_base_id is None or chunk.knowledge_base_id == knowledge_base_id
            )
        return results

    def search_chunks(
        self,
        *,
        query: str,
        query_embedding: list[float],
        embedding_model: str,
        knowledge_base_id: str,
        top_k: int,
        filters: dict[str, object],
    ) -> list[SourceMetadata]:
        from app.rag.retrievers.base import SimpleRetriever

        return SimpleRetriever.score_chunks(
            query=query,
            chunks=self.list_chunks(knowledge_base_id),
            top_k=top_k,
            filters=filters,
        )

    def hydrate_parent_context(self, sources: list[SourceMetadata]) -> list[SourceMetadata]:
        hydrated: list[SourceMetadata] = []
        for source in sources:
            try:
                chunks = self.get_chunks(source.document_id)
                matched_chunk = next((chunk for chunk in chunks if chunk.chunk_id == source.chunk_id), None)
                if matched_chunk is None:
                    hydrated.append(_mark_parent_child_unsupported(source))
                    continue
                neighbors = [
                    chunk
                    for chunk in chunks
                    if matched_chunk.chunk_index - 1 <= chunk.chunk_index <= matched_chunk.chunk_index + 1
                ]
                neighbors.sort(key=lambda chunk: chunk.chunk_index)
                metadata = {**source.metadata}
                metadata["parent_child_mode"] = "neighbor-window"
                metadata["context_source_chunk_ids"] = [chunk.chunk_id for chunk in neighbors]
                metadata["content_preview"] = "\n\n".join(chunk.content for chunk in neighbors)[:1200]
                hydrated.append(source.copy(update={"metadata": metadata}))
            except Exception as exc:  # pragma: no cover - defensive fallback
                hydrated.append(_mark_parent_child_error(source, exc))
        return hydrated

    def save_graph_facts(
        self,
        *,
        knowledge_base_id: str,
        document_id: str,
        chunk_id: str,
        entities: list[GraphEntity],
        relationships: list[GraphRelationship],
    ) -> None:
        key = f"{knowledge_base_id}:{chunk_id}"
        self.graph_entities[key] = entities
        self.graph_relationships[key] = relationships

    def find_graph_facts(
        self,
        *,
        knowledge_base_id: str | None,
        entity_names: list[str],
    ) -> dict[str, object]:
        requested = {name.lower() for name in entity_names}
        matched_entities: list[str] = []
        graph_relationships: list[dict[str, object]] = []
        expansion_terms: set[str] = set()
        for key, entities in self.graph_entities.items():
            if knowledge_base_id and not key.startswith(f"{knowledge_base_id}:"):
                continue
            for entity in entities:
                if entity.name.lower() in requested:
                    matched_entities.append(entity.name)
        for key, relationships in self.graph_relationships.items():
            if knowledge_base_id and not key.startswith(f"{knowledge_base_id}:"):
                continue
            chunk_id = key.split(":", 1)[1] if ":" in key else key
            for relationship in relationships:
                source_matches = relationship.source.lower() in requested
                target_matches = relationship.target.lower() in requested
                if not source_matches and not target_matches:
                    continue
                if source_matches and relationship.target.lower() not in requested:
                    expansion_terms.add(relationship.target)
                if target_matches and relationship.source.lower() not in requested:
                    expansion_terms.add(relationship.source)
                graph_relationships.append(
                    {
                        "source": relationship.source,
                        "target": relationship.target,
                        "relation_type": relationship.relation_type,
                        "confidence": relationship.confidence,
                        "chunk_id": chunk_id,
                    }
                )
        return {
            "matched_entities": sorted(set(matched_entities)),
            "relationship_count": len(graph_relationships),
            "relationships": sorted(
                graph_relationships,
                key=lambda item: (str(item["source"]).lower(), str(item["target"]).lower(), str(item["relation_type"])),
            ),
            "expansion_terms": sorted(expansion_terms),
        }


class PostgresDocumentRepository(BaseDocumentRepository):
    def __init__(self, database_url: str) -> None:
        self.database_url = _normalize_database_url(database_url)
        self.connection_kwargs = _parse_database_url(self.database_url)

    def save_document(self, parsed_document: ParsedDocument, *, request: Any | None = None) -> None:
        if request is None:
            return
        metadata = {**request.metadata, **parsed_document.metadata}
        with self._connection() as connection:
            with _cursor(connection) as cursor:
                cursor.execute(
                    """
                    INSERT INTO documents (
                        id, knowledge_base_id, title, document_type, file_name, file_type,
                        mime_type, source_type, source_path, parser_name, parser_version,
                        status, summary, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'LOCAL_UPLOAD', %s, %s, %s, 'INDEXED', %s, %s::jsonb)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        document_type = EXCLUDED.document_type,
                        file_name = EXCLUDED.file_name,
                        file_type = EXCLUDED.file_type,
                        mime_type = EXCLUDED.mime_type,
                        source_path = EXCLUDED.source_path,
                        parser_name = EXCLUDED.parser_name,
                        parser_version = EXCLUDED.parser_version,
                        status = EXCLUDED.status,
                        summary = EXCLUDED.summary,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        parsed_document.document_id,
                        request.knowledge_base_id,
                        parsed_document.title,
                        str(request.document_type),
                        request.file.filename,
                        str(request.file.file_type),
                        request.file.mime_type,
                        request.file.source_path,
                        parsed_document.parser_name,
                        parsed_document.parser_version,
                        parsed_document.normalized_text[:1000],
                        json.dumps(metadata, ensure_ascii=False),
                    ),
                )

    def save_chunks(self, document_id: str, knowledge_base_id: str, chunks: list[ChunkRecord]) -> None:
        with self._connection() as connection:
            with _cursor(connection) as cursor:
                cursor.execute("DELETE FROM document_chunks WHERE document_id = %s", (document_id,))
                for chunk in chunks:
                    cursor.execute(
                        """
                        INSERT INTO document_chunks (
                            id, document_id, knowledge_base_id, title, content, chunk_index,
                            chunk_strategy, page_number, sheet_name, row_range, metadata
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                        """,
                        (
                            chunk.chunk_id,
                            document_id,
                            knowledge_base_id,
                            chunk.title,
                            chunk.content,
                            chunk.chunk_index,
                            chunk.metadata.get("chunk_strategy"),
                            chunk.metadata.get("page_number"),
                            chunk.metadata.get("sheet_name"),
                            chunk.metadata.get("row_range"),
                            json.dumps(chunk.metadata, ensure_ascii=False),
                        ),
                    )

    def save_embeddings(
        self,
        *,
        chunks: list[ChunkRecord],
        embeddings: list[list[float]],
        embedding_model: str,
    ) -> None:
        with self._connection() as connection:
            with _cursor(connection) as cursor:
                for chunk, embedding in zip(chunks, embeddings, strict=False):
                    cursor.execute(
                        "DELETE FROM chunk_embeddings WHERE chunk_id = %s AND embedding_model = %s",
                        (chunk.chunk_id, embedding_model),
                    )
                    cursor.execute(
                        """
                        INSERT INTO chunk_embeddings (chunk_id, embedding_model, embedding, metadata)
                        VALUES (%s, %s, %s::vector, %s::jsonb)
                        """,
                        (
                            chunk.chunk_id,
                            embedding_model,
                            _vector_literal(embedding),
                            json.dumps({"source": "stub-embedding"}, ensure_ascii=False),
                        ),
                    )

    def get_chunks(self, document_id: str) -> list[ChunkRecord]:
        with self._connection() as connection:
            with _cursor(connection) as cursor:
                cursor.execute(
                    """
                    SELECT id, document_id, knowledge_base_id, title, chunk_index, content, metadata
                    FROM document_chunks
                    WHERE document_id = %s
                    ORDER BY chunk_index ASC
                    """,
                    (document_id,),
                )
                return [_row_to_chunk(row) for row in _fetch_dicts(cursor)]

    def list_chunks(self, knowledge_base_id: str | None = None) -> list[ChunkRecord]:
        with self._connection() as connection:
            with _cursor(connection) as cursor:
                if knowledge_base_id:
                    cursor.execute(
                        """
                        SELECT id, document_id, knowledge_base_id, title, chunk_index, content, metadata
                        FROM document_chunks
                        WHERE knowledge_base_id = %s
                        ORDER BY created_at DESC
                        """,
                        (knowledge_base_id,),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id, document_id, knowledge_base_id, title, chunk_index, content, metadata
                        FROM document_chunks
                        ORDER BY created_at DESC
                        """
                    )
                return [_row_to_chunk(row) for row in _fetch_dicts(cursor)]

    def search_chunks(
        self,
        *,
        query: str,
        query_embedding: list[float],
        embedding_model: str,
        knowledge_base_id: str,
        top_k: int,
        filters: dict[str, object],
    ) -> list[SourceMetadata]:
        params: list[object] = [
            _vector_literal(query_embedding),
            query,
            embedding_model,
            knowledge_base_id,
        ]
        filter_sql = ""
        for key, value in filters.items():
            filter_sql += " AND c.metadata ->> %s = %s"
            params.extend([key, str(value)])
        params.extend(
            [
                _vector_literal(query_embedding),
                query,
                top_k,
            ]
        )
        with self._connection() as connection:
            with _cursor(connection) as cursor:
                cursor.execute(
                    f"""
                    SELECT
                        c.id AS chunk_id,
                        c.document_id,
                        d.title AS document_title,
                        d.source_path,
                        c.title AS chunk_title,
                        c.chunk_index,
                        c.content,
                        c.page_number,
                        c.sheet_name,
                        c.metadata,
                        1 - (e.embedding <=> %s::vector) AS vector_score,
                        ts_rank_cd(to_tsvector('simple', c.content), plainto_tsquery('simple', %s)) AS keyword_score
                    FROM document_chunks c
                    JOIN documents d ON d.id = c.document_id
                    LEFT JOIN chunk_embeddings e
                        ON e.chunk_id = c.id
                        AND e.embedding_model = %s
                    WHERE c.knowledge_base_id = %s
                    {filter_sql}
                    ORDER BY
                        (COALESCE(1 - (e.embedding <=> %s::vector), 0) * 0.7
                         + COALESCE(ts_rank_cd(to_tsvector('simple', c.content), plainto_tsquery('simple', %s)), 0) * 0.3) DESC,
                        c.created_at DESC
                    LIMIT %s
                    """,
                    tuple(params),
                )
                return [_row_to_source(row) for row in _fetch_dicts(cursor)]

    def hydrate_parent_context(self, sources: list[SourceMetadata]) -> list[SourceMetadata]:
        if not sources:
            return []
        try:
            with self._connection() as connection:
                with _cursor(connection) as cursor:
                    return [self._hydrate_source_parent_context(cursor, source) for source in sources]
        except Exception as exc:
            return [_mark_parent_child_error(source, exc) for source in sources]

    def _hydrate_source_parent_context(self, cursor: Any, source: SourceMetadata) -> SourceMetadata:
        cursor.execute(
            """
            SELECT document_id, chunk_index
            FROM document_chunks
            WHERE id = %s
            """,
            (source.chunk_id,),
        )
        rows = _fetch_dicts(cursor)
        if not rows:
            return _mark_parent_child_unsupported(source)

        hit = rows[0]
        cursor.execute(
            """
            SELECT id, content
            FROM document_chunks
            WHERE document_id = %s
              AND chunk_index BETWEEN %s AND %s
            ORDER BY chunk_index ASC
            """,
            (hit["document_id"], hit["chunk_index"] - 1, hit["chunk_index"] + 1),
        )
        neighbors = _fetch_dicts(cursor)
        if not neighbors:
            return _mark_parent_child_unsupported(source)

        metadata = {**source.metadata}
        metadata["parent_child_mode"] = "neighbor-window"
        metadata["context_source_chunk_ids"] = [str(row["id"]) for row in neighbors]
        metadata["content_preview"] = "\n\n".join(str(row.get("content") or "") for row in neighbors)[:1200]
        return source.copy(update={"metadata": metadata})

    def save_graph_facts(
        self,
        *,
        knowledge_base_id: str,
        document_id: str,
        chunk_id: str,
        entities: list[GraphEntity],
        relationships: list[GraphRelationship],
    ) -> None:
        if not entities:
            return
        with self._connection() as connection:
            with _cursor(connection) as cursor:
                cursor.execute("DELETE FROM graph_relationships WHERE chunk_id = %s", (chunk_id,))
                cursor.execute("DELETE FROM graph_entities WHERE chunk_id = %s", (chunk_id,))
                entity_ids: dict[str, str] = {}
                for entity in entities:
                    cursor.execute(
                        """
                        INSERT INTO graph_entities (
                            knowledge_base_id, document_id, chunk_id, name, normalized_name,
                            entity_type, aliases, metadata
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                        RETURNING id
                        """,
                        (
                            knowledge_base_id,
                            document_id,
                            chunk_id,
                            entity.name,
                            entity.name.lower(),
                            entity.entity_type,
                            json.dumps(list(entity.aliases), ensure_ascii=False),
                            json.dumps({"source": "rule-based-graph-extractor"}, ensure_ascii=False),
                        ),
                    )
                    entity_ids[entity.name] = str(cursor.fetchone()[0])

                for relationship in relationships:
                    cursor.execute(
                        """
                        INSERT INTO graph_relationships (
                            knowledge_base_id, document_id, chunk_id, source_entity_id, target_entity_id,
                            source_name, target_name, relation_type, confidence, metadata
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                        ON CONFLICT (chunk_id, source_name, target_name, relation_type) DO NOTHING
                        """,
                        (
                            knowledge_base_id,
                            document_id,
                            chunk_id,
                            entity_ids.get(relationship.source),
                            entity_ids.get(relationship.target),
                            relationship.source,
                            relationship.target,
                            relationship.relation_type,
                            relationship.confidence,
                            json.dumps({"source": "rule-based-graph-extractor"}, ensure_ascii=False),
                        ),
                    )

    def find_graph_facts(
        self,
        *,
        knowledge_base_id: str | None,
        entity_names: list[str],
    ) -> dict[str, object]:
        if not knowledge_base_id or not entity_names:
            return {"matched_entities": [], "relationship_count": 0, "relationships": [], "expansion_terms": []}
        normalized = [name.lower() for name in entity_names]
        placeholders = ", ".join(["%s"] * len(normalized))
        with self._connection() as connection:
            with _cursor(connection) as cursor:
                cursor.execute(
                    f"""
                    SELECT DISTINCT name
                    FROM graph_entities
                    WHERE knowledge_base_id = %s
                      AND normalized_name IN ({placeholders})
                    ORDER BY name
                    """,
                    tuple([knowledge_base_id, *normalized]),
                )
                matched_entities = [str(row["name"]) for row in _fetch_dicts(cursor)]
                cursor.execute(
                    f"""
                    SELECT
                        source_name,
                        target_name,
                        relation_type,
                        confidence,
                        chunk_id
                    FROM graph_relationships
                    WHERE knowledge_base_id = %s
                      AND (lower(source_name) IN ({placeholders}) OR lower(target_name) IN ({placeholders}))
                    ORDER BY confidence DESC, created_at DESC
                    LIMIT 50
                    """,
                    tuple([knowledge_base_id, *normalized, *normalized]),
                )
                relationships = _fetch_dicts(cursor)
                graph_relationships = [
                    {
                        "source": str(row["source_name"]),
                        "target": str(row["target_name"]),
                        "relation_type": str(row["relation_type"]),
                        "confidence": float(row["confidence"] or 0.0),
                        "chunk_id": str(row["chunk_id"]) if row.get("chunk_id") else None,
                    }
                    for row in relationships
                ]
                expansion_terms = sorted(
                    {
                        term
                        for relationship in graph_relationships
                        for term in (str(relationship["source"]), str(relationship["target"]))
                        if term.lower() not in normalized
                    }
                )
        return {
            "matched_entities": matched_entities,
            "relationship_count": len(graph_relationships),
            "relationships": graph_relationships,
            "expansion_terms": expansion_terms,
        }

    @contextmanager
    def _connection(self):
        if pg8000 is None:
            raise RuntimeError("pg8000 is required for database-backed RAG")
        connection = pg8000.dbapi.connect(**self.connection_kwargs)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


def build_repository() -> BaseDocumentRepository:
    if settings.rag_use_database and settings.database_url:
        return PostgresDocumentRepository(settings.database_url)
    return InMemoryDocumentRepository()


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg://"):
        return "postgresql://" + database_url.removeprefix("postgresql+psycopg://")
    return database_url


def _parse_database_url(database_url: str) -> dict[str, object]:
    parsed = urlparse(database_url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/"),
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
    }


def _fetch_dicts(cursor: Any) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]


@contextmanager
def _cursor(connection: Any):
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        cursor.close()


def _row_to_chunk(row: dict[str, Any]) -> ChunkRecord:
    return ChunkRecord(
        chunk_id=str(row["id"]),
        document_id=str(row["document_id"]),
        knowledge_base_id=str(row["knowledge_base_id"]),
        title=row.get("title"),
        chunk_index=row["chunk_index"],
        content=row["content"],
        metadata=_metadata(row.get("metadata")),
    )


def _row_to_source(row: dict[str, Any]) -> SourceMetadata:
    metadata = _metadata(row.get("metadata"))
    content = row.get("content") or ""
    metadata["content_preview"] = content[:600]
    if row.get("chunk_index") is not None:
        metadata["chunk_index"] = row["chunk_index"]
    metadata["vector_score"] = float(row["vector_score"] or 0.0)
    metadata["keyword_score"] = float(row["keyword_score"] or 0.0)
    score = metadata["vector_score"] * 0.7 + metadata["keyword_score"] * 0.3
    return SourceMetadata(
        document_id=str(row["document_id"]),
        chunk_id=str(row["chunk_id"]),
        title=row.get("chunk_title") or row.get("document_title") or str(row["document_id"]),
        source_path=row.get("source_path"),
        score=round(score, 6),
        page_number=row.get("page_number"),
        sheet_name=row.get("sheet_name"),
        metadata=metadata,
    )


def _metadata(value: Any) -> dict[str, object]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return dict(value)


def _vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(str(value) for value in embedding) + "]"


def _mark_parent_child_unsupported(source: SourceMetadata) -> SourceMetadata:
    metadata = {**source.metadata}
    metadata.setdefault("parent_child_mode", "unsupported")
    return source.copy(update={"metadata": metadata})


def _mark_parent_child_error(source: SourceMetadata, exc: Exception) -> SourceMetadata:
    metadata = {**source.metadata}
    metadata["parent_child_mode"] = metadata.get("parent_child_mode") or "fallback-error"
    metadata["fallback_error"] = str(exc)
    return source.copy(update={"metadata": metadata})


repository = build_repository()
