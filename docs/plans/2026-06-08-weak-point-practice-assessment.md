# Weak Point Practice Assessment Plan

## Goal

Close the weak point practice loop by letting a user submit a practice answer and automatically updating mastery state from deterministic scoring.

## Scope

- Reuse `POST /api/chat/{sessionId}/weak-points/{weakPointId}/practice-turn`.
- Score `userAnswer` against the weak point expected answer in Spring Boot because mastery state is business data.
- Return the assessment, updated weak point, and refreshed summary with the existing assistant turn.
- Add a frontend answer box and submit action on weak point cards.
- Avoid database migrations in this minimal slice.

## Validation

- `mvn test`
- `npm.cmd run typecheck`
- `npm.cmd run build`
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`
