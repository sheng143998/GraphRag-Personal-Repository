# Learning Weak Points Review Prompt

Please review the learning weak points change with focus on:

- Weak points are persisted in Spring Boot from Agent `reviewCards` without moving Agent/RAG logic out of `ai-service/`.
- `learning_weak_points` correctly links session, knowledge base, evidence message, topic, expected answer, source hint, difficulty, and review count.
- `POST /api/chat/{sessionId}/assistant-turn` returns `weakPoints`, and `GET /api/chat/{sessionId}/weak-points` lists persisted rows.
- Frontend chat reads weak points through Spring API only.
- Tests and smoke checks verify persistence and retrieval.
