# Parent-Child Chunking Strategy Review Prompt

Date: 2026-06-08

Review the optional parent-child chunking strategy for AI ingest.

## Files

- `ai-service/app/rag/chunkers/base.py`
- `ai-service/app/services/ingest_service.py`
- `ai-service/app/rag/retrievers/base.py`
- `ai-service/app/db/repositories.py`
- `ai-service/tests/test_parent_child_chunker.py`
- `docs/plans/2026-06-08-parent-child-chunking-strategy.md`
- `docs/testing/strategy.md`
- `docs/handoff/CURRENT_STATE.md`
- `PROJECT_CONTEXT.md`

## Questions

- Does default ingest still use flat `SimpleChunker` behavior?
- Does metadata `chunk_strategy=parent-child` produce parent chunks plus children with valid `parent_chunk_id`?
- Are parent chunks excluded from retrieval, embeddings, and graph fact extraction so child hits can hydrate parent context?
- Are metadata-provided chunk sizes bounded?
- Does the query-level test prove a parent-child ingest can return `parent_child_mode=parent-child`?

## Validation Snapshot

- `.\.venv\bin\python.exe -m pytest tests/test_parent_child_chunker.py tests/test_advanced_rag_strategy.py tests/test_strategy_comparison_evaluator.py -q`: passed with 15 tests.
- `.\.venv\bin\python.exe -m pytest tests -q`: passed with 22 tests.
- Full-chain local smoke: passed with 131/131 checks.
