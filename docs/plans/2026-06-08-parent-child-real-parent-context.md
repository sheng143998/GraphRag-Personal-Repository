# Parent-Child Real Parent Context Plan

Date: 2026-06-08

## Scope

Improve Advanced RAG parent-child retrieval so it uses real `parent_chunk_id` relationships when they are present, while keeping the neighbor-window fallback for existing simple chunks.

## Implementation

- Add optional `parent_chunk_id` to AI service `ChunkRecord`.
- Persist `parent_chunk_id` into `document_chunks` from the AI repository when chunk records include it.
- Load `parent_chunk_id` back from PostgreSQL-backed chunk reads.
- In in-memory and PostgreSQL repositories, hydrate parent-child context from the parent chunk plus same-parent child chunks before falling back to the neighbor window.
- Keep SimpleChunker unchanged; it still emits flat chunks until a dedicated parent chunker is introduced.

## Validation

- AI: `.\.venv\bin\python.exe -m pytest tests/test_advanced_rag_strategy.py tests/test_strategy_comparison_evaluator.py -q` passed with 11 tests.
- AI: `.\.venv\bin\python.exe -m pytest tests -q` passed with 18 tests.
- Full-chain: `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1` passed with 131/131 smoke checks.
