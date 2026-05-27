# Python 人工智能服务模块

## 模块职责

人工智能服务负责本项目的文档处理、切分、向量生成、检索、重排、回答生成、评估和后续智能体编排能力。Java 后端通过内部接口调用本服务，前端不直接访问本服务。

## 技术栈

- Python 3.12。
- FastAPI。
- Pydantic。
- pg8000。
- PostgreSQL。
- pgvector。
- 后续预留 LangChain 与 LangGraph。

## 目录结构说明

```text
ai-service/
├─ app/
│  ├─ api/          # 接口路由
│  ├─ core/         # 配置和基础能力
│  ├─ db/           # 数据库访问
│  ├─ rag/          # 检索增强生成核心模块
│  ├─ schemas/      # 请求和响应结构
│  ├─ services/     # 应用服务
│  ├─ agents/       # 智能体预留目录
│  └─ prompts/      # 提示词预留目录
├─ tests/
├─ pyproject.toml
└─ README.md
```

## 本地启动方式

```powershell
cd ai-service
python -m venv .venv
.\.venv\bin\python.exe -m pip install -e .
.\.venv\bin\python.exe -m uvicorn app.main:app --reload --port 8001
```

## 常用命令

```powershell
.\.venv\bin\python.exe -m pip install -e .
.\.venv\bin\python.exe -m pip install -e ".[dev]"
.\.venv\bin\python.exe -m compileall app tests
.\.venv\bin\python.exe -m pytest
```

## 环境变量说明

- `AI_DATABASE_URL`：人工智能服务访问 PostgreSQL 的连接地址。
- `DATABASE_URL`：数据库连接地址备用变量。
- `AI_RAG_USE_DATABASE`：是否使用真实数据库检索。设为 `false` 时使用内存模式，方便单元测试。

真实数据库密码只放在本地环境，不写入仓库文档或测试。

## 关键代码入口

- `app/api/routes/health.py`：健康检查接口。
- `app/api/routes/ingest.py`：文档入库接口。
- `app/api/routes/rag.py`：检索增强生成接口。
- `app/services/rag_service.py`：RAG 应用服务。
- `app/db/repositories.py`：文档、片段、向量的数据库访问。
- `app/rag/retrievers/base.py`：检索器接口与数据库检索器。
- `app/rag/strategies/base.py`：RAG 策略入口。
- `app/services/adapters/stub.py`：本地占位模型适配器。
- `tests/test_basic_rag_pipeline.py`：基础 RAG 主链路测试。

## 内部接口

- `GET /ai/health`
- `POST /ai/ingest/document`
- `POST /ai/ingest/rebuild-embeddings`
- `POST /ai/rag/retrieve`
- `POST /ai/rag/query`
- `POST /ai/rag/evaluate`
- `POST /ai/agent/invoke`

## 检索增强生成主链路

```text
Java 后端
-> POST /ai/rag/query
-> RagService
-> 策略
-> 检索器
-> 数据库访问层
-> PostgreSQL 与 pgvector
-> 生成器
-> 返回答案、引用和追踪信息
```

## 重点审查文件

- `app/api/routes/rag.py`
- `app/api/routes/ingest.py`
- `app/services/rag_service.py`
- `app/db/repositories.py`
- `app/rag/retrievers/base.py`
- `app/rag/strategies/base.py`
- `app/rag/rerankers/base.py`
- `app/services/adapters/stub.py`
- `tests/test_basic_rag_pipeline.py`

## 当前已实现能力

- 健康检查。
- 文档文本入库接口。
- 基础片段切分。
- 1536 维本地确定性向量生成。
- PostgreSQL 与 pgvector 写入。
- 数据库检索器。
- 基础混合检索。
- 基础问答请求。
- 追踪信息返回结构。

## 当前占位实现

- 回答生成器仍返回占位答案。
- 向量生成仍是确定性散列逻辑，不代表真实语义效果。
- 重排器仍是占位实现。
- MinerU PDF 解析器仍是预留位置。
- 多格式文件解析还未完成。
- 智能体编排还未完成。

## 后续待补能力

- 真实向量模型接入。
- 真实大模型生成器接入。
- 真实重排器接入。
- Markdown、TXT、Word、PDF、Excel 解析。
- MinerU PDF 解析流程。
- 查询改写、多查询检索、父子片段检索、上下文压缩。
- RAG 评估与实验对比。

## 常见问题

- 如果依赖安装失败，先确认 Python 版本和包源是否可用。
- 如果数据库连接失败，检查 `AI_DATABASE_URL` 或 `DATABASE_URL`。
- 如果单测需要绕过数据库，设置 `AI_RAG_USE_DATABASE=false`。
- 如果 pgvector 写入失败，检查向量维度是否为 1536。
