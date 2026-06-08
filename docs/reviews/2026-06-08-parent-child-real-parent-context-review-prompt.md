# Parent-Child Real Parent Context Review Prompt

Date: 2026-06-08

Review the AI service parent-child context hydration change.

## Files

- `ai-service/app/schemas/ingest.py`
- `ai-service/app/db/repositories.py`
- `ai-service/tests/test_advanced_rag_strategy.py`
- `docs/plans/2026-06-08-parent-child-real-parent-context.md`
- `docs/testing/strategy.md`
- `docs/handoff/CURRENT_STATE.md`
- `PROJECT_CONTEXT.md`

## Questions

- Does `ChunkRecord.parent_chunk_id` remain optional so existing flat chunking still works?
- Does PostgreSQL save/read preserve `parent_chunk_id` without changing the Spring API contract?
- Does parent context hydration prefer parent + same-parent child chunks when available?
- Does neighbor-window fallback still work when no parent is present?
- Does the new test prove the real parent-child path separately from the existing Advanced RAG fallback test?

## Validation Snapshot

- `.\.venv\bin\python.exe -m pytest tests/test_advanced_rag_strategy.py tests/test_strategy_comparison_evaluator.py -q`: passed with 11 tests.
- `.\.venv\bin\python.exe -m pytest tests -q`: passed with 18 tests.
- Full-chain local smoke: passed with 131/131 checks.
