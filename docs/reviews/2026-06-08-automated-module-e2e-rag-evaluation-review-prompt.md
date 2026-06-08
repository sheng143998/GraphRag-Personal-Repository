# Review Prompt: Automated Module, E2E, and RAG Evaluation

Please review the 2026-06-08 automated testing changes with focus on:

- Whether AI service tests correctly isolate external model providers and database dependencies.
- Whether Advanced RAG coverage meaningfully verifies query rewrite, metadata filters, multi-query fusion, parent-child context hydration, reranking, and evaluation traces.
- Whether replacing corrupted query transformer strings with ASCII synonyms changes intended retrieval behavior.
- Whether pytest cache relocation is appropriate for this workspace.
- Whether the full-chain blocker documentation is accurate and actionable.

Verification commands already run:

- `npm.cmd run typecheck`
- `npm.cmd run build`
- `mvn test`
- `.venv/bin/python.exe -m pytest`
- `python smoke_test.py` (failed because services/dependencies were unavailable)
