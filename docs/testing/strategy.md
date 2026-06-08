# Testing Strategy

测试分为四类：

- 单元测试：隔离模块，不依赖外部服务。
- 外部依赖单元测试：依赖 PostgreSQL、Redis、模型服务等，但不跑完整应用。
- 集成测试：运行在真实部署环境上，不做 mock。
- Playwright E2E 测试：覆盖前后端完整交互。

## 第一阶段测试重点

- Python：chunker、parser、prompt builder、retriever adapter、trace schema。
- Java：service 规则、controller contract、AI client 错误处理、Flyway migration。
- 前端：API client、上传表单、聊天页面、引用来源展示。
- 数据库：pgvector extension、向量索引、metadata filter。

## 测试失败复盘

非显而易见或跨模块问题需要在 `docs/testing/failures/` 下记录：

- 问题现象
- 复现步骤
- 根因
- 修复方案
- 补充的回归测试
- 下次排查建议
## 2026-06-08 Current Automated Verification

- Frontend: `npm.cmd run typecheck`, `npm.cmd run build`.
- Backend: `mvn test`; current service-level coverage includes RAG bridge persistence/failure cases and async document ingest success/failure cases.
- AI service: `.venv\bin\python.exe -m pytest`; current coverage includes Basic RAG, Advanced RAG, OpenAI-compatible adapter parsing, and offline strategy comparison metrics.
- Full-chain local smoke: `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1 -SkipBuild`.
- Direct smoke script: `python smoke_test.py`; accepts `SMOKE_BASE_URL`, `SMOKE_AI_BASE_URL`, and `SMOKE_TIMEOUT`.

The full-chain smoke now treats RAG query failure as a hard failure and includes an `advanced-rag` trace assertion for completed status, citation presence, and stored `rewrittenQuery`.

## 2026-06-08 Agent Workflow Validation

- AI pytest covers question classification, automatic strategy selection, RAG execution, citations, and workflow step trace metadata.
- Backend Maven tests cover the Spring Boot `/api/agent/invoke` bridge request/response mapping.
- Local full-chain smoke covers Spring Boot -> FastAPI Agent invocation and now passes 47/47 checks.

## 2026-06-08 GraphRAG Validation

- AI pytest covers deterministic GraphRAG entity/relationship extraction, graph query augmentation, trace attributes, and citation graph metadata.
- Frontend typecheck/build verifies the `GraphRAG` strategy option is available to the workbench.
- Local full-chain smoke covers Spring Boot -> FastAPI `strategyName=graph-rag` invocation and now passes 54/54 checks.

## 2026-06-08 GraphRAG Persistence Validation

- Flyway migration `V202606081300__create_graph_facts.sql` is included in the backend package and executed during local Spring Boot startup.
- AI pytest covers persisted graph fact lookup through the in-memory repository.
- Full-chain smoke remains 54/54 after adding graph fact tables and ingest-time graph extraction.

## 2026-06-08 Graph Facts Query Validation

- Backend Maven tests now include `GraphFactServiceTest`, covering entity filter normalization, DTO mapping, and the 100-row query limit.
- Frontend typecheck/build covers the new `/graph` workbench page and `frontend/src/api/graph.ts`.
- The local full-chain script now runs the AI service in database-backed mode (`AI_RAG_USE_DATABASE=true`) so AI ingest writes graph facts into the same PostgreSQL database that Spring Boot reads.
- Local full-chain smoke now covers `GET /api/graph/facts` and `GET /api/graph/facts?entity=GraphRAG`, passing 60/60 checks with persisted entity and relationship counts.

## 2026-06-08 GraphRAG Traversal Retrieval Validation

- AI pytest covers one-hop graph expansion terms and traversal relationships in GraphRAG trace/citation metadata.
- `smoke_test.py` now checks Spring Boot RAG run retrieval metadata for `graph_expansion_terms` and `graph_traversal_relationships`.
- Local full-chain smoke should pass 62/62 checks after this change.

## 2026-06-08 Assistant Turn Chat Flow Validation

- Backend Maven tests include `AssistantTurnServiceTest`, covering user/assistant message persistence and Agent request context propagation.
- Frontend typecheck/build covers the new `sendAssistantTurn()` API wiring and chat store flow.
- `smoke_test.py` now covers `POST /api/chat/{sessionId}/assistant-turn`, assistant workflow metadata, persisted messages, and feedback submission against the assistant message.

## 2026-06-08 Agent Follow-Up Questions Validation

- AI pytest covers the new `generate_follow_up_questions` workflow step, trace attribute, and three generated follow-up prompts.
- Backend Maven tests cover `follow_up_questions` to `followUpQuestions` DTO propagation through Agent and assistant-turn services.
- Frontend typecheck/build covers clickable follow-up prompts in the chat workbench.
- `smoke_test.py` now verifies assistant-turn returns at least three non-empty `followUpQuestions` through Spring Boot.
- Local full-chain smoke now passes 74/74 checks, including direct Agent and assistant-turn follow-up trace assertions.
