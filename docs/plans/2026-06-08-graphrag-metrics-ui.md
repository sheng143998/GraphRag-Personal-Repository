# 2026-06-08 GraphRAG Metrics UI

## Goal

Surface GraphRAG evaluation metric notes in the frontend experiment views so users can compare entity, relationship, and expansion-term quality without reading raw evaluator text.

## Scope

- Parse GraphRAG metric notes from persisted experiment evaluation history.
- Show compact GraphRAG metric tiles in the experiment history list.
- Add a Graph metrics column to the comparison page.
- Keep browser traffic on Spring Boot `/api/*`; no FastAPI direct calls.
- Keep backend and FastAPI contracts unchanged.

## Out Of Scope

- New backend aggregation fields.
- Editing GraphRAG metric weights.
- Docker validation.
