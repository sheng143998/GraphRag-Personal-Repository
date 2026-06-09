# 2026-06-09 Unified Trace Id Review Prompt

## Review Focus

- `ai-service/app/core/tracing.py`
  - Confirm `TraceBuilder` reuses the request-scoped trace id and keeps `run_id` unique.
  - Confirm context variable reset is handled by middleware and does not leak across requests.

- `ai-service/app/main.py`
  - Confirm FastAPI generates a trace id only when `X-Trace-Id` is missing.
  - Confirm response headers include `X-Trace-Id`.

- `frontend/src/api/chat.ts`
  - Confirm chat APIs pass optional `traceId` through request options without changing payload contracts.

- `frontend/src/stores/workbench.ts`
  - Confirm one question action reuses the same trace id across assistant-turn and follow-up refresh calls.

## Verification

- `python -m compileall app`
- `uv run --isolated --with pytest --with fastapi==0.95.2 --with pydantic==1.10.26 pytest tests/test_agent_workflow.py -q`
- `npm run typecheck`
- `mvn.cmd -q -DskipTests compile`
