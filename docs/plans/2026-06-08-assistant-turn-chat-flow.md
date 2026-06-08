# 2026-06-08 Assistant Turn Chat Flow

## Scope

- Add the first product-oriented learning/interview assistant chat turn.
- Keep browser calls on Spring Boot `/api/*`.
- Keep AI question classification, strategy selection, and RAG execution inside FastAPI Agent workflow.

## Implementation

- Backend:
  - Added `POST /api/chat/{sessionId}/assistant-turn`.
  - Added `AssistantTurnService` to save the user message, invoke the existing Agent bridge, save the assistant message with citations, and return workflow metadata plus follow-up questions.
  - Added request/response DTOs for assistant turns.
  - Added `AssistantTurnServiceTest`.
- Frontend:
  - Added assistant-turn request/response types, including `followUpQuestions`.
  - Added `sendAssistantTurn()` in `frontend/src/api/chat.ts`.
  - Updated the workbench store chat flow to auto-create a session when needed and use assistant-turn instead of the legacy direct RAG query flow.
- Smoke:
  - Added full-chain assistant-turn checks for persisted user/assistant messages, selected strategy, question type, workflow steps, and follow-up questions.

## Validation

- `mvn test` passed with 8 tests after backend implementation.
- `npm.cmd run typecheck` passed.
- `npm.cmd run build` passed.
- Full-chain smoke passed with 74/74 checks after follow-up question assertions were added.
