# RAG Evaluation Dataset Schema Review

## Scope

- Updated `datasets/processed/rag-folder-evaluation-cases-20260616.json` to the current layered evidence schema.
- Added `requiredChunkIds`, `supportingChunkIds`, `acceptableChunkIds`, and `citationChunkIds` for all 18 cases.
- Kept compatibility fields populated: `relevantChunkIds`, `relevantDocumentIds`, and `expectedCitationChunkIds`.

## Review Focus

- Verify `requiredChunkIds` only contains core evidence needed to answer the case.
- Verify `supportingChunkIds` contains useful but non-essential context.
- Verify `acceptableChunkIds` is not over-expanded, because the current evaluator includes it in chunk targets.
- Verify `citationChunkIds` matches the chunks that should be cited by generated answers.

## Validation

- JSON parse succeeded for 18 cases.
- All required layered fields are present and list-typed.
- `requiredChunkIds` and `citationChunkIds` are non-empty for every case.
- `relevantChunkIds` equals the ordered union of required + supporting + acceptable chunks.
- `expectedCitationChunkIds` mirrors `citationChunkIds`.
- Database existence check passed against PostgreSQL `agent_knowledge`: 65 unique chunk IDs and 22 unique document IDs all exist.

## Notes

- The dataset file is ignored by `.gitignore` via `datasets/processed/*`, so it will not appear in normal `git status`.
- Temporary validation outputs were written under `.tmp/` and are not part of the review artifact.
