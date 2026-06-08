# 2026-06-08 Assistant Turn Chat Flow

## Scope

- Add the first product-oriented learning/interview assistant chat turn.
- Keep browser calls on Spring Boot `/api/*`.
- Keep AI question classification, strategy selection, and RAG execution inside FastAPI Agent workflow.

## Implementation

- Backend:
  - Added `POST /api/chat/{sessionId}/assistant-turn`.
  - Added `AssistantTurnService` to save the user message, invoke the existing Agent bridge, save the assistant message with citations, and return workflow metadata.
  - Added request/response DTOs for assistant turns.
  - Added `AssistantTurnServiceTest`.
- Frontend:
  - Added assistant-turn request/response types.
  - Added `sendAssistantTurn()` in `frontend/src/api/chat.ts`.
  - Updated the workbench store chat flow to auto-create a session when needed and use assistant-turn instead of the legacy direct RAG query flow.
- Smoke:
  - Added full-chain assistant-turn checks for persisted user/assistant messages, selected strategy, question type, and workflow steps.

## Validation

- `mvn test` passed with 8 tests after backend implementation.
- `npm.cmd run typecheck` passed.
- `npm.cmd run build` passed.
- Full-chain smoke should be run after final doc updates.
