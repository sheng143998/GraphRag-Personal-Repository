# RAG Evaluation Summary Endpoint Review Prompt

Date: 2026-06-08

## Review Focus

- Confirm `GET /api/rag/experiment-evaluations/summary` is a read-only Spring aggregation endpoint and does not duplicate evaluator scoring logic.
- Check limit clamping and recent-history semantics.
- Verify averages ignore missing score values and best experiment selection is understandable.
- Confirm frontend dashboard falls back to mock/local experiment history when live summary is unavailable.
- Review smoke coverage for endpoint status, count, averages, recent rows, run context, and best experiment.

## Files

- `backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/repository/RagExperimentEvaluationRepository.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/rag/RagExperimentEvaluationSummaryResponse.java`
- `frontend/src/api/experiments.ts`
- `frontend/src/stores/workbench.ts`
- `frontend/src/pages/experiments/ExperimentsPage.vue`
- `smoke_test.py`

## Validation Commands

- `mvn test` from `backend-java/`
- `npm.cmd run typecheck` from `frontend/`
- `npm.cmd run build` from `frontend/`
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`
