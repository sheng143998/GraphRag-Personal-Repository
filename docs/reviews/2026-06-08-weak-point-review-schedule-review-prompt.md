# Weak Point Review Schedule Review Prompt

Date: 2026-06-08

Review the weak point review schedule change for correctness and project-boundary compliance.

## Files

- `backend-java/src/main/resources/db/migration/V202606081700__add_weak_point_review_schedule.sql`
- `backend-java/src/main/java/com/example/agentknowledge/domain/LearningWeakPoint.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/chat/LearningWeakPointResponse.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/chat/LearningWeakPointSummaryResponse.java`
- `backend-java/src/main/java/com/example/agentknowledge/repository/LearningWeakPointRepository.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/LearningWeakPointService.java`
- `backend-java/src/test/java/com/example/agentknowledge/service/LearningWeakPointServiceTest.java`
- `backend-java/src/test/java/com/example/agentknowledge/service/WeakPointPracticeServiceTest.java`
- `backend-java/src/test/java/com/example/agentknowledge/service/AssistantTurnServiceTest.java`
- `frontend/src/types/index.ts`
- `frontend/src/pages/chat/ChatPage.vue`
- `smoke_test.py`

## Questions

- Does the Flyway migration safely add nullable schedule fields for existing weak points?
- Does manual mastery assessment schedule mastered items into the future and needs-review items as due now?
- Does practice answer assessment update score, practice count, and next review time consistently?
- Does repository prioritization keep weak points with lower mastery and due review status at the top?
- Does the frontend display schedule metadata without bypassing Spring Boot APIs?
- Do backend unit tests and full-chain smoke cover the new response fields?

## Validation Snapshot

- `mvn test`: passed with 18 tests.
- `npm.cmd run typecheck`: passed.
- `npm.cmd run build`: passed.
- Full-chain local smoke: passed with 130/130 checks.
