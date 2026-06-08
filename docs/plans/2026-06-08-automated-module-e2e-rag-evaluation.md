# 2026-06-08 Automated Module, E2E, and RAG Evaluation

## Scope

- Review completed frontend, Spring Boot backend, and FastAPI AI service modules.
- Run module-level verification for completed work.
- Focus Advanced RAG regression coverage on strategy dispatch, query rewrite, multi-query retrieval, metadata filtering, parent-child context hydration, reranking, and trace metadata.
- Run full-chain HTTP smoke after module tests are stable.
- Run RAG evaluation after full-chain verification and record optimization notes.
- Commit changes in focused groups instead of one large commit.

## Planned Commands

- Frontend: `npm run typecheck`, `npm run build`
- Backend: `mvn test`
- AI service: `pytest`
- Full chain: `python smoke_test.py`

## Result Log

- `frontend`: `npm.cmd run typecheck` passed.
- `frontend`: `npm.cmd run build` passed.
- `backend-java`: `mvn test` passed; Maven reported no test sources.
- `ai-service`: `.venv/bin/python.exe -m pytest` passed with 7 tests.
- Advanced RAG regression coverage was added for query rewrite, metadata filtering, multi-query fusion, parent-child neighbor context, reranking trace steps, and heuristic RAG evaluation.
- Full-chain HTTP smoke initially failed because local services were not running and Docker Desktop could not start.
- The chain was rerun without Docker by starting FastAPI in stub/in-memory mode and Spring Boot against the local PostgreSQL credentials from `.env`.
- First real smoke run reached the services and passed 26/30 checks; failures exposed stale backend packaging and a RAG retrieval-result foreign-key mismatch when AI citations referenced chunks not present in the Java database.
- RAG retrieval result persistence was hardened to associate local document/chunk rows only when they exist.
- Rebuilt the Spring Boot jar and reran `python smoke_test.py`: 34/34 checks passed.
- Additional Advanced RAG HTTP smoke passed with `strategyName=advanced-rag`, run status `COMPLETED`, one citation, and a populated `rewrittenQuery`.
