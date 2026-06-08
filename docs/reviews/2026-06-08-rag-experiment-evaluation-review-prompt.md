# RAG Experiment Evaluation Review Prompt

Date: 2026-06-08

Please review the Spring Boot RAG experiment evaluation loop with these priorities:

1. API contract: `POST /api/rag/experiments/{id}/evaluate` should accept a persisted `runId` and optional `expectedAnswer`, then return the updated experiment plus grounded/retrieval scores and notes.
2. Architecture boundary: Spring Boot should not implement evaluator scoring logic; it should only gather persisted run evidence and call FastAPI `/ai/rag/evaluate`.
3. Persistence behavior: evaluator `grounded_score` is stored as `precisionScore`, evaluator `retrieval_score` as `recallScore`, status is set to `COMPLETED`, and notes append the evaluated run id.
4. Trace and request mapping: Java DTO JSON field names must match FastAPI snake_case schema fields.
5. Regression coverage: `RagExperimentServiceTest` should verify request construction and score persistence; `smoke_test.py` should verify the full Advanced RAG run -> evaluation path.

Validated commands:

- `mvn test` in `backend-java`: 12 tests passed.
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`: 94/94 smoke checks passed.
