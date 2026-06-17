# Heading Parent-Child Block-Type Chunking Review

## Scope

- Document ingest chunk strategy now uses a deterministic router instead of one global default:
  - long-form note documents (`tech_note`, `course_note`, `development_experience`, `project_experience`) with text-like files use `parent-child`;
  - code snippets, interview experience, job descriptions, and table files use `recursive-overlap`;
  - explicit metadata `chunk_strategy` / `chunkStrategy` still wins.
- Chunk metadata now includes heading-aware `embedding_text`, `embedding_text_mode`, `block_type`, `quality_score`, and `low_quality_reasons`.
- Embedding and embedding rebuild use `embedding_text` when present, while stored chunk `content` remains clean for citation display.
- In-memory and PostgreSQL retrieval use heading-aware search text and multiply scores by `quality_score`.
- Advanced RAG parent-child mode now fuses child hits by `parent_chunk_id`, preserving the best child hit while boosting parents with multiple matched children.
- RAG query/retrieve now classifies question type and sets `enable_parent_child_context`; broad conceptual/implementation/troubleshooting/interview/summary/comparison questions hydrate parent context, while fact lookup questions stay chunk-level unless explicitly overridden.

## Review Focus

- Check that child chunks have real `parent_chunk_id` for long-form note uploads, but code/table/exact documents do not get parent IDs by accident.
- Check that heading context is not duplicated into stored chunk content.
- Check that low-quality chunks are down-ranked, not hard-filtered.
- Check `parent_child_matched_child_chunk_ids` and `parent_child_aggregate_bonus` semantics in retrieved citation metadata.
- Check PostgreSQL SQL for safe handling of missing or non-numeric `quality_score`.
- Check that `question_type` and `enable_parent_child_context` trace attributes match the actual Advanced RAG behavior.

## Validation

- `.\.venv\bin\python.exe -m pytest tests/test_parent_child_chunker.py tests/test_advanced_rag_strategy.py tests/test_basic_rag_pipeline.py`
- `.\.venv\bin\python.exe -m pytest tests/test_agent_workflow.py`
