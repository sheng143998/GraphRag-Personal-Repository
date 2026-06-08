# Agent Review Cards Plan

Date: 2026-06-08

## Scope

- Generate active-recall `review_cards` inside the AI Agent workflow after session study plan generation.
- Propagate FastAPI `review_cards` through Spring Boot as `reviewCards`.
- Return `reviewCards` from `POST /api/chat/{sessionId}/assistant-turn`.
- Display review cards in the Vue chat workbench.

## Boundaries

- Review card generation stays inside `ai-service/`.
- Spring Boot maps structured Agent responses and keeps assistant-turn persistence responsibilities.
- The browser continues to call Spring `/api/*` only.

## Verification

- AI pytest covers workflow step order, two generated review cards, and trace attribute propagation.
- Backend Maven tests cover Agent and assistant-turn DTO mapping.
- Frontend typecheck/build cover the chat store and page rendering path.
- Full-chain smoke covers direct Agent and assistant-turn review card responses.
- Final local full-chain smoke passed with 82/82 checks.
