# RAG Experiment Evaluation Loop

Date: 2026-06-08

## Goal

Connect persisted RAG runs to the existing FastAPI RAG evaluator through Spring Boot, so an experiment can be scored from a real Advanced RAG run without adding a new migration.

## Scope

- Add `POST /api/rag/experiments/{id}/evaluate`.
- Read the selected `rag_runs` row and its ordered `rag_retrieval_results`.
- Call FastAPI `POST /ai/rag/evaluate` through `AiServiceGateway`.
- Store evaluator scores back on `rag_experiments`:
  - `precisionScore` receives evaluator `grounded_score`.
  - `recallScore` receives evaluator `retrieval_score`.
  - `status` becomes `COMPLETED`.
  - `notes` appends the evaluated run id and evaluator notes.
- Extend full-chain smoke so Advanced RAG query, persisted run lookup, and experiment evaluation are tested together.

## Boundaries

- Spring Boot only coordinates business persistence and calls the AI service.
- FastAPI remains responsible for evaluator logic.
- No frontend change in this slice because the experiments page does not yet expose a stable run picker.

## Validation

- `mvn test` from `backend-java`: 12 tests passed.
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`: 94/94 checks passed.

## Next

- Add a frontend experiment evaluation action once the UI has a clear run selection model.
- Consider a dedicated evaluation history table when multiple evaluations per experiment need to be compared instead of only updating summary fields.
