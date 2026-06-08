# GraphRAG Offline Evaluation Fixture Plan

## Goal

Add deterministic offline evaluation coverage showing when `graph-rag` should outperform generic `advanced-rag` for entity/relationship questions.

## Scope

- Reuse the existing offline strategy comparison evaluator.
- Add graph relationship and graph expansion cases to AI pytest.
- Avoid database, Docker, LLM, embedding, and reranker dependencies.
- Keep scoring logic unchanged unless the fixture reveals an evaluator limitation.

## Validation

- `ai-service/.venv/bin/python.exe -m pytest tests -q`
- Full-chain smoke remains the runtime integration guard for GraphRAG trace and persisted summary behavior.
