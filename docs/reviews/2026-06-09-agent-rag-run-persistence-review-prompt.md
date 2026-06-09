# 2026-06-09 Agent RAG Run Persistence Review Prompt

## Review Focus

- `ai-service/app/agents/workflow.py`
  - Confirm nested RAG trace is captured without changing RAG strategy logic.
  - Confirm rewritten query is exposed in Agent trace attributes and workflow step payload.

- `ai-service/app/schemas/agent.py`
  - Confirm `rag_trace` is additive and optional.

- `backend-java/src/main/resources/db/migration/V202606092045__add_rag_run_trace_payload.sql`
  - Confirm migration is additive and safe for existing rows.

- `backend-java/src/main/java/com/example/agentknowledge/service/RagRunRecorder.java`
  - Confirm it only persists returned trace/citation data and does not implement retrieval logic.
  - Confirm citations are saved in rank order and linked to document/chunk when present.

- `backend-java/src/main/java/com/example/agentknowledge/service/AssistantTurnService.java`
  - Confirm assistant-turn creates a RAG run after Agent response and before returning the turn response.

## Verification

- `python -m compileall app`
- `uv run --isolated --with pytest --with fastapi==0.95.2 --with pydantic==1.10.26 pytest tests/test_agent_workflow.py -q`
- `npm run typecheck`
- `mvn.cmd -q -DskipTests compile`
- `mvn.cmd -q "-Dtest=AgentServiceTest,AssistantTurnServiceTest,RagRunRecorderTest,RagServiceTest" test`
