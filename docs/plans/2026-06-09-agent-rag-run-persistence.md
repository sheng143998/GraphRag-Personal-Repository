# 2026-06-09 Agent RAG Run Persistence

## Background

Knowledge-base chat uses `/api/chat/{sessionId}/assistant-turn`, which calls FastAPI `/ai/agent/invoke`. Before this change, Agent citations were saved in `chat_messages.citations`, but the internal RAG query did not create `rag_runs` or `rag_retrieval_results`, so a trace id could not show rewritten query and top-k chunks from the RAG run table.

## Scope

- Expose the nested RAG trace from FastAPI Agent responses as `rag_trace`.
- Add `trace_attributes` and `trace_steps` to `rag_runs`.
- Persist assistant-turn internal RAG runs with question, rewritten query, answer, final context, trace payload, and top-k citation chunks.
- Keep RAG execution logic inside FastAPI; Spring Boot only stores returned observability data.

## Result

After restarting services and running Flyway migration, a knowledge-base chat question should produce:

- `chat_messages`: user and assistant messages with the same trace id.
- `rag_runs`: one completed run with the same trace id, rewritten query, trace attributes, and trace steps.
- `rag_retrieval_results`: top-k chunks ordered by rank.
