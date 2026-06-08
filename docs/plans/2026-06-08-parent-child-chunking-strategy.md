# Parent-Child Chunking Strategy Plan

Date: 2026-06-08

## Scope

Add an opt-in parent-child chunking strategy so ingest can produce parent chunks and child chunks with `parent_chunk_id`, completing the path needed by the real parent-context hydration work.

## Implementation

- Keep `SimpleChunker` as the default flat chunking behavior.
- Add `ParentChildChunker` that emits parent chunks and child chunks with stable `parent_chunk_id` references.
- Select parent-child chunking when ingest metadata contains `chunk_strategy=parent-child`.
- Treat parent chunks as context carriers: store them, but skip them for retrieval, embeddings, and graph fact extraction.
- Clamp metadata-provided parent/child chunk sizes to avoid explosive or degenerate chunking.

## Validation

- AI: `.\.venv\bin\python.exe -m pytest tests/test_parent_child_chunker.py tests/test_advanced_rag_strategy.py tests/test_strategy_comparison_evaluator.py -q` passed with 15 tests.
- AI: `.\.venv\bin\python.exe -m pytest tests -q` passed with 22 tests.
- Full-chain: `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1` passed with 131/131 smoke checks.
