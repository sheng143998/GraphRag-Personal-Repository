# 当前交接状态
更新时间：2026-06-08

## 当前正在做什么

已完成 Phase 4 Advanced RAG 工程闭环第一版，并完成 OpenAI-compatible LLM / Embedding / Rerank 真实模型 adapter 接入。用户要求项目先完成到 Advanced RAG，后续 LangGraph、GraphRAG、复习/面试辅助暂不继续。

## 本轮已完成的变更

### Python AI 服务

- `ai-service/app/rag/query_transformers/base.py`（新建）— 规则型 `RuleBasedQueryRewriter` 与 `RuleBasedMultiQueryExpander`，用于无真实 LLM 情况下验证 query rewrite / multi-query 工程链路。
- `ai-service/app/rag/query_transformers/__init__.py`（新建）— query transformer 包入口。
- `ai-service/app/rag/strategies/advanced.py`（新建）— `AdvancedRagStrategy`，支持 `hybrid-rerank`、`metadata-filter`、`parent-child`、`advanced-rag`。
- `ai-service/app/services/rag_service.py`（修改）— 从固定 `BasicRagStrategy` 改为策略分发：`basic-rag` 走基础策略，其余 Phase 4 策略走 AdvancedRagStrategy。
- `ai-service/app/db/repositories.py`（修改）— 增加 `hydrate_parent_context()`，PostgreSQL / InMemory 均支持邻近 chunk window fallback，metadata 写入 `parent_child_mode` 与 `context_source_chunk_ids`。
- `ai-service/app/core/config.py`（修改）— 自动读取根目录 `.env`，新增 LLM / Embedding / Rerank adapter 配置，并支持 `MODEL_MAX_RETRIES`。
- `ai-service/app/services/adapters/openai_compatible.py`（新建）— OpenAI-compatible LLM、Embedding、Rerank HTTP adapter；对网络异常、超时、429 与 5xx 做轻量指数退避重试。
- `ai-service/app/services/adapters/registry.py`（修改）— 根据 `.env` 自动选择真实 adapter 或 fallback stub。

### Java 后端

- `backend-java/src/main/java/.../dto/rag/RagQueryRequest.java`（修改）— 新增 `metadataFilters`，并要求 `knowledgeBaseId` 非空。
- `backend-java/src/main/java/.../client/dto/AiRagQueryRequest.java`（确认）— 通过 `metadata_filters` 透传到 Python。
- `backend-java/src/main/java/.../client/dto/AiTraceMetadata.java`（修改）— 新增 `attributes`，用于接收 Python trace attributes。
- `backend-java/src/main/java/.../client/AiServiceClient.java`（修改）— mock trace 构造补齐 `attributes`。
- `backend-java/src/main/java/.../service/RagService.java`（修改）— metadataFilters 空值安全透传；保存 Python trace attributes 中的 `rewritten_query` 到 `rag_runs.rewritten_query`；retrieval result rank 改为顺序计数。

### 前端

- `frontend/src/types/index.ts`（修改）— `ChatRequest` 新增 `knowledgeBaseId`、`messageId`、`retrieverType`、`metadataFilters`、`topK`。
- `frontend/src/api/chat.ts`（修改）— `sendChatMessage()` 透传 `knowledgeBaseId/sessionId/messageId/retrieverType/metadataFilters/topK` 到 `/api/rag/query`。
- `frontend/src/utils/mock-data.ts`（修改）— 策略列表补齐并对齐 `basic-rag`、`hybrid-rerank`、`metadata-filter`、`parent-child`、`advanced-rag`。
- `frontend/src/stores/workbench.ts`（修改）— 提问前校验默认/选中知识库，避免向 Python 发送空 knowledgeBaseId。

### 环境配置

