# Python AI 服务模块

`ai-service/` 是项目的 AI / RAG 服务。它通过内部 `/ai/*` 接口被 Java 后端调用，负责文档解析、切分、embedding、检索、重排、回答生成、Advanced RAG preset、企业售后 Agent 编排、GraphRAG、RAGAS 测评集生成和 evaluator 指标计算。

React 前端不直接访问本服务。

## 当前状态

- 已完成 FastAPI 基础工程、health check、文档入库、RAG 查询、检索、评估和 Agent 调用接口。
- 已升级到 FastAPI / Pydantic v2 / LangChain / LangGraph 新版本栈，保留兼容序列化 helper。
- 已完成 MinerU PDF parser、Word parser、Spreadsheet parser、Markdown block-aware、Q&A chunker、code-aware chunker 和表格行组 chunker。
- 文档入库可按文档类型动态选择 chunk 策略，并对短文档 parent-child 重复内容做自动降级。
- Advanced RAG 已收敛为 preset 配置：`hybrid-rerank`、`metadata-filter`、`parent-child`、`advanced-rag`、`graph-rag`。
- 企业售后技术支持 Agent 已升级为 Support Supervisor：澄清、检索、代码/日志分析、诊断、风险审查、工单升级、评估审查。
- Support Supervisor 默认 `auto` runtime，依赖可用时使用真实 LangGraph `StateGraph.compile().ainvoke(...)`；依赖缺失时可观测回落本地 runtime。
- RAGAS 测评集生成支持 `rule / llm / ragas / auto`，离线评估报告可经 Java 后端回填数据库。
- trace 已记录 provider usage、token usage、latency breakdown、adapter calls、workflow gates、final status 和 RAG run 定位信息。

## 技术栈

- Python 3.12
- FastAPI
- Pydantic v2
- LangChain
- LangGraph
- pg8000
- PostgreSQL + pgvector
- OpenAI-compatible model API
- RAGAS 兼容离线评估链路

## 目录结构

```text
ai-service/
├── app/
│   ├── api/          # /ai/* 路由
│   ├── agents/       # Support Supervisor、节点、状态和工具
│   ├── core/         # 配置、日志、trace
│   ├── db/           # 数据库访问
│   ├── prompts/      # Prompt 模板
│   ├── rag/          # RAG 核心、retriever、reranker、strategy、evaluator
│   ├── schemas/      # Pydantic schema
│   └── services/     # 应用服务和模型 adapter
├── scripts/          # 入库、导出、RAGAS 离线运行辅助脚本
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
.\.venv\bin\python.exe -m pytest tests
.\.venv\bin\python.exe -m pytest tests\test_agent_workflow.py tests\test_support_agent_nodes.py tests\test_support_supervisor_graph.py
.\.venv\bin\python.exe -m pytest tests\test_ragas_bridge.py tests\test_ragas_testset_generation.py
.\.venv\bin\python.exe -m compileall -q app\agents app\services\agent_service.py
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
- `AI_AGENT_SUPPORT_WORKFLOW_RUNTIME`：`auto`、`langgraph` 或 `local`。
- `RAGAS_TESTSET_GENERATION_MODE`：测评集生成模式，可选 `rule`、`llm`、`ragas`、`auto`。

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

## Support Supervisor 链路

```text
Spring Boot assistant-turn
-> /ai/agent/invoke
-> SupportSupervisorWorkflow
-> clarification
-> retrieval
-> code_log_analysis
-> diagnosis
-> risk_review
-> escalation
-> evaluation_review
-> supportPlan + workflowSteps + trace
```

## 关键入口

- `app/services/rag_service.py`：RAG query / retrieve / evaluate 应用服务。
- `app/services/agent_service.py`：Agent 调用入口。
- `app/agents/graphs/support_supervisor.py`：售后 Support Supervisor 编排。
- `app/agents/nodes/`：澄清、检索、诊断、风险、升级、评估等节点。
- `app/rag/strategies/presets.py`：Advanced RAG preset 配置。
- `app/rag/strategies/advanced.py`：Advanced RAG 执行链路。
- `app/rag/evaluators/`：指标计算和 RAGAS bridge / testset generation。
- `app/services/adapters/openai_compatible.py`：OpenAI-compatible 模型调用和 usage 捕获。
- `app/core/tracing.py`：trace、token usage、latency 和 workflow attributes 汇总。
- `app/db/repositories.py`：文档、chunk、embedding、run、graph 数据访问。

## 后续优化

- 将 Support Supervisor 的工单升级草稿接入真实工单系统或 webhook。
- 为 RAGAS 生成样本增加前端可解释质量分和证据缺失原因。
- 增强 GraphRAG 的关系置信度、社区发现和跨文档推理。
- 为不同 provider 的 token / cost 估算维护可配置价格表，并明确标记估算来源。
