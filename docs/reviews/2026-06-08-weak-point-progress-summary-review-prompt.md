# Review Prompt: Weak Point Progress Summary

Review the weak point progress summary for these concerns:

- Spring Boot owns the persisted learning-state aggregation; FastAPI remains responsible only for Agent/RAG generation.
- The summary validates session ownership through the existing chat service.
- Empty sessions return zero counts and no next item.
- Frontend calls stay under `/api/chat/*` through `src/api/chat.ts`.
- Full-chain smoke proves summary values are present before and after mastery assessment.
