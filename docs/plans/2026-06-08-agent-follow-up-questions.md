# Agent Follow-Up Questions Plan

Date: 2026-06-08

## Scope

- Generate deterministic study/interview follow-up questions inside the AI Agent workflow after RAG retrieval and citation preparation.
- Propagate `follow_up_questions` from FastAPI to Spring Boot as `followUpQuestions`.
- Return follow-up questions from `POST /api/chat/{sessionId}/assistant-turn`.
- Surface follow-up questions in the Vue chat page as clickable prompts that refill the question input.

## Boundaries

- AI-only Agent orchestration stays in `ai-service/`.
- Spring Boot only maps and persists the assistant-turn business flow.
- The browser continues to call Spring `/api/*` through `frontend/src/api/*`; it does not call FastAPI directly.

## Verification

- AI unit tests cover the new workflow step, trace attribute, and three generated follow-up prompts.
- Backend service tests cover DTO mapping through `/api/agent/invoke` and assistant-turn responses.
- Frontend typecheck/build cover the chat API/store/page wiring.
- Full-chain smoke covers assistant-turn follow-up questions returned through Spring.
- Final local full-chain smoke passed with 74/74 checks.
