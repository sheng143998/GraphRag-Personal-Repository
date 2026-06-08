# Review Prompt: RAG Evaluator Answer Alignment

Review the evaluator change for these concerns:

- The deterministic heuristic penalizes obvious expected/generated answer mismatch without requiring a real LLM.
- Citation presence alone should no longer force a perfect grounded score.
- Empty or missing expected answers preserve the previous lightweight smoke behavior.
- Spring evaluation requests continue forwarding `expectedAnswer`, generated answer, citations, and context.
