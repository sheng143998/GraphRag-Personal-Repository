# RAG Evaluation Summary Endpoint Plan

Date: 2026-06-08

## Scope

- Add a backend aggregation endpoint for recent RAG experiment evaluation history.
- Let the frontend experiments dashboard use the aggregation endpoint instead of deriving all global metrics from experiment list rows.
- Keep FastAPI evaluator logic unchanged; Spring Boot only reads persisted evaluation history and summarizes business data.

## Implementation

- Add `GET /api/rag/experiment-evaluations/summary?limit={n}`.
- Return recent evaluation count, average grounded score, average retrieval score, best experiment, and recent evaluation rows.
- Reuse `RagExperimentEvaluationHistoryResponse` for recent rows and include `experimentName` for display.
- Add `RagExperimentEvaluationSummaryResponse`.
- Fetch the summary in the Pinia workbench store during hydrate and after experiment evaluation.

## Validation

- Backend Maven tests cover summary aggregation, best experiment selection, and run context propagation.
- Frontend typecheck/build cover summary API typing and dashboard state usage.
- Full-chain smoke validates the endpoint after two evaluations of the same experiment.
