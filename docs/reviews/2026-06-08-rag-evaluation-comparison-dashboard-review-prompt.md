# RAG Evaluation Comparison Dashboard Review Prompt

Date: 2026-06-08

## Review Focus

- Verify Spring Boot only exposes persisted run context and does not implement new evaluator scoring logic.
- Check the history DTO extension for backward-compatible JSON field additions.
- Confirm the experiments page dashboard communicates recent-history scope, not all-time metrics.
- Review frontend layout for long questions, long experiment names, and narrow viewports.
- Confirm the smoke test proves two evaluations for one experiment produce comparison history.

## Files

- `backend-java/src/main/java/com/example/agentknowledge/dto/rag/RagExperimentEvaluationHistoryResponse.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
- `backend-java/src/test/java/com/example/agentknowledge/service/RagExperimentServiceTest.java`
- `frontend/src/types/index.ts`
- `frontend/src/pages/experiments/ExperimentsPage.vue`
- `frontend/src/styles.css`
- `frontend/src/utils/mock-data.ts`
- `smoke_test.py`

## Validation Commands

- `mvn test` from `backend-java/`
- `npm.cmd run typecheck` from `frontend/`
- `npm.cmd run build` from `frontend/`
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`
