# 2026-06-09 Agent RAG Run Persistence Notes

## Observations

- Existing assistant-turn chat records already stored citations, so old traces can recover top-k from `chat_messages.citations`, but they cannot backfill `rag_runs` without re-running the question.
- New persistence requires the Spring Boot service to restart and Flyway to apply `V202606092045__add_rag_run_trace_payload.sql`.
- Python tests still need `uv run --isolated ...` because the existing `ai-service/.venv/bin/python.exe` is a MINGW virtualenv and not suitable for Windows execution.
- Pytest emitted the known cache warning under `.tmp/pytest-cache`; targeted tests passed.

## Passed Commands

```powershell
python -m compileall app
uv run --isolated --with pytest --with fastapi==0.95.2 --with pydantic==1.10.26 pytest tests/test_agent_workflow.py -q
npm run typecheck
mvn.cmd -q -DskipTests compile
mvn.cmd -q "-Dtest=AgentServiceTest,AssistantTurnServiceTest,RagRunRecorderTest,RagServiceTest" test
```
