# RAG Evaluation Comparison Dashboard Plan

Date: 2026-06-08

## Scope

- Make persisted experiment evaluation history easier to compare in the frontend workbench.
- Keep scoring in FastAPI `/ai/rag/evaluate`; Spring Boot only returns persisted run context alongside evaluation history.
- Avoid adding a charting dependency or a new backend aggregation endpoint in this iteration.

## Implementation

- Extend `RagExperimentEvaluationHistoryResponse` with read-only RAG run summary fields:
  - `runQuestion`
  - `runStrategyName`
  - `runRetrieverType`
  - `runModelName`
  - `runLatencyMs`
  - `runCreatedAt`
- Update the experiments page dashboard with recent-history totals, average grounded/retrieval scores, best latest experiment, per-experiment history averages, and latest score deltas.
- Upgrade history rows from opaque run ids to question snapshots, run strategy, retriever/model details, latency, scores, and delta labels.
- Seed frontend mock experiments with evaluation history so the dashboard is visible before live API data loads.

## Validation

- Backend Maven tests verify history responses include run question, strategy, retriever, model, latency, and run creation time.
- Frontend typecheck/build verify dashboard typing and rendering paths.
- Full-chain smoke evaluates the same experiment twice and verifies history comparison data is returned end to end.
