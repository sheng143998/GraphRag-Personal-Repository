# Review Prompt: Configurable Hybrid Retrieval

Please review the request-level hybrid retrieval weighting implementation.

Focus areas:

- `retrieval_options` should not be mixed with business `metadata_filters`.
- Default retrieval must remain equivalent to 0.7 vector / 0.3 keyword.
- CamelCase and snake_case option names should both work.
- Invalid or zero weights should fall back safely.
- Spring Boot should only bridge the new option and not implement RAG logic.
- Full-chain smoke should verify that configured weights are visible in persisted retrieval metadata.

Validation commands:

```powershell
cd ai-service
.\.venv\bin\python.exe -m pytest tests/test_advanced_rag_strategy.py -q
```

```powershell
mvn test -f backend-java/pom.xml
npm.cmd --prefix frontend run typecheck
python -m py_compile smoke_test.py
```
