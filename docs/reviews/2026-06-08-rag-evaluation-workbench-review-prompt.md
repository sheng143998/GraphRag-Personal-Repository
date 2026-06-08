# RAG Evaluation Workbench Review Prompt

Date: 2026-06-08

Please review the frontend RAG evaluation workbench slice with these priorities:

1. API contract: `GET /api/rag/runs?limit={n}` should return recent run summaries without retrieval detail payloads.
2. Evaluation flow: the experiments page should select a recent run and call `POST /api/rag/experiments/{id}/evaluate`.
3. State update: successful evaluation should replace the updated experiment in the workbench store.
4. Architecture boundary: frontend calls Spring `/api`; Spring calls FastAPI evaluator.
5. UI behavior: the Evaluate button should be disabled until a run is selected, and experiment CRUD should remain intact.
6. Regression coverage: Maven tests should cover recent run summary mapping; smoke should cover recent run listing and existing experiment evaluation.

Validated commands:

- `mvn test` in `backend-java`: 14 tests passed.
- `npm.cmd run typecheck` in `frontend`: passed.
- `npm.cmd run build` in `frontend`: passed.
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`: 101/101 smoke checks passed.
