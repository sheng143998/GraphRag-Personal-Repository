# 2026-06-08 Offline RAG Strategy Comparison

## Scope

Added a deterministic offline evaluator for comparing retrieval outputs without calling the RAG main pipeline, database, LLM, embedding, or reranker adapters.

## Metrics

- `recall_at_k`: relevant retrieved items in top K divided by expected relevant items.
- `precision_at_k`: relevant retrieved items in top K divided by K.
- `mrr`: reciprocal rank of the first relevant item in top K.
- `citation_hit`: whether returned citations include an expected citation chunk, falling back to relevant source matching when no expected citation set is provided.

## Fixture Coverage

- Single-case metric calculation covers recall, precision, MRR, and citation hit.
- Strategy comparison fixture compares `basic-rag` and `advanced-rag` over fixed retrieval/citation lists.
- The fixture expects `advanced-rag` to outperform `basic-rag` on all four metrics.
- Unknown case references fail fast with `ValueError`.

## Verification

- Command: `.venv\bin\python.exe -m pytest`
- Result: 10 passed.
