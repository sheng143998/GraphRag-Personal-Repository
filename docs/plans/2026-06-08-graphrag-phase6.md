# Phase 6 GraphRAG First Loop

Date: 2026-06-08

## Scope

- Build the first verifiable GraphRAG engineering loop.
- Keep GraphRAG logic in `ai-service/`.
- Keep Spring Boot as the API bridge and persistence owner for existing RAG runs.
- Do not add database graph tables in this batch; persistence can follow after the graph extraction contract stabilizes.

## Completed

- Added `ai-service/app/rag/graph/extractors.py` with deterministic entity and relationship extraction.
- Added `graph-rag` to Advanced RAG supported strategy names.
- `graph-rag` now extracts query entities, creates lightweight relationships, augments the retrieval query, and stores graph metadata in trace attributes.
- Retrieved citations include `graph_entities`, `graph_matched_entities`, and `graph_relationship_count` metadata.
- Frontend strategy options now include `GraphRAG`.
- Full-chain smoke now exercises `strategyName=graph-rag` through Spring Boot `/api/rag/query`.

## Verification

- `ai-service/.venv/bin/python.exe -m pytest`: 13 passed.
- `npm.cmd run typecheck`: passed.
- `npm.cmd run build`: passed.
- `mvn test`: 6 passed.
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`: 54/54 smoke checks passed.

## Next Hardening

- Add Flyway migrations for `graph_entities` and `graph_relationships`.
- Persist extracted graph facts from document chunks.
- Add graph-aware retrieval over persisted entities/relationships instead of query-only graph augmentation.
