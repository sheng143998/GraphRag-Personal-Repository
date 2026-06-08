# RAG Evaluation History Review Prompt

Date: 2026-06-08

## Review Focus

- Verify Spring Boot remains a bridge/persistence layer and does not implement evaluator scoring logic.
- Check that `RagExperimentService.evaluate()` updates `rag_experiments` and inserts `rag_experiment_evaluations` in one transaction.
- Confirm the new history response fields are backward-compatible for frontend callers.
- Review Flyway migration constraints and indexes for cascade delete behavior and recent-history queries.
- Check the experiments page history UI for narrow viewport wrapping and readable score formatting.
- Verify smoke coverage proves Advanced RAG evaluation history is returned end to end.

## Files

- `backend-java/src/main/resources/db/migration/V202606081630__create_rag_experiment_evaluations.sql`
- `backend-java/src/main/java/com/example/agentknowledge/domain/RagExperimentEvaluation.java`
- `backend-java/src/main/java/com/example/agentknowledge/repository/RagExperimentEvaluationRepository.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/rag/*Evaluation*.java`
- `backend-java/src/test/java/com/example/agentknowledge/service/RagExperimentServiceTest.java`
- `frontend/src/types/index.ts`
- `frontend/src/pages/experiments/ExperimentsPage.vue`
- `frontend/src/styles.css`
- `smoke_test.py`

## Validation Commands

- `mvn test` from `backend-java/`
- `npm.cmd run typecheck` from `frontend/`
- `npm.cmd run build` from `frontend/`
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`
