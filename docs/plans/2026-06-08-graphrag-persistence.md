# GraphRAG Persistence

Date: 2026-06-08

## Scope

- Persist GraphRAG entities and relationships in the shared PostgreSQL schema.
- Keep schema ownership in Spring Boot Flyway migrations.
- Keep extraction and graph fact writes in the AI service.
- Keep the existing `graph-rag` query API unchanged.

## Completed

- Added Flyway migration `V202606081300__create_graph_facts.sql`.
- Added `graph_entities` and `graph_relationships` tables with chunk, document, and knowledge-base references.
- Added in-memory and PostgreSQL repository methods for `save_graph_facts()` and `find_graph_facts()`.
- AI ingest now extracts graph entities and relationships from chunks and persists them after chunk storage.
- `graph-rag` reads persisted graph matches and exposes them in trace attributes plus citation metadata.

## Verification

- `ai-service/.venv/bin/python.exe -m pytest`: 13 passed.
- `mvn test`: 6 passed.
- `npm.cmd run typecheck`: passed.
- `npm.cmd run build`: passed.
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`: 54/54 smoke checks passed.

## Remaining Graph Hardening

- Add dedicated graph retrieval over persisted relationships instead of only enriching retrieval metadata.
- Add API/read models for inspecting graph facts from the workbench.
- Add extraction quality evaluation against a small labeled graph fixture.