- `.env`（本地忽略文件）— 已配置用户提供的 DashScope OpenAI-compatible LLM / Embedding / Rerank 信息；真实密钥只保留在本地 `.env`。
- `.env.example`（可提交示例）— 补充模型 adapter 占位变量，不包含真实密钥。
- 根据阿里百炼文档修正：
  - `text-embedding-v4` 使用 `compatible-mode/v1/embeddings`，维度 1536，批量大小 10。
  - 文本 rerank 使用 `qwen3-rerank` 与 `compatible-api/v1/reranks`。
  - `qwen3-vl-rerank` 不走 OpenAI-compatible 文本 rerank，本项目文本 RAG 暂不用。

### 文档

- `docs/plans/2026-06-08-advanced-rag-phase4.md`（新建）— Phase 4 实现计划。
- `docs/plans/2026-06-08-openai-compatible-model-adapters.md`（新建）— 模型 adapter 接入计划。
- `docs/experiments/eval-questions.md`（新建）— Advanced RAG 固定评估问题集。
- `docs/testing/failures/2026-06-08-advanced-rag-phase4-notes.md`（新建）— pytest/pydantic 环境缺失与 PowerShell UTF-8 BOM 问题复盘。
- `docs/reviews/2026-06-08-openai-compatible-model-adapters-review-prompt.md`（新建）— adapter review 提示。
- `ai-service/README.md`、`backend-java/README.md`、`frontend/README.md`（修改）— 补充 Advanced RAG 与模型 adapter 当前能力、入口和限制。
- `PROJECT_CONTEXT.md`（修改）— 更新阶段状态、当前待办与 2026-06-08 变更摘要。

## 已通过的验证

- ✅ `python -m compileall ai-service/app`
- ✅ `mvn compile -q -f backend-java/pom.xml`
- ✅ `frontend npm run build`
- ✅ adapter import smoke：registry 自动选择 `OpenAICompatibleLLMAdapter`、`OpenAICompatibleEmbeddingAdapter`、`OpenAICompatibleRerankAdapter`
- ✅ 真实 adapter 小流量 smoke：embedding 返回 1536 维；rerank 返回 2 个分数且相关文档更高；LLM 接口可返回内容
- ✅ retry 改造后再次执行 embedding / rerank 小流量 smoke，通过

## 尚未验证

- ❌ `python -m pytest ai-service/tests -q`：当前 shell Python 缺少 `pytest` 与 `pydantic`，已写入失败复盘。
- ❌ 全链路 HTTP smoke：当前 Docker CLI 存在但 Docker Desktop daemon 未运行，无法启动 PostgreSQL / Redis；需启动 Docker Desktop 后再验证 `/api/rag/query` 多策略行为。
- ❌ 浏览器端策略切换与真实引用展示。

## 当前重点 review 文件

1. `ai-service/app/services/adapters/openai_compatible.py` — 真实模型 adapter、响应解析、错误处理与重试。
2. `ai-service/app/services/adapters/registry.py` — adapter 自动选择与 fallback。
3. `ai-service/app/core/config.py` — `.env` 读取与模型配置。
4. `ai-service/app/rag/strategies/advanced.py` — Advanced RAG 主策略链路。
5. `ai-service/app/rag/query_transformers/base.py` — 规则型 query rewrite / multi-query。
6. `ai-service/app/db/repositories.py` — hybrid search 与 parent-child fallback。
7. `ai-service/app/services/rag_service.py` — 策略分发与生成上下文。
8. `backend-java/src/main/java/.../service/RagService.java` — metadataFilters 透传、rewritten_query 入库、rank 修复。
9. `frontend/src/api/chat.ts` / `frontend/src/utils/mock-data.ts` — 前端策略与参数透传。
10. `docs/experiments/eval-questions.md` — Phase 4 评估问题。

## 当前仍是占位或限制

- 如果 `.env` 中模型配置缺失，会 fallback 到 stub embedding / LLM / reranker。
- 当前真实 adapter 已有轻量重试，但尚未实现限流、熔断、成本统计。
- query rewrite / multi-query 当前是规则型 fallback，不是真实 LLM 改写。
- parent-child 本轮是邻近 chunk fallback，尚未基于真实 parent_chunk_id 切分策略构建父块。
- DashScope-native 高级 embedding 参数（text_type、instruct、sparse vector）尚未接入。

