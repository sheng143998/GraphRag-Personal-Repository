# Weak Point Review Queue Controls Review Prompt

Date: 2026-06-08

Review the chat workbench weak point queue controls.

## Files

- `frontend/src/pages/chat/ChatPage.vue`
- `docs/plans/2026-06-08-weak-point-review-queue-controls.md`
- `docs/testing/strategy.md`
- `docs/handoff/CURRENT_STATE.md`
- `PROJECT_CONTEXT.md`

## Questions

- Does the filter logic use `nextReviewAt` consistently with the backend schedule semantics?
- Does `Practice next due` use the existing store action and avoid new browser-to-FastAPI calls?
- Does the UI handle empty filtered queues without hiding the summary metrics?
- Does the feature remain frontend-only without changing Spring or FastAPI contracts?

## Validation Snapshot

- `npm.cmd run typecheck`: passed.
- `npm.cmd run build`: passed.
- Full-chain local smoke: passed with 131/131 checks.

Reviewer hardening applied:

- Status comparisons normalize the backend string before matching.
- Invalid `nextReviewAt` values are not treated as due.
- `Practice next due` is disabled without an active session and clears stale assessment focus before launching practice.
