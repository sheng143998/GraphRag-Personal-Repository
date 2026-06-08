# 2026-06-08 Graph Facts Query UI

## Scope

- Expose persisted GraphRAG facts through Spring Boot without moving graph extraction logic out of the AI service.
- Add a frontend workbench page for inspecting entities and relationships by knowledge base.
- Extend the local non-Docker full-chain smoke so GraphRAG persistence is verified end to end.

## Implementation

- Backend:
  - Added JPA mappings for `graph_entities` and `graph_relationships`.
  - Added `GET /api/graph/facts?knowledgeBaseId={uuid}&entity={optional}`.
  - Added `GraphFactServiceTest` for query limit, filter trimming, and DTO mapping.
  - Split unfiltered and filtered repository queries to avoid nullable PostgreSQL parameter inference errors.
- Frontend:
  - Added `frontend/src/api/graph.ts` and graph fact TypeScript types.
  - Added `frontend/src/pages/graph/GraphPage.vue`.
  - Added `/graph` route and sidebar navigation item.
- Smoke:
  - Updated the smoke document content to include GraphRAG entities.
  - Added graph fact entity/relationship assertions.
  - Updated `scripts/test-fullchain-local.ps1` so the AI service uses the same local PostgreSQL database as Spring Boot during full-chain validation.

## Validation

- `ai-service/.venv/bin/python.exe -m pytest` passed with 13 tests from `ai-service/`.
- `mvn test` passed with 7 tests.
- `npm.cmd run typecheck` passed.
- `npm.cmd run build` passed.
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1` passed with 60/60 smoke checks.
