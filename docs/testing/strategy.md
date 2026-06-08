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
