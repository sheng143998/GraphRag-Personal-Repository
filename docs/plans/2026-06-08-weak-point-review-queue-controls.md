# Weak Point Review Queue Controls Plan

Date: 2026-06-08

## Scope

Improve the learning weak point panel with client-side queue controls that use the schedule fields already returned by Spring Boot.

## Implementation

- Add an `All / Due / Needs review / Mastered` queue filter in the chat workbench.
- Compute due weak points from `nextReviewAt` without changing the Spring Boot API contract.
- Add a `Practice next due` action that starts practice for the first due item in the existing prioritized list.
- Keep all browser traffic on Spring Boot `/api/*` endpoints.

## Validation

- Frontend: `npm.cmd run typecheck` passed.
- Frontend: `npm.cmd run build` passed.
- Full-chain: `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1` passed with 131/131 smoke checks.
