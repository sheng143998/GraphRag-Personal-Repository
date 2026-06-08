# 2026-06-08 Iterative Test Hardening

## Scope

- Make full-chain smoke stricter for RAG failures.
- Add Advanced RAG HTTP trace assertions to the full-chain smoke path.
- Add Java unit coverage for the Spring Boot RAG bridge without requiring a database.
- Re-run frontend, backend, AI service, and full-chain tests.

## Changes

- `smoke_test.py` now requires `/api/rag/query` to return HTTP 200 instead of treating failures as graceful.
- `smoke_test.py` now runs an `advanced-rag` query and checks:
  - run id is present
  - status is `COMPLETED`
  - strategy is `advanced-rag`
  - at least one citation is present
  - stored run exposes a populated `rewrittenQuery`
- Added `RagServiceTest` to verify:
  - metadata filters are forwarded to the AI service request
  - rewritten query from AI trace metadata is persisted on the run
  - retrieval results remain valid when AI citation document/chunk ids do not exist in the Java database

## Verification

- `ai-service`: `.venv/bin/python.exe -m pytest` -> 7 passed
- `frontend`: `npm.cmd run typecheck` -> passed
- `frontend`: `npm.cmd run build` -> passed
- `backend-java`: `mvn test` -> 1 test passed
- Full-chain: `python smoke_test.py` -> 42/42 passed

## Notes

- Maven test execution needed elevated permissions because Windows denied sandboxed reads of the local Maven repository jar path.
- Full-chain testing used local PostgreSQL credentials from `.env` and FastAPI stub/in-memory mode.
