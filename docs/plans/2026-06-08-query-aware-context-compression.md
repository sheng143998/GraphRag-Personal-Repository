# 2026-06-08 Query-Aware Context Compression

## Goal

Reduce noisy parent-child retrieval context before rerank and generation while preserving the hit child evidence and query-matched sentences.

## Scope

- Add deterministic query-aware sentence packing inside FastAPI parent-child hydration.
- Preserve existing parent-child and neighbor-window behavior for selecting context source chunks.
- Store compression metadata on each citation: mode, original chars, compressed chars, and ratio.
- Add Advanced RAG trace aggregation for compression counts and character totals.
- Extend AI tests and full-chain smoke assertions.

## Out Of Scope

- LLM-based compression.
- UI controls for compression settings.
- Docker validation.
