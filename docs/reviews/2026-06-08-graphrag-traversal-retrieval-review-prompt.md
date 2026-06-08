# Review Prompt: GraphRAG Traversal Retrieval

Please review the GraphRAG traversal retrieval changes with focus on:

- Repository contract consistency between in-memory and PostgreSQL modes.
- Whether `expansion_terms` are truly derived from persisted graph relationships, not only query extraction.
- Whether trace and citation metadata expose enough evidence to debug graph-aware retrieval.
- Whether Spring Boot remains outside AI retrieval logic and only persists/returns metadata.
- Regression risk around existing `graph-rag`, `advanced-rag`, and local full-chain smoke coverage.

Validation target:

- `ai-service/.venv/bin/python.exe -m pytest`
- `mvn test`
- `npm.cmd run typecheck`
- `npm.cmd run build`
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`
