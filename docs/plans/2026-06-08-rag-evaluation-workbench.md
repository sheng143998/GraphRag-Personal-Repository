# RAG Evaluation Workbench

Date: 2026-06-08

## Goal

Make RAG experiment evaluation usable from the frontend, not only through smoke tests and backend APIs.

## Scope

- Add Spring Boot `GET /api/rag/runs?limit={n}` for recent RAG run summaries.
- Keep run lists lightweight by excluding retrieval results from summaries.
- Add frontend `fetchRagRuns()` and `evaluateExperiment()` API helpers.
- Store recent runs in the workbench store.
- Update the experiments page with a recent run selector, optional expected answer input, and `Evaluate` action.
- Rewrite the experiments page text to clean ASCII labels because the prior file contained visible mojibake strings.
- Extend full-chain smoke to verify the recent run list includes the created RAG run.

## Boundaries

- Spring Boot exposes persisted run summaries and coordinates experiment evaluation.
- FastAPI remains responsible for evaluator scoring through `/ai/rag/evaluate`.
- The browser calls Spring Boot `/api/*` only.

## Validation

- `mvn test` from `backend-java`: 14 tests passed.
- `npm.cmd run typecheck` from `frontend`: passed.
- `npm.cmd run build` from `frontend`: passed.
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`: 101/101 checks passed.
