# Weak Point Progress Summary Plan

## Goal

Add a session-level weak point progress summary so the learning/interview assistant can show how many topics still need review, how many are mastered, and what to practice next.

## Scope

- Add a Spring Boot read endpoint under `/api/chat/{sessionId}/weak-points/summary`.
- Aggregate persisted `learning_weak_points` rows in `backend-java`; do not move learning state into FastAPI.
- Display the summary in the Vue chat workbench next to weak point cards.
- Extend local full-chain smoke to verify summary creation and update after mastery assessment.

## Validation

- Backend Maven tests for summary aggregation.
- Frontend typecheck/build for API/store/page wiring.
- Non-Docker full-chain smoke for assistant turn -> weak points -> summary -> mastery update.
