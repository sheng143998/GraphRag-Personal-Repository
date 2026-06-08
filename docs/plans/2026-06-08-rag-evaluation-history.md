# RAG Evaluation History Plan

Date: 2026-06-08

## Scope

- Persist every `POST /api/rag/experiments/{id}/evaluate` result as an immutable experiment evaluation history row.
- Keep evaluator scoring logic in FastAPI `/ai/rag/evaluate`; Spring Boot only bridges, updates the experiment summary, and stores business history.
- Return recent history in experiment responses so the frontend workbench can display repeated evaluation runs.
- Extend non-Docker full-chain smoke coverage for the Advanced RAG evaluation path.

## Implementation

- Add Flyway migration `V202606081630__create_rag_experiment_evaluations.sql`.
- Add `RagExperimentEvaluation` entity and `RagExperimentEvaluationRepository`.
- Extend `RagExperimentResponse` and `RagExperimentEvaluationResponse` with evaluation history DTOs.
- Make `RagExperimentService.evaluate()` transactional so experiment summary updates and history persistence commit together.
- Show recent evaluation history in `frontend/src/pages/experiments/ExperimentsPage.vue`.

## Validation

- Backend unit test: `RagExperimentServiceTest` verifies evaluator request construction, experiment score update, and history row persistence.
- Frontend typecheck/build covers the new response types and history UI.
- Full-chain smoke asserts `data.evaluation`, `data.history`, and `data.experiment.evaluations` for the Advanced RAG run evaluation.
