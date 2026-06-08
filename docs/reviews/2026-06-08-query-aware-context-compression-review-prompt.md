# Review Prompt: Query-Aware Context Compression

Please review the deterministic context compression implementation for Advanced RAG.

Focus areas:

- Compression must run only inside the AI service RAG boundary.
- Parent-child hydration should still report the same `context_source_chunk_ids`.
- Hit child evidence must not be dropped when parent context is long.
- Metadata should be useful for evaluation: original chars, compressed chars, ratio, and compression mode.
- Trace payload should expose aggregate compression statistics.
- Existing flat chunk neighbor fallback should continue to work.

Validation commands:

```powershell
cd ai-service
.\.venv\bin\python.exe -m pytest tests/test_advanced_rag_strategy.py -q
.\.venv\bin\python.exe -m pytest tests -q
```

```powershell
python -m py_compile smoke_test.py
powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1
```
