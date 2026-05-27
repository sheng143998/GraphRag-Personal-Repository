# Cognee CLAUDE.md 中文学习整理版

原始项目：Cognee  
原始文档：[topoteretes/cognee/CLAUDE.md](https://github.com/topoteretes/cognee/blob/main/CLAUDE.md)  
整理目的：学习 AI Memory / Knowledge Graph / GraphRAG 项目如何给 Claude Code 或 Codex 提供开发上下文。  
整理方式：中文改写与结构化提炼，不是逐字翻译。

## 1. 这份文档的定位

Cognee 的 `CLAUDE.md` 是一份专门写给 Claude Code 的开发上下文文档。

它的核心价值是：把一个复杂的 AI Memory / Knowledge Graph 项目压缩成 Agent 能快速理解的系统地图，包括：

- 项目是什么
- 怎么安装
- 怎么测试
- 核心工作流是什么
- 数据如何从原始输入变成图谱和向量索引
- 支持哪些数据库和模型供应商
- 新增功能应该扩展哪里
- 常见问题怎么排查

这份文档非常适合你的项目学习，因为你的目标里也包含 Advanced RAG、GraphRAG、知识图谱、不同检索策略路由等内容。

## 2. 项目概览

Cognee 是一个开源 AI memory 平台，目标是把原始数据转换成持久化知识图谱，供 AI Agent 长期使用。

它强调的不是传统 RAG，而是一个类似 `Extract -> Cognify -> Load` 的流程：

- 从原始数据中抽取信息
- 用 LLM 抽取实体和关系
- 写入图数据库和向量数据库
- 支持后续通过图检索、向量检索、摘要检索等方式查询

对你的项目的启发：

你的项目虽然第一阶段可以先做传统 RAG，但文档里应该提前为 GraphRAG 留出位置：

```text
原始文档
-> 文本解析
-> chunk 切分
-> embedding 入库
-> 实体关系抽取
-> 图谱构建
-> 多策略检索
-> Agent 生成回答
```

## 3. 开发命令组织方式

Cognee 的文档先列开发命令，包括：

- 创建虚拟环境
- 安装项目
- 安装开发依赖
- 安装可选模块
- 安装 pre-commit
- 执行测试
- 执行格式化和类型检查
- 运行 SDK 示例
- 使用 CLI 添加、处理、搜索、删除数据

这说明一个好的 Agent 上下文文档应该把“怎么启动和验证项目”写得非常具体。

对你的项目的启发：

后续可以在你的 `PROJECT_CONTEXT.md` 或 `docs/development/local-setup.md` 中写：

```md
## 本地开发命令

### 启动基础设施

### 启动前端

### 启动 Java 后端

### 启动 Python AI 服务

### 运行 Python 测试

### 运行 Java 测试

### 运行前端测试

### 重建 embedding

### 执行 RAG 评估
```

Agent 每次开发时，如果文档里没有命令，就很容易乱猜。

## 4. 可选依赖设计

Cognee 把不同能力拆成安装 extras，例如：

- PostgreSQL / PGVector
- Neo4j
- ChromaDB
- 文档解析
- 网页抓取
- LangChain
- LlamaIndex
- Anthropic / Gemini / Ollama / Mistral 等模型供应商
- Redis
- 评估工具
- 监控工具
- 分布式执行
- 调试工具

这个设计说明它把项目做成了“可组合能力平台”。

对你的项目的启发：

你的项目前期不一定要做 Python package extras，但可以借鉴“能力分层”的思路：

```text
core: 基础 RAG
graph: GraphRAG / 实体关系抽取
eval: RAG 评估
local-llm: Ollama / 本地模型
monitoring: Langfuse / OpenTelemetry
web: 前端管理台
interview: 面试复习能力
```

这样后续扩展时不会混成一团。

## 5. 核心工作流

Cognee 最值得学习的是它把复杂系统概括成四个动作：

```text
add -> cognify -> search / memify
```

可以理解为：

- `add`：把文件、URL、文本等数据加入数据集
- `cognify`：抽取实体、关系和摘要，构建知识图谱
- `search`：使用不同检索策略查询知识
- `memify`：进一步丰富图谱，让系统形成长期记忆

对你的项目的启发：

你的项目也应该定义自己的核心工作流，而不是只列一堆技术。

建议第一版可以定义为：

```text
upload -> ingest -> retrieve -> answer -> evaluate
```

后续 GraphRAG 版本可以演进为：

```text
upload -> ingest -> index -> graphify -> retrieve -> reason -> evaluate
```

把工作流写进项目文档后，Agent 更容易判断当前任务处在哪个阶段。

## 6. Pipeline 架构

Cognee 使用 pipeline-based processing。所有数据处理都通过任务流水线完成，每个任务可以串行或并行组合。

典型任务包括：

- 文档分类
- 文本 chunk 抽取
- 图谱信息抽取
- 数据点写入
- 摘要生成
- 向量写入

对你的项目的启发：

你的 AI 服务可以设计类似模块：

```text
rag/
├── pipelines/
│   ├── ingestion_pipeline.py
│   ├── indexing_pipeline.py
│   ├── retrieval_pipeline.py
│   └── evaluation_pipeline.py
├── tasks/
│   ├── parse_document.py
│   ├── clean_text.py
│   ├── split_chunks.py
│   ├── extract_entities.py
│   ├── generate_embeddings.py
│   └── save_indexes.py
```

这比把所有逻辑写进一个 `service.py` 更适合长期演进。

## 7. 数据库适配器思想

Cognee 将数据库能力接口化：

- 图数据库通过 Graph DB interface 抽象
- 向量数据库通过 Vector DB interface 抽象
- 关系型数据库独立负责元数据和状态

它支持多种后端：

- Graph：Kuzu、Neo4j、Neptune、Postgres 等
- Vector：LanceDB、ChromaDB、PGVector 等
- Relational：SQLite、PostgreSQL 等

对你的项目的启发：

你当前计划使用 PostgreSQL + pgvector，很适合第一阶段。但代码层面不要把所有检索逻辑写死在 PostgreSQL 查询里。

建议保留接口：

```text
VectorStore
GraphStore
DocumentStore
ChatHistoryStore
RagRunStore
```

第一版实现：

```text
PostgresVectorStore
PostgresDocumentStore
PostgresRagRunStore
```

后续如果要接 Neo4j、Milvus、Qdrant，也不会大面积重写。

## 8. 分层结构写法

Cognee 用一个清晰的层级图说明系统结构：

```text
API Layer
-> Main Functions
-> Pipeline Orchestrator
-> Task Execution Layer
-> Domain Modules
-> Infrastructure Adapters
-> External Services
```

这对 Agent 非常友好，因为它说明了“入口在哪里、业务在哪里、基础设施在哪里”。

对你的项目的启发：

你的 AI 服务可以写成：

```text
FastAPI Routers
-> Application Services
-> LangGraph Workflows
-> RAG Strategies
-> Retrievers / Rerankers / Generators
-> Stores / Model Clients
-> PostgreSQL / LLM Providers
```

Java 后端可以写成：

```text
Controller
-> Application Service
-> Domain Service
-> Repository / AI Client
-> PostgreSQL / FastAPI AI Service
```

## 9. 关键数据流路径

Cognee 明确写出关键路径，例如：

- 数据加入路径
- 知识图谱构建路径
- 搜索路径

这类内容比单纯目录结构更重要，因为 Agent 修改功能时，需要知道真实调用链。

对你的项目的启发：

建议后续为每条核心链路写出路径：

```md
## 文档入库链路

POST /ai/ingest/document
-> DocumentParser
-> TextCleaner
-> Chunker
-> EmbeddingService
-> VectorStore
-> DocumentStatusUpdater

## RAG 问答链路

POST /ai/rag/query
-> QuestionClassifier
-> StrategySelector
-> Retriever
-> Reranker
-> PromptBuilder
-> LLMGenerator
-> CitationBuilder
-> RagRunLogger

## GraphRAG 链路

DocumentChunks
-> EntityExtractor
-> RelationExtractor
-> GraphStore
-> GraphRetriever
-> ContextMerger
-> AnswerGenerator
```

## 10. 检索类型枚举

Cognee 的文档列出了大量 search type，这对你的项目非常有启发。

它不是只有一种 search，而是包括：

- 图遍历 + LLM 回答
- 图摘要检索
- 图上的推理型检索
- 三元组检索
- 传统 RAG
- chunk 向量检索
- chunk 关键词检索
- 摘要检索
- 自然语言转结构化查询
- 时间感知检索
- 自动选择检索类型
- 代码规则检索

对你的项目的启发：

你也可以从一开始定义自己的检索类型枚举：

```python
class RetrievalStrategy(str, Enum):
    VECTOR = "vector"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    RERANKED_HYBRID = "reranked_hybrid"
    PARENT_CHILD = "parent_child"
    MULTI_QUERY = "multi_query"
    SUMMARY = "summary"
    GRAPH = "graph"
    GRAPH_VECTOR_HYBRID = "graph_vector_hybrid"
    INTERVIEW_MODE = "interview_mode"
    AUTO = "auto"
```

这会让 Advanced RAG 的演进更清晰。

## 11. 核心数据模型

Cognee 强调了图谱中的几个关键模型：

- 数据点：图节点的基础单元
- 边：节点之间的关系
- 三元组：主语、谓语、宾语
- 知识图谱：节点和边的容器
- 节点：实体及其描述
- 关系：实体之间的连接

对你的项目的启发：

后续 GraphRAG 阶段可以设计：

```text
graph_entities
- id
- name
- entity_type
- description
- aliases
- source_chunk_ids

graph_relationships
- id
- source_entity_id
- target_entity_id
- relation_type
- description
- confidence
- source_chunk_ids

graph_triplets
- id
- subject
- predicate
- object
- source_chunk_id
```

这可以和 `document_chunks` 关联，让图谱检索结果可追溯。

## 12. LLM 与结构化输出

Cognee 使用统一 LLM Gateway 来适配多个模型供应商，并使用结构化输出能力抽取实体和关系。

这对 GraphRAG 很关键，因为实体关系抽取不能只依赖自由文本输出，否则后续很难稳定入库。

对你的项目的启发：

建议实体关系抽取时使用 Pydantic schema：

```python
class ExtractedEntity(BaseModel):
    name: str
    entity_type: str
    description: str | None = None

class ExtractedRelationship(BaseModel):
    source: str
    target: str
    relation_type: str
    evidence: str
```

并把 Prompt、模型、输出 schema、解析错误都记录到 trace 中。

## 13. 配置管理

Cognee 的配置部分非常完整，包括：

- LLM Provider
- Embedding Provider
- 关系型数据库
- 向量数据库
- 图数据库
- 存储后端
- 结构化输出框架
- 速率限制
- 本地模型
- 云模型

它还提醒：只配置 LLM 或只配置 embedding 时，另一个可能回退到默认供应商。

对你的项目的启发：

你的 `.env.example` 不应该只写几个 key，而应该按模块分区：

```env
# App
APP_ENV=local

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agent_knowledge

# LLM
LLM_PROVIDER=openai
LLM_MODEL=
LLM_API_KEY=

# Embedding
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=

# RAG
DEFAULT_RETRIEVAL_STRATEGY=hybrid
TOP_K=10
RERANK_TOP_K=5

# GraphRAG
GRAPH_ENABLED=false
```

## 14. 扩展点设计

Cognee 明确告诉 Agent：如果要加新功能，应该从哪里扩展。

扩展点包括：

- 新任务类型
- 新数据库后端
- 新 LLM 供应商
- 新文档处理器
- 新搜索类型
- 自定义图模型

这非常适合复杂 AI 项目，因为 Agent 不会乱找位置。

对你的项目的启发：

你也应该写：

```md
## 扩展点

- 新文档解析器：添加到 `ai-service/app/rag/parsers/`
- 新 chunk 策略：添加到 `ai-service/app/rag/chunkers/`
- 新 embedding provider：添加到 `ai-service/app/rag/embeddings/`
- 新 retriever：添加到 `ai-service/app/rag/retrievers/`
- 新 reranker：添加到 `ai-service/app/rag/rerankers/`
- 新 RAG 策略：添加到 `ai-service/app/rag/strategies/`
- 新 LangGraph 节点：添加到 `ai-service/app/agents/nodes/`
- 新 GraphRAG 能力：添加到 `ai-service/app/rag/graph/`
```

## 15. 分支与代码风格

Cognee 规定从 `dev` 分支创建功能分支，并说明代码格式化、行宽、字符串风格、类型检查和 pre-commit。

对你的项目的启发：

后续可以统一：

- Python 使用 Ruff + mypy
- Java 使用 Checkstyle 或 Spotless
- Vue 使用 ESLint + Prettier
- 提交前跑 pre-commit 或对应检查
- 功能分支统一从 `dev` 拉出

这部分虽然不直接属于 RAG，但对长期维护很重要。

## 16. API 与 SDK 入口

Cognee 明确写出 FastAPI 路由和 Python SDK 入口。

对你的项目的启发：

你可以同时设计：

### FastAPI 入口

```text
POST /ai/ingest/document
POST /ai/rag/query
POST /ai/rag/retrieve
POST /ai/rag/evaluate
POST /ai/agent/invoke
GET  /ai/health
```

### Python 内部入口

```python
ingest_document()
retrieve()
answer()
evaluate()
build_graph()
```

Agent 做开发时会知道：API 是外部入口，函数是内部编排入口。

## 17. 安全配置

Cognee 在安全部分列出多个环境变量，用于控制：

- 是否允许访问本地文件
- 是否允许发起 HTTP 请求
- 是否允许直接执行图查询
- 是否要求认证
- 是否启用后端访问控制

对你的项目的启发：

你的本地知识库项目也应该认真考虑：

- 文档路径是否允许任意读取
- 是否允许从 URL 抓取资料
- 是否允许 Agent 自动执行数据库查询
- 是否需要用户级知识库隔离
- 面试经验、项目经验是否包含敏感信息
- 日志中是否会泄露 API Key 或私密内容

即使是个人项目，也要从一开始写清楚安全边界。

## 18. 常见问题与排查

Cognee 的文档最后提供了常见问题，例如：

- 本地模型和 OpenAI embedding 混用导致问题
- 结构化输出模式配置错误
- 默认 provider 回退导致意外调用 OpenAI
- 权限不足时搜索返回空结果
- 数据库连接失败
- 速率限制错误

对你的项目的启发：

你可以后续在文档中维护：

```md
## 常见问题

### 文档上传成功但检索不到

### embedding 生成失败

### pgvector 查询报错

### RAG 回答没有引用来源

### GraphRAG 抽取结果为空

### 本地模型输出无法解析为 JSON
```

这会极大减少后续新对话里的重复排查成本。

## 19. 可以直接借鉴到你项目的结构

建议从 Cognee 吸收以下结构到你的项目文档：

```md
## Project Overview

## Development Commands

## Core Workflow

## Architecture Overview

## Layer Structure

## Critical Data Flow Paths

## Retrieval Strategy Types

## Core Data Models

## LLM Gateway

## Database Configuration

## Extension Points

## Branching Strategy

## Code Style

## Testing Strategy

## API Structure

## Security Considerations

## Debugging & Troubleshooting
```

## 20. 学习总结

Cognee 的 `CLAUDE.md` 最大价值是：它把 GraphRAG / AI Memory 这类复杂系统拆成清楚的工作流、数据流、分层结构和扩展点。

它适合你重点学习：

- 如何描述 GraphRAG 系统
- 如何把 ingestion、graph construction、search 写成清楚的数据流
- 如何把检索策略设计成枚举和路由
- 如何抽象向量数据库、图数据库和关系数据库
- 如何为 Agent 标注扩展点
- 如何写出本地模型、云模型、数据库切换的配置说明

对你的本地知识库 Agent 项目来说，最值得复制的是：

- 定义核心工作流
- 写清关键数据流路径
- 提前设计检索策略枚举
- 抽象 VectorStore / GraphStore / DocumentStore
- GraphRAG 使用结构化实体关系抽取
- 文档中明确扩展点和排查手册
