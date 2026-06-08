# Agent Review Cards Review Prompt

Please review the Agent review cards change with focus on:

- `review_cards` is generated only in the AI Agent workflow and recorded in trace attributes.
- Spring Boot maps FastAPI `review_cards` to Java/JSON `reviewCards` without adding RAG or Agent logic.
- Assistant-turn responses include `reviewCards` alongside messages, follow-up questions, study plan, workflow steps, and trace.
- Frontend chat displays `reviewCards` from Spring responses only.
- Tests and smoke checks verify both direct Agent invocation and assistant-turn propagation.
