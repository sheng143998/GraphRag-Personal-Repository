# Agent Study Plan Plan

Date: 2026-06-08

## Scope

- Generate a short session-level `study_plan` inside the AI Agent workflow after follow-up question generation.
- Propagate FastAPI `study_plan` through Spring Boot as `studyPlan`.
- Return `studyPlan` from `POST /api/chat/{sessionId}/assistant-turn`.
- Display the plan in the Vue chat workbench next to strategy and citation context.

## Boundaries

- Study plan generation remains in `ai-service/`.
- Spring Boot maps the structured response and keeps assistant-turn persistence responsibilities.
- The browser continues to call Spring `/api/*` only.

## Verification

- AI pytest covers workflow step order, three study plan steps, and trace attribute propagation.
- Backend Maven tests cover Agent and assistant-turn DTO mapping.
- Frontend typecheck/build cover the chat store and page rendering path.
- Full-chain smoke covers direct Agent and assistant-turn study plan responses.
- Final local full-chain smoke passed with 78/78 checks.
