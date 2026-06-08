# Agent Follow-Up Questions Review Prompt

Please review the assistant follow-up questions change with focus on:

- `follow_up_questions` is generated only in the AI Agent workflow and is included in the Agent trace attributes.
- Spring Boot maps FastAPI `follow_up_questions` to Java `followUpQuestions` without changing RAG/Agent behavior.
- `POST /api/chat/{sessionId}/assistant-turn` returns follow-up questions alongside the persisted user and assistant messages.
- Frontend chat uses the Spring assistant-turn response and does not call FastAPI directly.
- Tests cover AI workflow generation, Spring DTO/service propagation, frontend type safety, and full-chain smoke response assertions.
