# Structured RAG Evaluation UI Plan

## Goal

Expose the structured RAG evaluation case flow from the experiments page so users can evaluate a persisted run with retrieval relevance data without hand-copying chunk ids.

## Scope

- Keep browser calls under Spring Boot `/api/*`.
- Load the selected RAG run detail through the existing Spring run-detail endpoint.
- Build a structured evaluation case from the top retrieval result.
- Submit the structured case through the existing experiment evaluation API.
- Keep the existing simple expected-answer evaluation path available.

## Validation

- `npm.cmd run typecheck`
- `npm.cmd run build`
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`
