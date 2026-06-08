# 2026-06-08 GraphRAG Evaluation Metrics

## Goal

Make GraphRAG retrieval quality visible in the RAG evaluator, not only in trace and citation metadata.

## Scope

- Read GraphRAG citation metadata in the FastAPI evaluator.
- Score entity coverage, relationship evidence hit, and expansion-term hit.
- Add evaluator notes with the GraphRAG metric breakdown.
- Blend GraphRAG metadata score into retrieval score when graph metadata is present.
- Extend AI regression tests and full-chain smoke coverage.

## Out Of Scope

- LLM-based graph extraction scoring.
- Spring Boot scoring logic.
- UI changes for GraphRAG metric display.
- Docker validation.
