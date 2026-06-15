# 2026-06-10 Evaluation Dataset Management

## Goal

Refactor the RAG experiment page from an ad hoc run evaluator into a persistent evaluation dataset management tool.

## Scope

- Add persisted evaluation cases owned by Spring Boot.
- Keep evaluator scoring in FastAPI through the existing `/ai/rag/evaluate` bridge.
- Let the frontend manage datasets/cases, expected answers, relevant chunk/document labels, citation labels, `topK`, selected RAG run, and evaluation history.
- Preserve the architecture boundary: frontend calls only Spring Boot `/api/*`; Spring Boot persists business data and forwards scoring requests; FastAPI owns scoring logic.

## Implementation Notes

- New table: `rag_evaluation_cases`.
- New backend API under `/api/rag/evaluation-cases`.
- Existing `POST /api/rag/experiments/{id}/evaluate` remains the evaluation execution endpoint.
- Frontend page becomes a Coze-style workbench with dataset overview, case editor, run binding, and evaluation history.

## Validation

- `mvn -f backend-java/pom.xml test`
- `npm.cmd --prefix frontend run typecheck`
- `npm.cmd --prefix frontend run build`
- Browser preview smoke check for `/experiments`.
