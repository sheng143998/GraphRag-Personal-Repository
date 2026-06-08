# Weak Point Practice Flow

Date: 2026-06-08

## Goal

Turn persisted learning weak points into an explicit practice workflow that runs through the existing assistant turn, saves messages, and refreshes review cards and weak points.

## Scope

- Add Spring Boot `POST /api/chat/{sessionId}/weak-points/{weakPointId}/practice-turn`.
- Validate the weak point belongs to the session.
- Build a controlled practice prompt from the weak point topic, expected answer, source hint, and optional user answer.
- Reuse `AssistantTurnService.runTurn()` so the normal Agent workflow, message persistence, review card generation, and weak point recording remain in one path.
- Add a frontend `Practice` action on weak point cards.
- Extend full-chain smoke to verify the practice turn returns a weak point, assistant message, review cards, and updated weak points.

## Boundaries

- Spring Boot coordinates the business flow and persistence.
- FastAPI remains responsible for Agent/RAG generation through the existing `/ai/agent/invoke` path.
- The browser still calls Spring Boot `/api/*` only.
- Practice turns do not automatically mark a weak point as mastered; the existing mastery buttons stay explicit.

## Validation

- `mvn test` from `backend-java`: 13 tests passed.
- `npm.cmd run typecheck` from `frontend`: passed.
- `npm.cmd run build` from `frontend`: passed.
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`: 99/99 checks passed.
