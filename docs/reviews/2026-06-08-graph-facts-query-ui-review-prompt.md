# Review Prompt: Graph Facts Query UI

Please review the GraphRAG fact inspection changes with priority on:

- Spring Boot remains a read-only business/API bridge for graph facts and does not implement graph extraction or retrieval logic.
- `GET /api/graph/facts` handles both unfiltered and entity-filtered requests against PostgreSQL.
- JSONB mappings are stable for graph entity aliases and metadata.
- The Vue page calls Spring Boot only through `frontend/src/api/graph.ts`.
- The full-chain local script intentionally runs the AI service in database-backed mode so persisted graph facts are verifiable from Spring Boot.

Validation already run:

- `ai-service/.venv/bin/python.exe -m pytest`
- `mvn test`
- `npm.cmd run typecheck`
- `npm.cmd run build`
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`
