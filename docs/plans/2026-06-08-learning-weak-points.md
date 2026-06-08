# Learning Weak Points Plan

Date: 2026-06-08

## Scope

- Persist session-level learning weak points from Agent review cards during assistant turns.
- Add `GET /api/chat/{sessionId}/weak-points` for querying the latest weak points.
- Return weak points in `POST /api/chat/{sessionId}/assistant-turn`.
- Display weak points in the Vue chat workbench.

## Boundaries

- AI still generates learning artifacts; Spring Boot persists business learning state.
- RAG and Agent orchestration remain in `ai-service/`.
- The browser continues to call Spring `/api/*` only.

## Verification

- Backend Maven tests cover weak point recording and assistant-turn response propagation.
- Frontend typecheck/build cover weak point API types, store state, and UI rendering.
- Full-chain smoke covers assistant-turn weak point creation and persisted weak point query.
- Final local full-chain smoke passed with 85/85 checks.
