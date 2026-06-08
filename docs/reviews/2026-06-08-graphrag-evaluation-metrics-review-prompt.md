# Review Prompt: GraphRAG Evaluation Metrics

Please review the GraphRAG evaluator metric refinement.

Focus areas:

- GraphRAG scoring must remain inside FastAPI.
- Existing structured retrieval metrics should remain backward compatible.
- Graph metrics should use persisted citation metadata rather than re-running graph extraction.
- Notes should clearly expose entity coverage, relationship hit, and expansion term hit.
- Full-chain smoke should prove Spring persisted run metadata reaches the evaluator path.

Validation commands:

```powershell
cd ai-service
.\.venv\bin\python.exe -m pytest tests/test_advanced_rag_strategy.py tests/test_strategy_comparison_evaluator.py -q
.\.venv\bin\python.exe -m pytest tests -q
```

```powershell
python -m py_compile smoke_test.py
powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1
```
