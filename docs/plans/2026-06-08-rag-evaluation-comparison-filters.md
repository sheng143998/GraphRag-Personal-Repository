# RAG Evaluation Comparison Filters Plan

## Goal

Make the dedicated RAG evaluation comparison page easier to inspect by filtering recent persisted evaluations by strategy and experiment.

## Scope

- Keep this as a frontend-only view enhancement.
- Reuse `experimentEvaluationSummary.recentEvaluations` from Pinia.
- Add strategy and experiment filters that affect ranking cards and recent evaluation rows.
- Do not add backend endpoints or browser calls to FastAPI.

## Validation

- `npm.cmd run typecheck`
- `npm.cmd run build`
- Non-Docker full-chain smoke remains the API regression gate for the summary endpoint.
