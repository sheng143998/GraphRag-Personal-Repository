# Review Prompt: Assistant Turn Chat Flow

Please review the assistant-turn chat flow with focus on:

- Spring Boot only performs business orchestration, persistence, and AI bridge calls.
- FastAPI remains responsible for classification, strategy selection, RAG execution, and workflow details.
- `POST /api/chat/{sessionId}/assistant-turn` persists exactly one user message and one assistant message for a successful turn.
- Agent request context includes `knowledgeBaseId`, `sessionId`, and the newly saved user `messageId`.
- Frontend chat uses the new Spring `/api/chat/{sessionId}/assistant-turn` API instead of calling FastAPI or directly orchestrating multiple backend calls.
- Smoke coverage proves the full turn and subsequent feedback path.

Validation target:

- `ai-service/.venv/bin/python.exe -m pytest`
- `mvn test`
- `npm.cmd run typecheck`
- `npm.cmd run build`
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`
