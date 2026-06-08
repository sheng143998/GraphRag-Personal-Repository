# 2026-06-08 Weak Point Prioritization Review Prompt

Review the weak point prioritization update for correctness and architecture boundaries.

Focus areas:

- Spring Boot should remain the source of truth for weak point ordering.
- `NEEDS_REVIEW` items should be returned before `MASTERED` items.
- The ranking should remain deterministic for equal mastery states.
- Full-chain smoke should prove the post-assessment ordering through `/api/chat/{sessionId}/weak-points`.

Validation commands:

- `mvn test`
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`
