# Python AI 服务模块

## 模块职责

`ai-service/` 是项目的 AI / RAG 服务。它通过内部 `/ai/*` 接口被 Java 后端调用，负责文档解析、切分、embedding、检索、重排、回答生成、Advanced RAG preset、Agent 编排、GraphRAG 和 evaluator 指标计算。

前端不直接访问本服务。

## 当前状态

- 已完成 FastAPI 基础工程、health check、文档入库、RAG 查询、检索、评估和 Agent 调用接口。
- 已完成 MinerU PDF parser、Word parser、基础 chunk / parent-child chunk 和空 chunk 防护。
- 已完成 OpenAI-compatible LLM / embedding / rerank adapter，并保留 stub fallback 便于测试。
- Advanced RAG 已收敛为 preset 配置：`hybrid-rerank`、`metadata-filter`、`parent-child`、`advanced-rag`、`graph-rag`。
- evaluator 返回结构化指标：`recall_at_k`、`precision_at_k`、`mrr`、`citation_hit`、GraphRAG entity / relationship / expansion 指标。
- trace 已记录真实 provider `usage`、`token_usage`、`latency_breakdown`、`adapter_calls`，Java 可提取为评测历史的 token / cost / latency 维度。

## 技术栈

- Python 3.12
- FastAPI
- Pydantic
- pg8000
- PostgreSQL + pgvector
- OpenAI-compatible model API
- LangChain / LangGraph 相关能力按当前工程逐步收敛

## 目录结构

```text
ai-service/
├── app/
│   ├── api/          # /ai/* 路由
│   ├── core/         # 配置、日志、trace
│   ├── db/           # 数据库访问
│   ├── rag/          # RAG 核心、retriever、reranker、strategy、evaluator
│   ├── schemas/      # Pydantic schema
│   ├── services/     # 应用服务和模型 adapter
│   ├── agents/       # Agent workflow
│   └── prompts/      # Prompt 模板
├── tests/
├── pyproject.toml
└── README.md
```

## 本地启动

```powershell
cd ai-service
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

如果本机虚拟环境是 `bin` 目录：

```powershell
.\.venv\bin\python.exe -m uvicorn app.main:app --reload --port 8001
```

## 常用命令

```powershell
.\.venv\bin\python.exe -m py_compile app\services\rag_service.py
.\.venv\bin\pytest.exe tests
.\.venv\bin\pytest.exe tests\test_strategy_comparison_evaluator.py tests\test_advanced_rag_strategy.py
```

## 环境变量

- `DB_URL`：统一 PostgreSQL JDBC 地址，AI 服务会转换为 Python PostgreSQL URL。
- `DB_USERNAME`：数据库用户名。
- `DB_PASSWORD`：数据库密码。
- `AI_RAG_USE_DATABASE`：是否使用真实数据库检索；`false` 时可使用测试 / 内存路径。
- `LLM_PROVIDER` / `LLM_MODEL` / `LLM_API_KEY` / `LLM_BASE_URL`：LLM adapter 配置。
- `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL` / `EMBEDDING_API_KEY` / `EMBEDDING_BASE_URL`：embedding adapter 配置。
- `RERANK_PROVIDER` / `RERANK_MODEL` / `RERANK_API_KEY` / `RERANK_BASE_URL`：rerank adapter 配置。
- `MINERU_API_BASE_URL` / `MINERU_API_TOKEN`：MinerU PDF 解析配置。

真实密钥只放在本地环境，不写入仓库。

## 内部接口

- `GET /ai/health`
- `POST /ai/ingest/document`
- `POST /ai/ingest/rebuild-embeddings`
- `POST /ai/rag/retrieve`
- `POST /ai/rag/query`
- `POST /ai/rag/evaluate`
- `POST /ai/agent/invoke`

## RAG 主链路

```text
Spring Boot
-> /ai/rag/query
-> RagService
-> embed query
-> preset strategy
-> query rewrite / multi-query / graph expansion
-> retrieval / fusion / parent-child context / rerank
-> prompt render
-> LLM generate
-> citations + trace
```

## 关键入口

- `app/services/rag_service.py`：RAG query / retrieve / evaluate 应用服务。
- `app/rag/strategies/presets.py`：Advanced RAG preset 配置。
- `app/rag/strategies/advanced.py`：Advanced RAG 执行链路。
- `app/rag/evaluators/base.py`：评测指标计算。
- `app/services/adapters/openai_compatible.py`：OpenAI-compatible 模型调用和 usage 捕获。
- `app/core/tracing.py`：trace、token usage 和 latency 汇总。
- `app/db/repositories.py`：文档、chunk、embedding、run、graph 数据访问。
- `app/prompts/rag_answer.v1.txt`：RAG 回答 prompt。

## 后续优化

- 将 provider 不返回 cost 时的估算成本做成可配置模型价格表，并明确标记估算来源。
- 增加 paragraph-aware / title-aware chunker，支持 chunk 策略实验。
- 增强 GraphRAG 的关系置信度、社区发现和跨文档推理。
- 为 adapter metadata 聚合补充更细粒度单元测试。