## 下一步建议

1. 按用户要求，Advanced RAG 之后能力暂不继续开发。
2. 若继续增强，优先做全链路 HTTP smoke：PostgreSQL + FastAPI + Spring Boot + 浏览器端策略切换。
3. 若继续增强模型侧，补限流、熔断、成本统计，并在 `docs/experiments/eval-questions.md` 固定问题集上做对比评估。
4. 在依赖环境就绪后运行 Python pytest。
---

## 2026-06-08 Local Full-Chain Validation Update

This update keeps the historical handoff content intact and records the latest non-Docker validation pass.

Completed in this iteration:

- Added local full-chain automation at `scripts/test-fullchain-local.ps1`.
- Made `smoke_test.py` configurable with `SMOKE_BASE_URL`, `SMOKE_AI_BASE_URL`, and `SMOKE_TIMEOUT`.
- Added offline Advanced RAG strategy comparison helpers under `ai-service/app/rag/evaluators/`.
- Added AI tests for strategy comparison and backend unit tests for async ingest plus RAG bridge behavior.
- Updated testing documentation in `docs/testing/strategy.md` and automation notes in `scripts/README.md`.

Validated:

- `ai-service/.venv/bin/python.exe -m pytest` passed.
- `mvn test` passed for backend Java tests.
- `npm.cmd run typecheck` and `npm.cmd run build` passed for frontend.
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1 -SkipBuild` passed with 42/42 smoke checks.

Advanced RAG coverage now includes:

- Offline strategy comparison metrics: recall@k, precision@k, MRR, and citation hit.
- Full-chain HTTP query using `strategyName=advanced-rag`.
- Citation presence check.
- Run detail retrieval and `rewrittenQuery` persistence check.

Frontend follow-up areas addressed by the multi-agent iteration:

- Runtime Settings changes now drive the API client at request time.
- Loaded chat history is mapped back into the visible thread.
- Knowledge base create/detail/edit/delete, document detail/delete, and upload validation are wired in the UI.

---

## 2026-06-08 Phase 5 Agent Workflow Update

Completed in this iteration:

- Added `ai-service/app/agents/workflow.py` with a node-style study agent workflow.
- `/ai/agent/invoke` now returns question classification, selected strategy, workflow steps, output, citations, and trace metadata.
- Added Spring Boot `/api/agent/invoke` bridge to FastAPI `/ai/agent/invoke`.
- Added AI and backend unit tests for the Agent workflow bridge.
- Extended `smoke_test.py` with Agent workflow full-chain coverage.

Validated:

- `ai-service/.venv/bin/python.exe -m pytest` passed with 12 tests.
- `mvn test` passed with 6 tests.
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1` passed with 47/47 smoke checks.

Current remaining large project areas after Phase 5:

- GraphRAG / knowledge graph enhancement, addressed in the next section as a first engineering loop.
- Learning and interview assistant product workflows.
- Optional future replacement of the local node-style runner with a real `langgraph` dependency-backed graph.

---

## 2026-06-08 Phase 6 GraphRAG First Loop Update

Completed in this iteration:

- Added deterministic query entity and relationship extraction under `ai-service/app/rag/graph/`.
- Added `graph-rag` as a supported Advanced RAG strategy.
- GraphRAG now stores graph entities, relationships, and the graph-augmented query in trace attributes.
- Citation metadata now includes graph entity and relationship context.
- Frontend strategy options now include `GraphRAG`.
- `smoke_test.py` now covers GraphRAG through Spring Boot `/api/rag/query`.

Validated:

- `ai-service/.venv/bin/python.exe -m pytest` passed with 13 tests.
- `npm.cmd run typecheck` and `npm.cmd run build` passed.
- `mvn test` passed with 6 tests.
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1` passed with 54/54 smoke checks.

Current remaining large project areas:

- Persist graph entities and relationships with Flyway-managed tables.
- Implement graph-aware retrieval over persisted graph facts.
- Build learning and interview assistant product workflows.
