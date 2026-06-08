# 2026-06-08 Configurable Hybrid Retrieval

## Goal

Make Advanced RAG hybrid retrieval weights configurable per request without changing the default 0.7 vector / 0.3 keyword behavior.

## Scope

- Add `retrieval_options` to AI RAG request context.
- Pass `retrievalOptions` through Spring Boot `/api/rag/query`.
- Allow frontend chat requests to carry retrieval options.
- Normalize `vectorWeight` / `keywordWeight` and snake_case equivalents in the AI repository.
- Persist `vector_score`, `keyword_score`, `vector_weight`, and `keyword_weight` in citation metadata.
- Add unit and full-chain smoke assertions for the new option path.

## Out Of Scope

- UI controls for editing retrieval weights.
- RRF or other fusion algorithms.
- Docker validation.
