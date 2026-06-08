# Review Prompt: Iterative Test Hardening

Please review the iterative test hardening changes with focus on:

- Whether full-chain smoke should require RAG query success now that the local chain is stable.
- Whether the Advanced RAG HTTP assertions are sufficient to catch regressions in strategy dispatch and trace persistence.
- Whether `RagServiceTest` adequately covers metadata filter forwarding, rewritten query persistence, and citation id mismatch tolerance.
- Whether any additional cleanup is needed for smoke-created chat sessions or feedback records.

Verification commands run:

- `.venv/bin/python.exe -m pytest`
- `npm.cmd run typecheck`
- `npm.cmd run build`
- `mvn test`
- `python smoke_test.py`
