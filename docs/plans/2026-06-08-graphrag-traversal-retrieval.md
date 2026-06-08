# 2026-06-08 GraphRAG Traversal Retrieval

## Scope

- Extend GraphRAG beyond persisted graph match counts.
- Use persisted one-hop graph relationships to expand the retrieval query and expose traversal evidence in trace/citation metadata.
- Keep graph logic inside the AI service; Spring Boot remains a bridge and persistence reader.

## Implementation

- `ai-service/app/db/repositories.py`
  - `find_graph_facts()` now returns matched entities, relationship count, relationship records, and one-hop `expansion_terms`.
  - In-memory and PostgreSQL repositories return the same response shape.
- `ai-service/app/rag/strategies/advanced.py`
  - `graph-rag` appends persisted expansion terms to the graph-augmented retrieval query.
  - Trace attributes now include `graph_expansion_terms` and `graph_traversal_relationships`.
  - Citation metadata now carries traversal relationships and expansion terms.
- `smoke_test.py`
  - GraphRAG run-detail checks now assert traversal metadata is persisted through Spring Boot retrieval results.

## Validation

- `ai-service/.venv/bin/python.exe -m pytest` passed with 13 tests.
- Full verification should include backend tests, frontend typecheck/build, and local full-chain smoke after documentation updates.
