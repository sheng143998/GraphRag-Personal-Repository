# Review Prompt: Structured RAG Evaluation Case

Review the structured RAG evaluation case change for these concerns:

- Existing experiment evaluation calls with only `runId` and `expectedAnswer` remain backward compatible.
- Spring Boot forwards structured relevance ids only through the AI service gateway and does not implement RAG scoring logic.
- FastAPI uses the existing offline retrieval metrics for structured cases and falls back to the old heuristic when no case is supplied.
- Full-chain smoke proves the Advanced RAG evaluation response includes structured retrieval metric notes.
- Browser code still calls only Spring Boot `/api/*` endpoints.
