# Weak Point Practice Flow Review Prompt

Date: 2026-06-08

Please review the weak point practice flow with these priorities:

1. API contract: `POST /api/chat/{sessionId}/weak-points/{weakPointId}/practice-turn` should return `{ weakPoint, turn }`, where `turn` is the normal assistant-turn response.
2. Ownership checks: the selected weak point must belong to the session before a practice turn is generated.
3. Architecture boundary: Spring should assemble the business prompt and call the existing assistant turn; FastAPI remains the Agent/RAG generator.
4. Product behavior: practice should save user/assistant messages and refresh review cards/weak points, but should not silently mark a weak point mastered.
5. Frontend behavior: the chat page should expose a clear `Practice` action on weak point cards and continue calling only Spring `/api`.
6. Regression coverage: Maven tests should cover prompt/variables construction; full-chain smoke should cover the persisted weak point to practice turn path.

Validated commands:

- `mvn test` in `backend-java`: 13 tests passed.
- `npm.cmd run typecheck` in `frontend`: passed.
- `npm.cmd run build` in `frontend`: passed.
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`: 99/99 smoke checks passed.
