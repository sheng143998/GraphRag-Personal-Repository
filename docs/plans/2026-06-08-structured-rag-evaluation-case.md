# Structured RAG Evaluation Case Plan

## Goal

Allow persisted RAG experiment evaluations to use structured retrieval relevance data instead of relying only on citation count.

## Scope

- Add optional evaluation case fields to Spring Boot experiment evaluation requests.
- Pass the structured case through to FastAPI without changing the existing simple `expectedAnswer` flow.
- Reuse the deterministic offline evaluator metrics for online evaluation requests when relevant chunk/document ids are supplied.
- Extend the non-Docker full-chain smoke so Advanced RAG evaluation proves the structured metrics path is exercised.

## Validation

- `.\.venv\bin\python.exe -m pytest tests/test_advanced_rag_strategy.py tests/test_strategy_comparison_evaluator.py -q`
- `mvn test`
- `npm.cmd run typecheck`
- `npm.cmd run build`
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`
