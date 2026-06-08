# 2026-06-08 Advanced RAG Evaluation

## Scope

This evaluation used deterministic offline fixtures first, then a real backend-to-AI HTTP smoke path with FastAPI running in stub/in-memory mode and Spring Boot using the local PostgreSQL credentials from `.env`.

## Coverage

- Query rewrite expands RAG-related terms into retrieval-oriented variants.
- Multi-query expansion creates distinct original, rewritten, technical, and implementation-focused query variants.
- Metadata filters restrict retrieval to the requested topic.
- Parent-child mode hydrates neighbor chunk context.
- Rerank scores are attached and used for final ordering.
- Trace steps expose `query_rewrite`, `multi_query_expand`, `fusion`, `parent_child_context`, and `rerank`.
- Heuristic evaluation returns grounded and retrieval scores when citations are present.
- HTTP smoke through `/api/rag/query` accepts `strategyName=advanced-rag`, stores a completed run, and preserves the rewritten query.

## Result

- AI service pytest: 7 passed.
- Advanced RAG focused tests: 2 passed.
- Heuristic RAG evaluation test: passed.
- Advanced RAG HTTP smoke: completed with one citation and a populated rewritten query.

## Optimization Applied

- Replaced corrupted multilingual synonym strings with stable ASCII query rewrite terms.
- Kept the rule-based rewrite simple and deterministic so it can run in offline CI and local smoke without model access.
- Preserved model-backed extension points through the existing embedding, rerank, and generator adapters.

## Remaining Evaluation Gap

The next evaluation should compare basic-rag and advanced-rag over a fixed question set with expected citations and score deltas.
