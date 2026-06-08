# RAG Evaluator Answer Alignment Plan

## Goal

Make the local deterministic RAG evaluator less misleading by penalizing generated answers that conflict with the optional expected answer, even when citations are present.

## Scope

- Keep the evaluator offline and deterministic.
- Add token-overlap answer alignment and citation support heuristics.
- Add AI pytest coverage for matched versus mismatched answers with the same citation set.
- Add a Spring unit assertion that `expectedAnswer` is forwarded to FastAPI evaluation requests.

## Validation

- AI pytest for evaluator behavior.
- Backend Maven tests for request bridge mapping.
- Full-chain smoke continues to validate persisted evaluation and summary aggregation.
