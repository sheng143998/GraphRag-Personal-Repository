# 2026-06-08 Automated Module, E2E, and RAG Evaluation Notes

## Observations

- Frontend type checking passed with `npm.cmd run typecheck`.
- Frontend production build passed with `npm.cmd run build`.
- Spring Boot backend passed `mvn test`, but the project currently has no Java test sources.
- AI service passed `.venv/bin/python.exe -m pytest` with 7 tests.
- Full-chain HTTP smoke eventually passed after starting FastAPI and Spring Boot without Docker.

## Full-Chain Startup Findings

- `docker ps` initially failed inside the sandbox because Docker config access was restricted.
- Retrying with elevated permissions reached Docker, but Docker Desktop daemon was not running.
- Starting `C:\Program Files\Docker\Docker\Docker Desktop.exe` launched Docker processes.
- After startup, `docker ps` and `docker-compose ps` both returned `Docker Desktop is unable to start`.
- No PostgreSQL or Redis listeners were available on 5432/6379.
- The backend was then started against the local PostgreSQL credentials from `.env`.
- The first service-backed smoke run passed 26/30 checks. Knowledge-base detail/update/delete and document delete failed because the running jar was stale.
- RAG query reached AI but returned 500 because AI in-memory citations referenced document/chunk ids not present in the Java database, and retrieval-result persistence tried to create mandatory foreign-key references.
- Rebuilding the backend jar picked up the missing route support.
- `RagService` now associates citation document/chunk references only when local rows exist, while still storing the retrieval result metadata.

## Fixes Made

- Stabilized AI service tests by forcing stub model providers and in-memory RAG storage before service imports.
- Replaced corrupted query transformer text with deterministic ASCII synonyms and query variants.
- Added Advanced RAG regression tests for rewrite, filtering, fusion, parent-child context, reranking, and trace metadata.
- Fixed RAG retrieval result persistence for AI citations whose ids are not present in the Java database.
- Added a heuristic RAG evaluation regression test.
- Moved pytest cache to `../.tmp/pytest-cache/ai-service` to avoid the locked `.pytest_cache` directory.

## Follow-Up

- Keep a dedicated non-Docker local startup path documented because the project can run against an existing PostgreSQL instance.
- Add Java integration tests for knowledge-base detail/update/delete, document delete, and RAG retrieval-result persistence.
