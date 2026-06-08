# RAG Evaluation Comparison Page Plan

## Goal

Add a dedicated frontend comparison page for persisted RAG experiment evaluations, reusing the Spring Boot summary endpoint already exposed at `/api/rag/experiment-evaluations/summary`.

## Scope

- Add a Vue page under `frontend/src/pages/experiments/`.
- Add a route and sidebar entry for `/experiments/comparison`.
- Reuse Pinia `experimentEvaluationSummary`; do not call FastAPI directly from the browser.
- Show aggregate ranking by strategy and experiment, plus recent evaluation rows with run context.

## Validation

- `npm.cmd run typecheck`
- `npm.cmd run build`
- Full-chain smoke remains focused on backend/API validation and already covers the summary endpoint.
