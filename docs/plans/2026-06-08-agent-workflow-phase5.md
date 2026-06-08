# Phase 5 Agent Workflow

Date: 2026-06-08

## Scope

- Build the first verifiable Agent orchestration loop without Docker.
- Keep AI orchestration inside `ai-service/`.
- Keep Spring Boot responsible for API bridging only.
- Do not start GraphRAG in this batch.

## Completed

- Added a node-style study agent workflow in `ai-service/app/agents/workflow.py`.
- The workflow executes `classify_question -> select_rag_strategy -> retrieve_and_generate -> cite_sources -> generate_follow_up_questions`.
- The workflow auto-routes implementation, troubleshooting, and interview questions to `advanced-rag` unless an explicit non-basic strategy is provided.
- `/ai/agent/invoke` now returns `question_type`, `selected_strategy_name`, `workflow_steps`, and `follow_up_questions` while preserving `output`, `citations`, and `trace`.
- Added Spring Boot `/api/agent/invoke` bridge to FastAPI `/ai/agent/invoke`.
- Added full-chain smoke coverage for Spring Boot -> FastAPI Agent invocation.

## Verification

- `ai-service/.venv/bin/python.exe -m pytest`: 12 passed.
- `mvn test`: 6 passed.
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`: 47/47 smoke checks passed.

## Notes

- This batch intentionally implements a local node-style workflow instead of adding a new `langgraph` dependency. The node boundaries mirror the planned LangGraph graph, so a later dependency-backed graph can replace the runner without changing the public API.
