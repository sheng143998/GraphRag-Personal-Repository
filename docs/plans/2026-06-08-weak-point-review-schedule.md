# Weak Point Review Schedule Plan

Date: 2026-06-08

## Scope

Add a lightweight spaced-review schedule to the learning weak point workflow after practice answers are assessed.

## Implementation

- Persist `practiceCount`, `lastPracticeScore`, and `nextReviewAt` on weak points.
- Include `dueReviewCount` in the weak point summary.
- Prioritize due weak points before future scheduled items.
- Backfill historical mastered weak points so they are not all immediately due after migration.
- Update weak point practice assessment so score and pass/fail status determine the next review time.
- Surface practice count, last score, due count, and next review time in the chat workbench.
- Extend full-chain smoke checks to assert the new scheduling fields.

## Review Rules

- Keep weak point scheduling in Spring Boot because it is business learning state.
- Keep RAG/Agent generation in FastAPI through the existing Spring bridge.
- Keep the browser on Spring `/api/*` endpoints only.

## Validation

- Backend: `mvn test` passed with 18 tests.
- Frontend: `npm.cmd run typecheck` passed.
- Frontend: `npm.cmd run build` passed.
- Full-chain: `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1` passed with 131/131 smoke checks.
- Follow-up review hardening added due-first sorting, mastered-row schedule backfill, and a future-time smoke assertion for practice `nextReviewAt`.
