# Heading Parent-Child Block-Type Chunking

## Goal

Implement three chunking and retrieval improvements for the AI service:

- Include heading path and section context in embedding text.
- Route ingest chunking by document type and file type instead of using one global default.
- Add `block_type` and low-quality metadata so retrieval can down-rank noisy chunks such as image captions, tables of contents, prompt examples, and weak OCR.
- Expand child hits to parent context during retrieval so answers are complete when child chunks match precisely.
- Route query-time Parent-Child context by question type, so broad explanation questions get parent context while fact lookup questions stay precise.

## Scope

- AI service chunkers and ingest service.
- AI service database repository and retriever behavior.
- AI service RAG query/retrieve routing options.
- Focused Python tests for chunk metadata, embedding text, default strategy, and parent aggregation.

## Non-Goals

- No destructive migration or rewriting existing uploaded documents in place.
- No Spring Boot business logic change unless an API contract forces it.
- No frontend visual change.

## Validation

- Run focused AI service tests for chunking and retrieval.
- Run existing strategy evaluator tests if affected.
- Confirm long-form note documents write real parent chunk IDs for child rows.
- Confirm code/table/exact documents stay on recursive-overlap unless explicitly overridden.
- Confirm fact lookup questions skip Parent-Child context by default and explicit options can enable it.
