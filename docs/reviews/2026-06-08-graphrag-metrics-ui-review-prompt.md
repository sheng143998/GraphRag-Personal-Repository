# Review Prompt: GraphRAG Metrics UI

Please review the frontend GraphRAG metric display.

Focus areas:

- The UI should parse evaluator notes defensively and remain stable for non-GraphRAG evaluations.
- Existing experiment evaluation and comparison flows should remain unchanged.
- The comparison table should remain scannable on desktop and horizontally scrollable on narrow screens.
- Browser code should continue calling only Spring Boot `/api/*` endpoints.
- Mock data should expose a GraphRAG metric example without changing live API contracts.

Validation commands:

```powershell
npm.cmd --prefix frontend run typecheck
npm.cmd --prefix frontend run build
powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1
```
