# Agent Study Plan Review Prompt

Please review the Agent study plan change with focus on:

- `study_plan` is generated inside the AI Agent workflow and recorded in trace attributes.
- Spring Boot maps FastAPI `study_plan` to Java/JSON `studyPlan` without adding RAG logic.
- Assistant-turn responses include `studyPlan` alongside messages, follow-up questions, workflow steps, and trace.
- Frontend chat displays `studyPlan` from Spring responses only.
- Tests and smoke checks verify both direct Agent invocation and assistant-turn propagation.
