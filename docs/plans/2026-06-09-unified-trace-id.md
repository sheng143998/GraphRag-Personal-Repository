# 2026-06-09 Unified Trace Id

## Background

Knowledge-base chat currently produces different trace ids across the browser refresh calls, Spring Boot logs, FastAPI Agent trace, and nested RAG trace. This makes it hard to inspect one user question end to end.

## Scope

- Reuse incoming `X-Trace-Id` inside FastAPI `TraceBuilder`.
- Keep `run_id` unique for each internal operation.
- Add frontend chat flow trace propagation so one user action can reuse the same request trace id across assistant-turn and follow-up refresh calls.
- Do not move RAG logic into Spring Boot.

## Expected Result

For one knowledge-base question, the same trace id should appear in:

- Browser request headers and response headers.
- Spring Boot `TraceIdFilter` logs.
- Spring Boot `AiServiceClient` logs.
- FastAPI request middleware logs.
- FastAPI Agent trace.
- FastAPI nested RAG trace.
