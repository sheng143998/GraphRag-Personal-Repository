# Local Full-Chain RAG Validation

Date: 2026-06-08

## Scope

- Keep Docker out of this iteration.
- Validate the completed AI, backend, frontend, and full-chain paths with local services.
- Focus Advanced RAG on strategy comparison, HTTP trace persistence, citations, and run detail retrieval.
- Preserve architecture boundaries: Vue calls Spring Boot only; Spring Boot bridges business APIs to FastAPI; FastAPI owns RAG logic.

## Automation

- `scripts/test-fullchain-local.ps1` starts FastAPI in stub/in-memory mode on `127.0.0.1:8001`, starts Spring Boot on `127.0.0.1:8080`, waits for health checks, runs `smoke_test.py`, and stops services it started.
- `smoke_test.py` reads `SMOKE_BASE_URL`, `SMOKE_AI_BASE_URL`, and `SMOKE_TIMEOUT`, so the same smoke suite can target local scripts or already-running services.

## Verification Targets

- AI: `ai-service/.venv/bin/python.exe -m pytest`
- Backend: `mvn test`
- Frontend: `npm.cmd run typecheck` and `npm.cmd run build`
- Full-chain: `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1 -SkipBuild`

## Current Result

- AI pytest passed with the offline strategy comparison evaluator included.
- Backend Maven tests passed with async ingest and RAG bridge coverage.
- Frontend typecheck and production build passed.
- Local full-chain smoke passed with 42/42 checks, including Advanced RAG query, citations, run detail, and rewritten query persistence.
