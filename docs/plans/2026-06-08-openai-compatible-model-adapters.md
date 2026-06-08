# OpenAI-compatible 模型 Adapter 接入计划

日期：2026-06-08

## 要解决的问题

当前 AI 服务的 LLM、Embedding、Rerank 都是 stub adapter，Advanced RAG 只能验证工程链路，不能验证真实模型效果。本轮目标是基于用户提供的阿里百炼 DashScope OpenAI-compatible 配置，实现真实模型调用 adapter。

## 调研发现

- `.env` 已配置 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`、`EMBEDDING_BASE_URL`、`EMBEDDING_API_KEY`、`EMBEDDING_MODEL`、`RERANK_BASE_URL`、`RERANK_API_KEY`、`RERANK_MODEL`。
- 当前 `ai-service/app/core/config.py` 只读取数据库和 MinerU 配置，没有读取模型 adapter 配置。
- 当前 `ai-service/app/services/adapters/registry.py` 固定使用 `StubLLMAdapter`、`StubEmbeddingAdapter`、`StubRerankAdapter`。
- `pyproject.toml` 已有 `httpx`，可以直接实现 HTTP 调用，不需要新增依赖。
- 百炼控制台文档链接为登录态动态页面，工具只能读取到 Loading，因此本轮按 OpenAI-compatible 常见接口实现，并对 rerank 响应做兼容解析。

## 当前目标范围

- 实现 OpenAI-compatible LLM adapter。
- 实现 OpenAI-compatible Embedding adapter。
- 实现 OpenAI-compatible Rerank adapter。
- `registry.py` 根据 provider 与 key/model 是否存在自动选择真实 adapter，否则 fallback stub。
- 更新配置、README、交接文档。

不做：

- 不改数据库向量维度，仍使用 1536。
- 不接 LangGraph、GraphRAG。
- 不提交真实 API Key。

## 涉及模块

- `ai-service/app/core/config.py`
- `ai-service/app/services/adapters/base.py`
- `ai-service/app/services/adapters/openai_compatible.py`
- `ai-service/app/services/adapters/registry.py`
- `ai-service/README.md`
- `.env.example`
- `docs/testing/failures/`
- `docs/handoff/CURRENT_STATE.md`

## 实现策略

1. 扩展 `Settings`，读取 LLM / Embedding / Rerank provider、base_url、api_key、model、timeout、维度、批量大小、top_n。
2. 新增 `OpenAICompatibleLLMAdapter`：调用 `/chat/completions`，messages 使用 system + user prompt。
3. 新增 `OpenAICompatibleEmbeddingAdapter`：调用 `/embeddings`，解析 `data[].embedding`，校验维度与 `EMBEDDING_DIMENSIONS` 一致。
4. 新增 `OpenAICompatibleRerankAdapter`：优先尝试 `/rerank`，兼容 `results[].relevance_score`、`results[].score`、`scores[]` 等常见响应；失败时抛出清晰错误，由 registry 或调用方决定是否 fallback。
5. `registry.py` 根据配置创建 adapter：配置完整且 provider 为 `openai-compatible` 时用真实 adapter，否则使用 stub。
6. 保留 `get_*_model_name()`，返回当前真实 model name 或 stub model name，确保 trace 可观测。

## 重点 review 文件

1. `ai-service/app/services/adapters/openai_compatible.py`
2. `ai-service/app/services/adapters/registry.py`
3. `ai-service/app/core/config.py`
4. `ai-service/app/services/rag_service.py` 中已有调用链路是否无需改动

## 测试计划

- `python -m compileall ai-service/app`
- 若依赖环境具备：`python -m pytest ai-service/tests -q`
- 可选真实 smoke：启动 AI 服务后调用 `/ai/rag/query`，观察 trace model name 是否变为真实模型名。

## 已知风险

- DashScope rerank OpenAI-compatible endpoint 可能不是 `/rerank`，需要根据真实文档调整。
- Embedding 模型实际返回维度必须等于 PostgreSQL `vector(1536)`，否则写入失败。
- 当前 `.env` 中真实 key 已由用户本地配置，仓库文档只保留占位变量。