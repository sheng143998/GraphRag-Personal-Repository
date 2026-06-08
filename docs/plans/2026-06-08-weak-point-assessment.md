# Weak Point Assessment Plan

Date: 2026-06-08

## Scope

- Add explicit user assessment state for persisted learning weak points.
- Add `PATCH /api/chat/{sessionId}/weak-points/{weakPointId}` with `masteryStatus`.
- Support `MASTERED` and `NEEDS_REVIEW` states.
- Display weak point status and assessment buttons in the Vue chat workbench.

## Boundaries

- Spring Boot owns persisted learning state and update APIs.
- AI Agent generation remains in `ai-service/`.
- Frontend only calls Spring `/api/*`.

## Verification

- Backend Maven tests cover mastery status updates and assistant-turn response compatibility.
- Frontend typecheck/build cover weak point update API and UI actions.
- Full-chain smoke covers updating a persisted weak point to `MASTERED`.
- Final local full-chain smoke passed with 87/87 checks.
