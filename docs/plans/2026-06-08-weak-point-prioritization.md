# 2026-06-08 Weak Point Prioritization

## Goal

Keep the learning loop focused on unresolved gaps by listing `NEEDS_REVIEW` weak points before `MASTERED` ones.

## Scope

- Spring Boot owns weak point persistence, ranking, and `/api/chat/*` response ordering.
- Vue consumes the ordered list from Spring Boot without calling the AI service directly.
- Full-chain smoke verifies the order after a mastery update.

## Implementation

- Add a repository query that ranks weak points by mastery status, difficulty, review count, and `lastSeenAt`.
- Update `LearningWeakPointService.listWeakPoints()` to use the prioritized query.
- Add backend unit coverage for the ordering contract.
- Extend `smoke_test.py` to re-list weak points after marking one `MASTERED`.

## Validation

- `mvn test`
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`
