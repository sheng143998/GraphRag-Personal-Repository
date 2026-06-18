# 本地知识库 Agent 项目上下文

更新时间：2026-06-18
项目状态：Phase 0-9 已完成工程闭环，覆盖三服务架构、文档入库、基础 RAG、Advanced RAG、Agent 学习闭环、GraphRAG、RAG 实验评估、评测集管理工具、复习辅助与 Coze Studio 风格前端工作台重构；2026-06-16 已完成文档上传入口升级，支持单篇、多篇和文件夹上传，默认使用 Spring `@Async` 本地线程池异步解析，并可通过 RabbitMQ 队列模式提交文档入库任务；同日新增 `frontend-react/` React + TypeScript 并行迁移工作区，按 Stitch RAG Knowledge Studio 设计实现第一版工作台页面；2026-06-17 AI 服务 chunk 切分继续增强，覆盖 Markdown block-aware、DOCX 标题/表格结构、MinerU PDF block metadata、Q&A chunker 与 code-aware chunker，并修复 MinerU 标准 batch 轮询端点导致的假超时；同日新增 RAGAS 兼容评估侧路，支持从已上传文档 chunk 自动生成 DRAFT 测评集草稿、人工审核 CSV、RAGAS JSONL 导出与独立环境离线评分；同日新增企业售后技术支持 Agent 编排，返回结构化 `supportPlan`，覆盖澄清问题、证据引用、诊断步骤、升级建议、风险提示和下一步动作；同日 `frontend-react/` 完成售后支持工作台中文化与美学优化，支持结构化展示 `supportPlan` 并通过 Playwright 渲染验证。2026-06-18 RAGAS 测评闭环继续完善：自动测评集生成支持 `rule / llm / ragas / auto`，离线 RAGAS 报告可回填 Spring Boot 数据库，React 实验页支持页面内人工审核、筛选、编辑、状态流转、样本删除、批量删除最近导入或当前筛选样本，以及删除当前实验；同日售后 Agent 从单体 workflow 升级为受控 Support Supervisor 本地状态图，拆分澄清、检索、代码/日志分析、诊断、风险审查、工单升级和评估审查节点，保持 `supportPlan` 兼容并强化 `workflowSteps` 可观测性。前端浏览器请求继续只进入 Spring Boot `/api/*`，Spring Boot 只做业务 / 桥接 / 持久化，FastAPI 负责 RAG / Agent / GraphRAG / evaluator 逻辑。
维护规则：每次开启新的开发对话时，优先提供本文件；每完成一个阶段目标或关键任务后，必须同步更新本文件。本文件只保留项目状态、关键架构决策、当前待办和阶段级变更摘要；接口级实现细节、验证命令和失败复盘放入 `docs/plans/`、`docs/reviews/`、`docs/testing/failures/` 与 `docs/handoff/`。

## 1. 项目目标

本项目是一个基于本地知识库的 Agent / Advanced RAG 练习项目，核心目标是帮助用户回忆和复习曾经学过的技术知识，并逐步沉淀开发经验、项目经验、面试经验等个人知识资产。

项目重点不只是做一个普通问答系统，而是围绕 RAG 技术进行系统练习，包括：

- 本地知识库管理
- 文档切分、清洗、解析、元数据设计
- 向量检索、关键词检索、混合检索
- Query Rewrite / Query Expansion
- Rerank
- 多路召回
- Parent-Child Chunk
- Multi-vector Retrieval
- Self-RAG / Corrective RAG
- GraphRAG 或知识图谱增强检索
- 基于文本类型选择不同 RAG 优化策略
- LangGraph Agent 编排
- 可观测、可评估、可迭代的 RAG 实验体系

## 2. 推荐技术架构

### 2.1 总体架构

推荐采用前后端分离 + AI 服务独立化的结构：

- 前端：Vue 3 + TypeScript + Vite
- 业务后端：Java + Spring Boot
- AI / RAG 服务：Python + FastAPI + LangChain + LangGraph
- 向量数据库：PostgreSQL + pgvector
- 元数据与业务数据：PostgreSQL
- 缓存与任务队列：Redis，可后续加入
- 异步任务：Celery / RQ / Spring Scheduler，可后续按需要选择
- 部署：Docker Compose 起步，后续可扩展到 K8s

### 2.2 服务职责边界

Spring Boot 后端负责：

- 用户、会话、权限等业务接口
- 知识库、文档、标签、分类等业务管理
- 调用 AI 服务并对外提供统一 API
- 记录问答历史、用户反馈、评估结果
- 管理系统配置和实验配置

FastAPI AI 服务负责：

- 文档解析、清洗、切分
- Embedding 生成
- 向量入库与检索
- Advanced RAG 策略执行
- LangChain Chain 构建
- LangGraph Agent 工作流编排
- RAG 评估、调试、检索结果解释

Vue 前端负责：

- 知识库管理界面
- 文档上传与解析状态展示
- 对话 / Agent 交互界面
- 检索过程可视化
- RAG 策略配置
- 问答反馈与评估结果展示

> 简化方案：如果前期想降低复杂度，可以先只做 Vue + FastAPI + PostgreSQL，等 RAG 主链路稳定后再引入 Spring Boot。

## 3. 项目目录结构

建议采用 Monorepo：

```text
agent-knowledge-rag/
├── README.md
├── PROJECT_CONTEXT.md
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── docs/
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── api-design.md
│   │   ├── rag-pipeline.md
│   │   └── database-design.md
│   ├── development/
│   │   ├── coding-standards.md
│   │   ├── git-workflow.md
│   │   └── local-setup.md
│   ├── product/
│   │   ├── user-stories.md
│   │   └── roadmap.md
│   ├── plans/
│   │   └── README.md
│   ├── handoff/
│   │   ├── CURRENT_STATE.md
│   │   └── YYYY-MM-DD-task-name.md
│   ├── testing/
│   │   ├── strategy.md
│   │   └── failures/
│   └── experiments/
│       ├── rag-evaluation.md
│       ├── eval-questions.md
│       └── strategy-comparison.md
│
├── frontend/
│   ├── README.md
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       ├── router/
│       ├── stores/
│       ├── api/
│       ├── components/
│       ├── layouts/
│       ├── pages/
│       │   ├── chat/
│       │   ├── knowledge-base/
│       │   ├── documents/
│       │   ├── experiments/
│       │   └── settings/
│       ├── types/
│       └── utils/
│
├── backend-java/
│   ├── README.md
│   ├── pom.xml
│   └── src/
│       ├── main/
│       │   ├── java/
│       │   │   └── com/example/agentknowledge/
│       │   │       ├── AgentKnowledgeApplication.java
│       │   │       ├── common/
│       │   │       ├── config/
│       │   │       ├── controller/
│       │   │       ├── service/
│       │   │       ├── repository/
│       │   │       ├── domain/
│       │   │       ├── dto/
│       │   │       └── client/
│       │   └── resources/
│       │       ├── application.yml
│       │       └── db/migration/
│       └── test/
│
├── ai-service/
│   ├── pyproject.toml
│   ├── README.md
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── prompts/
│   │   ├── rag/
│   │   │   ├── loaders/
│   │   │   ├── parsers/
│   │   │   ├── chunkers/
│   │   │   ├── embeddings/
│   │   │   ├── retrievers/
│   │   │   ├── rerankers/
│   │   │   ├── generators/
│   │   │   ├── graph/
│   │   │   ├── evaluators/
│   │   │   └── strategies/
│   │   ├── agents/
│   │   │   ├── graphs/
│   │   │   ├── nodes/
│   │   │   ├── states/
│   │   │   └── tools/
│   │   └── db/
│   ├── scripts/
│   │   ├── ingest_documents.py
│   │   ├── rebuild_embeddings.py
│   │   └── evaluate_rag.py
│   └── tests/
│
├── infra/
│   ├── README.md
│   ├── postgres/
│   │   └── init.sql
│   ├── nginx/
│   └── docker/
│
├── datasets/
│   ├── raw/
│   ├── processed/
│   └── samples/
│
└── scripts/
    ├── README.md
    ├── dev-start.ps1
    ├── dev-stop.ps1
    └── reset-local-db.ps1
```

## 4. 数据分类设计

知识库中的内容建议先按文档类型分类，因为不同类型适合不同的 RAG 策略。

### 4.1 文档类型

- 技术笔记：概念、原理、框架、源码分析、学习记录
- 开发经验：问题排查、Bug 记录、踩坑复盘、最佳实践
- 项目经验：项目背景、架构设计、技术选型、难点总结
- 面试经验：八股题、场景题、项目追问、面试复盘
- 代码片段：工具类、配置、脚本、Demo
- 书籍 / 课程摘要：章节笔记、重点总结、问题清单
- 招聘 JD：岗位职责、任职要求、技术栈关键词、业务领域、经验年限、加分项、面试关注点

### 4.2 支持的文档格式

文档入库需要支持常见办公和知识资料格式，先覆盖高频格式，再逐步增强复杂版面解析能力。

- 文本类：`.md`、`.txt`、`.html`
- Word：`.docx`，后续按需支持 `.doc`
- PDF：`.pdf`
- Excel / 表格：`.xlsx`、`.xls`、`.csv`
- 演示文稿：后续按需支持 `.pptx`
- 图片类：后续按需支持 `.png`、`.jpg`、`.jpeg`，主要用于 OCR 或截图笔记

解析工具建议：

- Markdown / TXT：直接解析文本并保留标题层级。
- Word：优先解析 `.docx` 的段落、标题、表格和列表结构。
- PDF：可使用 MinerU 作为 PDF 提取工具，优先处理复杂版面、表格、公式、扫描件 OCR 等场景。
- Excel：按工作表、表头、行记录和关键字段解析，保留 sheet 名称、行列位置等 metadata。
- 不同格式解析后统一输出标准 Document / Chunk 结构，便于后续切分、embedding、检索和引用。

### 4.3 元数据字段

每个知识片段建议至少包含：

- `id`
- `document_id`
- `knowledge_base_id`
- `title`
- `content`
- `chunk_index`
- `document_type`
- `file_type`
- `mime_type`
- `source_type`
- `source_path`
- `parser_name`
- `parser_version`
- `page_number`
- `sheet_name`
- `row_range`
- `tags`
- `tech_stack`
- `difficulty`
- `created_at`
- `updated_at`
- `embedding_model`
- `chunk_strategy`
- `summary`
- `parent_chunk_id`

## 5. RAG 策略规划

### 5.1 基础 RAG

基础链路：

```text
用户问题
-> 问题预处理
-> 检索 query 生成
-> 向量检索
-> 上下文组装
-> LLM 生成回答
-> 来源引用
```

### 5.2 Advanced RAG 能力

计划逐步实现：

- Hybrid Search：向量检索 + BM25 / 全文检索
- Rerank：对召回结果进行相关性重排
- Query Rewrite：将口语化问题改写成更适合检索的问题
- Query Expansion：扩展同义词、相关技术词、上下游概念
- Multi-query Retrieval：生成多个检索问题并合并结果
- Parent-Child Retrieval：小块检索，大块回答
- Context Compression：压缩上下文，减少无关内容
- Metadata Filter：按技术栈、文档类型、时间、标签过滤
- Step-back Prompting：先抽象问题，再检索具体内容
- Corrective RAG：检测召回质量，不足时触发补救检索
- Self-RAG：让模型判断是否需要检索、是否需要重试
- GraphRAG：基于实体、关系、主题社区进行图增强问答

### 5.3 按文档类型选择策略

| 文档类型 | 推荐策略 |
| --- | --- |
| 技术笔记 | Hybrid Search + Rerank + Parent-Child Retrieval |
| 开发经验 | Metadata Filter + Hybrid Search + Rerank |
| 项目经验 | Query Rewrite + Multi-query + Parent-Child Retrieval |
| 面试经验 | Q&A Pair Chunking + Query Expansion + Rerank + Answer Template |
| 代码片段 | Code-aware Chunking + Keyword Search + Metadata Filter + 精确引用 |
| 书籍 / 课程摘要 | Summary Index + Parent-Child Retrieval |
| 招聘 JD | Keyword Extraction + Metadata Filter + Hybrid Search + 技能差距分析 |

## 6. LangGraph Agent 规划

Agent 不是第一阶段就做复杂，而是在基础 RAG 稳定后逐步加入。

### 6.1 初始 Graph

```text
START
-> classify_question
-> select_rag_strategy
-> retrieve_context
-> grade_context
-> generate_answer
-> cite_sources
-> END
```

### 6.2 后续扩展节点

- `rewrite_query`：改写用户问题
- `expand_query`：扩展检索词
- `route_by_document_type`：根据问题和文档类型路由
- `retrieve_vector`：向量检索
- `retrieve_keyword`：关键词检索
- `retrieve_graph`：图检索
- `rerank_documents`：重排文档
- `compress_context`：压缩上下文
- `verify_answer`：检查回答是否有依据
- `generate_followup_questions`：生成复习追问
- `save_memory`：保存用户反馈和学习状态

## 7. 数据库规划

PostgreSQL 建议同时承担业务数据和向量数据存储。前期为了降低复杂度，可以共用一个数据库，但必须明确表结构归属、写入职责和迁移目录，避免多个服务同时“偷偷改库”。

### 7.1 核心表

业务与知识库表：

- `knowledge_bases`
- `documents`
- `tags`
- `document_tags`
- `chat_sessions`
- `chat_messages`
- `rag_feedback`
- `rag_experiments`

RAG 派生数据与可观测性表：

- `document_chunks`
- `chunk_embeddings`
- `rag_runs`
- `rag_retrieval_results`
- `graph_entities`
- `graph_relationships`

### 7.2 数据写入职责

- Spring Boot 默认负责业务表写入，包括知识库、文档元信息、标签、会话、消息、反馈、实验配置。
- FastAPI AI 服务默认只读业务表；如需更新文档解析状态，优先通过 Spring Boot API 回写，不直接改业务表。
- FastAPI AI 服务负责写入 RAG 派生数据，包括 `document_chunks`、`chunk_embeddings`、`rag_runs`、`rag_retrieval_results`。
- `graph_entities`、`graph_relationships` 由 AI 服务在 GraphRAG 流程中写入，但表结构仍通过统一迁移管理。
- 任一服务新增写表权限时，必须在本节补充职责说明，并在对应测试中覆盖。

### 7.3 数据库迁移规范

默认选择 Flyway 管理 Java 后端和共享数据库 schema。除非后续明确切换到 Liquibase，否则不要混用两套迁移工具。

如何运行数据库迁移：

- 本地先启动 PostgreSQL，例如通过 `docker compose up -d postgres`。
- Java 后端启动时自动执行 Flyway 迁移；也可以在 `backend-java/` 下通过 Maven Flyway 命令手动执行。
- 手动执行示例：Windows 使用 `.\mvnw.cmd flyway:migrate`，macOS / Linux 使用 `./mvnw flyway:migrate`。
- CI 环境必须先执行迁移，再运行依赖数据库的测试。
- 如果早期只做 Vue + FastAPI + PostgreSQL，Python 服务可临时使用 Alembic，但共享表迁移仍需要最终收敛到统一目录。

如何创建数据库迁移：

- Flyway 迁移文件放在 `backend-java/src/main/resources/db/migration/`。
- 文件名使用 `V{yyyyMMddHHmm}__{description}.sql`，例如 `V202605251730__create_rag_trace_tables.sql`。
- 迁移文件需要手写 SQL，并放在工具约定会扫描的位置；禁止只依赖 ORM 自动生成、启动时自动同步或临时 SQL。
- 如果使用 Liquibase 或 Alembic 生成空迁移文件，可以让工具生成文件名和路径，但表结构、索引、数据修正逻辑必须人工审阅并手写。
- 每次数据库变更必须有迁移脚本，不允许只改 Entity、DTO、Pydantic Schema 或 Repository。
- 迁移脚本需要可重复在空库上按顺序执行；已经合入的迁移不得随意改历史，只能追加新迁移修正。
- 数据库相关代码集中放置：Java 在 `backend-java/src/main/java/.../repository/` 与 `backend-java/src/main/resources/db/migration/`，Python 在 `ai-service/app/db/` 与 `ai-service/app/rag/` 内部，不在页面、Controller 或脚本里散落 SQL。

### 7.4 pgvector 规范

pgvector 主要用于：

- `chunk_embeddings.embedding`
- 后续可扩展多 embedding 字段，例如标题 embedding、摘要 embedding、正文 embedding

建表和索引要求：

- 首个向量迁移中必须包含 `CREATE EXTENSION IF NOT EXISTS vector;`。
- 向量字段维度必须和 `embedding_model` 明确绑定，例如 `vector(1536)` 或 `vector(3072)`。
- 大批量导入前可以先建表后导入，再创建 `ivfflat` 或 `hnsw` 索引；索引参数需要写入迁移注释或数据库设计文档。
- 常用 metadata filter 字段需要单独建 B-tree 或 GIN 索引，例如 `knowledge_base_id`、`document_type`、`tags`、`created_at`。
- pgvector 查询、metadata filter 和迁移脚本都需要数据库测试覆盖。

pgvector 索引迁移示例：

```sql
CREATE INDEX idx_chunk_embeddings_embedding_hnsw
ON chunk_embeddings
USING hnsw (embedding vector_cosine_ops);

CREATE INDEX idx_chunk_embeddings_metadata_gin
ON chunk_embeddings
USING gin (metadata);
```

## 8. API 规划

### 8.1 Spring Boot 对外 API

- `POST /api/chat/sessions`
- `GET /api/chat/sessions`
- `POST /api/chat/{sessionId}/messages`
- `GET /api/chat/{sessionId}/messages`
- `POST /api/knowledge-bases`
- `GET /api/knowledge-bases`
- `POST /api/documents/upload`
- `GET /api/documents`
- `GET /api/documents/{id}`
- `POST /api/rag/experiments`
- `GET /api/rag/experiments`
- `GET /api/rag/experiments/{id}`
- `PUT /api/rag/experiments/{id}`
- `DELETE /api/rag/experiments/{id}`
- `GET /api/rag/runs/{id}`
- `POST /api/feedback`

### 8.2 FastAPI AI 服务内部 API

- `POST /ai/ingest/document`
- `POST /ai/ingest/rebuild-embeddings`
- `POST /ai/rag/query`
- `POST /ai/rag/retrieve`
- `POST /ai/rag/evaluate`
- `POST /ai/agent/invoke`
- `GET /ai/health`

## 9. 开发与协作规范

### 9.1 Agent 关键规则

- 每次开始处理项目任务时，默认优先阅读最新 `PROJECT_CONTEXT.md`，再看相关代码和文档。
- 不要把真实 API Key、数据库密码、模型服务 Token 写入代码、测试、日志或文档；只提交 `.env.example` 中的占位变量名。
- 所有 RAG 调用必须记录 trace，包括问题、策略、召回结果、重排结果、上下文、答案、耗时和模型信息。
- 所有数据库迁移必须放在指定迁移目录中，数据库变更必须有迁移脚本，不允许只改实体类或 Schema。
- 新增 RAG 策略必须补充评估问题，默认写入 `docs/experiments/eval-questions.md` 或对应评估数据集。
- 前端请求统一走 `frontend/src/api/` 下的 API client，页面和组件不直接拼接 URL，也不直接散落 `fetch` / `axios` 调用。
- AI 服务的 Prompt 统一放在 `ai-service/app/prompts/`，业务代码只引用 prompt 名称、版本和变量，不内联大段 prompt。
- 前端默认只调用 Spring Boot 对外 API；Spring Boot 负责转调 FastAPI AI 服务，避免前端绕过业务后端直接访问 AI 服务。
- 复杂功能先写 `docs/plans/` 计划文档，再实现代码；简单修复可以直接做，但关键决策要同步到上下文或架构文档。
- 新增外部依赖、模型、向量维度、RAG 策略或跨服务接口时，必须同步更新文档和测试。
- 每完成一个阶段目标或关键任务后，更新 `PROJECT_CONTEXT.md` 的项目状态、当前待办和阶段级变更摘要；接口级实现细节、验证命令和失败复盘不写入 `PROJECT_CONTEXT.md`，改写入 `docs/plans/`、`docs/reviews/`、`docs/testing/failures/` 与 `docs/handoff/`。
- 每完成一个接口开发后，必须在 Codex 对话窗口发送 review 提示并暂停继续开发，给用户时间查看代码；用户明确确认继续后，才进入下一个接口或下一组改动。
- 子 Agent 可以并行开发，但必须遵守统一代码风格、目录结构、命名规范、错误处理、响应结构、trace 字段和文档语言规范；主 Agent 负责最终统一码风和接口契约。

### 9.2 通用规范

- 所有模块必须有清晰 README 或说明文档。
- 所有环境变量写入 `.env.example`，禁止提交真实密钥。
- 每个接口都要定义明确的请求和响应结构。
- 每个关键 RAG 流程都要记录输入、检索结果、策略、耗时和输出。
- 回答类接口必须保留来源引用，不能只返回无来源的自然语言答案。
- 重要决策写入 `docs/architecture/`，复杂功能计划写入 `docs/plans/`。
- 新增功能时同步更新 `PROJECT_CONTEXT.md`。

### 9.3 Git 规范

分支建议：

- `main`：稳定主分支
- `dev`：日常开发分支
- `feature/*`：功能分支
- `fix/*`：修复分支
- `experiment/*`：RAG 实验分支

提交信息建议：

```text
feat: add document ingestion api
fix: correct chunk metadata mapping
docs: update rag strategy plan
refactor: simplify retriever interface
test: add hybrid search tests
chore: update docker compose config
```

### 9.4 前端规范

- 使用 Vue 3 Composition API
- 使用 TypeScript
- 页面级组件放在 `pages/`
- 通用组件放在 `components/`
- API 请求统一放在 `api/`
- 类型定义统一放在 `types/`
- 状态管理建议使用 Pinia
- 表格、表单、上传、对话区等组件要考虑加载态、错误态、空状态
- 页面不直接拼接后端地址，统一通过 API client 管理
- API client 需要集中处理 base URL、认证头、错误结构、超时和请求追踪 ID

### 9.5 Java 后端规范

- Controller 只处理参数、权限和响应
- Service 承担业务逻辑
- Repository 只做数据访问
- DTO 与 Entity 分离
- 统一异常处理
- 统一响应结构
- AI 服务调用统一封装在 `client/`
- 数据库迁移使用 Flyway 或 Liquibase
- 复杂业务流程写单元测试或集成测试
- 对外接口返回统一错误码和可读错误信息，内部异常不直接暴露给前端
- 调用 AI 服务时透传或生成 trace ID，便于串联前端、后端和 AI 服务日志

### 9.6 Python AI 服务规范

- FastAPI 只负责 API 入口，RAG 逻辑放在 `rag/`
- LangGraph 节点保持小而清晰
- 每种 RAG 策略放在 `rag/strategies/`
- Retriever、Reranker、Generator 使用接口化设计
- Prompt 统一放在 `app/prompts/`，避免散落在业务代码中
- 每次 RAG 调用保存 trace，便于调试和评估
- 对检索结果保留 source、score、metadata
- 对实验参数保留可复现配置
- LLM、embedding、rerank、图像、语音、意图分类调用必须通过统一 adapter，便于限流、重试、超时、trace 和成本统计
- 输出结构需要优先使用明确 Schema，减少直接解析自然语言结果

### 9.7 测试策略

测试分为四类：

- 单元测试：隔离模块，不依赖外部服务，不访问真实数据库、Redis 或模型服务。
- 外部依赖单元测试：依赖 PostgreSQL、Redis、模型服务等外部组件，但不跑完整应用。
- 集成测试：运行在真实部署环境上，不做 mock，用来验证跨服务真实行为。
- Playwright E2E 测试：覆盖前后端完整交互，只用于明显需要浏览器验证的关键路径。

测试选择建议：

- 简单纯函数适合单元测试，例如文本清洗、chunk 切分、metadata 解析。
- 需要验证真实数据库、缓存、向量库时，写外部依赖单元测试。
- 端到端行为优先写集成测试，例如上传文档到完成入库、提问到返回引用。
- 涉及明显前后端协作的功能才写 E2E，例如上传文档、发起提问、查看引用来源、提交反馈。
- RAG 策略调整至少跑一组固定评估问题，避免只凭单次主观效果判断。

建议测试规划：

- Python 单元测试：`chunker`、`retriever`、`prompt builder`、`reranker adapter`、query rewrite 输入输出约束。
- Python RAG 评估测试：固定问题集、召回结果、引用覆盖、答案质量、无依据回答检测。
- Java 单元测试：Service 业务规则、权限判断、DTO 映射、AI client 错误处理。
- Java 集成测试：知识库、文档、会话、反馈接口，以及调用 AI 服务后的状态流转。
- 前端组件测试：表单、上传状态、聊天消息列表、引用来源展示、错误态和空状态。
- Playwright E2E 测试：上传文档、发起提问、查看引用来源、切换 RAG 策略、提交反馈。
- 数据库测试：迁移脚本、pgvector 查询、metadata filter、唯一约束和级联关系。

测试发现问题后的沉淀：

- 遇到非显而易见、反复出现或跨模块的问题时，在 `docs/testing/failures/` 增加复盘文档。
- 复盘文档建议包含：问题现象、复现步骤、根因、修复方案、补充的回归测试、下次排查建议。
- 修复 bug 时优先补回归测试；如果暂时不能自动化测试，需要在复盘文档中说明原因。

### 9.8 日志与可观测性及 LLM 调用规范

RAG 执行过程建议使用 `rag_runs` 和 `rag_retrieval_results` 记录。`rag_runs` 记录一次完整 RAG 调用的主流程，建议字段包括：

- `run_id`
- `trace_id`
- `session_id`
- `message_id`
- `question`
- `rewritten_query`
- `strategy_name`
- `retriever_type`
- `retrieved_chunk_ids`
- `scores`
- `rerank_scores`
- `final_context`
- `answer`
- `latency_ms`
- `model_name`
- `prompt_name`
- `prompt_version`
- `status`
- `error_message`
- `created_at`

`rag_retrieval_results` 记录每个召回片段的明细，建议字段包括：

- `id`
- `run_id`
- `chunk_id`
- `document_id`
- `rank`
- `score`
- `rerank_score`
- `retriever_type`
- `source`
- `metadata`
- `selected_for_context`
- `created_at`

LLM 调用规范：

- 所有 LLM、embedding、rerank、图像、语音、意图分类调用都必须打 trace 标签。
- trace 标签至少包含 `trace_id`、`run_id`、`operation`、`model_name`、`prompt_name`、`prompt_version`、`strategy_name`。
- 日志中禁止输出 API Key、完整认证头和敏感环境变量。
- 保存 full prompt、final context、模型输出时要考虑隐私与体积；本地开发可完整保存，后续生产化需要支持脱敏或采样。
- 每次模型调用需要记录耗时、输入输出 token 或近似长度、重试次数、错误类型和降级路径。
- 对 RAG 回答必须保存引用来源，便于后续评估答案是否有依据。

### 9.9 计划文档规范

复杂功能先在 `docs/plans/` 下写计划文档，再进入实现。文件名建议使用 `YYYY-MM-DD-feature-name.md`，例如 `2026-05-25-rag-trace-tables.md`。

计划文档核心结构：

- 要解决的问题
- 调研过程中发现的重要信息
- 当前背景
- 涉及模块
- 实现策略
- 重点 review 文件
- 测试计划
- 已知风险

计划文档不需要写时间线，也不需要写回滚计划。实现过程中如果发现计划明显不准确，需要更新计划或在最终变更记录中说明偏差原因。

### 9.10 代码审查与关键链路说明规范

本项目重点是 RAG 技术练习，因此每次涉及 Java 后端、Python AI 服务、RAG 策略、数据库迁移或跨服务调用时，Agent 必须补充“代码导读说明”，帮助用户快速 review，而不是只输出“完成了”。

每次开发完成后必须说明：

- 本次改了哪些文件。
- 每个文件负责什么。
- 入口 API 是什么。
- Java 后端如何调用 Python AI 服务。
- Python AI 服务内部 RAG 调用链路。
- 数据库读写发生在哪些类或函数。
- trace 如何生成、传递和保存。
- 哪些代码只是占位实现，哪些代码已经是真实逻辑。
- 如何运行和验证。

Java 调 Python 服务说明要求：

- 前端请求入口，例如 `POST /api/rag/query`。
- Java Controller 入口。
- Java Service 处理流程。
- Java AI client / gateway 调用方式。
- Python FastAPI 对应接口。
- Python RAG service 内部执行步骤。
- 返回结果如何回到前端。
- `trace_id` 如何贯穿前端、Java、Python 和数据库。

建议跨服务链路说明格式：

```text
Vue 页面
-> frontend/src/api/*
-> Spring Boot Controller
-> Spring Boot Service
-> AiServiceClient
-> FastAPI /ai/rag/query
-> RagService
-> Retriever / Reranker / Generator
-> TraceBuilder
-> 返回 answer + citations + trace
```

RAG 代码导读要求：

- 策略入口在哪个文件。
- retriever 如何召回。
- reranker 如何重排。
- prompt 如何选择。
- generator 如何调用模型。
- trace 记录了哪些字段。
- 该策略对应的评估问题在哪里。

接口级 review 暂停规则：

- 每开发完一个接口，Agent 必须立刻停下来提示用户 review。
- 提示内容必须包括接口方法与路径、涉及文件、调用链路、重点 review 顺序、验证命令和当前占位实现。
- 如果一个功能包含多个接口，必须按接口拆分交付，不允许一次性连续完成多个接口后才提示。
- 只有在用户明确回复继续、通过、下一个等确认意图后，Agent 才能继续开发下一个接口。
- 如果用户要求批量开发多个接口，Agent 仍需要在每个接口完成后给出短暂停点；除非用户明确说“本批接口全部完成后再统一 review”。
- Codex 不能弹出系统级模态窗口时，使用对话消息作为 review 提示，并停止后续工具调用。

子 Agent 代码风格一致性规则：

- 主 Agent 分配子 Agent 任务时，必须明确该子 Agent 的写入范围、代码风格、命名约定、接口契约和输出格式。
- 子 Agent 不允许自创一套目录结构、响应结构、错误码、trace 字段或命名风格。
- 同一语言内必须保持一致格式：Java 按 Controller / Service / Repository / DTO / Domain 分层，Python 按 api / services / schemas / rag / db 分层，前端按 pages / components / api / stores / types 分层。
- 同类接口的请求字段、响应字段、错误结构、分页结构、时间字段命名必须保持一致。
- RAG 相关代码的 trace 字段、prompt 命名、strategy 命名、retriever / reranker / generator 接口命名必须保持一致。
- 主 Agent 在合并子 Agent 结果后，必须做一次统一 review，检查码风、命名、跨服务契约和文档语言是否一致。
- 如果发现子 Agent 代码风格不一致，主 Agent 必须先整理一致，再交给用户 review。

### 9.11 当前重点 Review 文件

Java 后端优先 review：

- `backend-java/src/main/java/.../controller/RagController.java`
- `backend-java/src/main/java/.../service/RagService.java`
- `backend-java/src/main/java/.../client/AiServiceClient.java`
- `backend-java/src/main/resources/db/migration/`

Python RAG 优先 review：

- `ai-service/app/api/routes/rag.py`
- `ai-service/app/services/rag_service.py`
- `ai-service/app/rag/strategies/`
- `ai-service/app/rag/retrievers/`
- `ai-service/app/rag/rerankers/`
- `ai-service/app/rag/generators/`
- `ai-service/app/core/tracing.py`
- `ai-service/app/prompts/`

前端联调优先 review：

- `frontend/src/api/`
- `frontend/src/stores/`
- `frontend/src/pages/chat/`
- `frontend/src/components/SourceList.vue`
- `frontend/src/components/StrategySelector.vue`
- `frontend/src/components/UploadEntry.vue`

### 9.12 Agent 工作连续性与中断恢复规范

为了避免 token 不够、主 Agent 中断、子 Agent 停止工作或上下文丢失，每次复杂任务必须维护可恢复的交接信息。禁止只依赖聊天上下文保存项目状态。

每次任务开始前，Agent 必须先阅读：

1. `PROJECT_CONTEXT.md`
2. 当前任务对应的 `docs/plans/*`
3. 最近一次工作交接文档
4. 相关模块 README

复杂任务开始前，在 `docs/plans/` 下创建计划文档，包含：

- 当前目标。
- 涉及模块。
- 预计修改文件。
- 子 Agent 分工。
- 验证方式。
- 当前风险。

每次阶段性完成后必须写交接摘要，建议使用：

```text
docs/handoff/
├── CURRENT_STATE.md
└── YYYY-MM-DD-task-name.md
```

`docs/handoff/CURRENT_STATE.md` 始终记录最新状态：

- 当前正在做什么。
- 已完成什么。
- 哪些命令验证通过。
- 哪些命令失败，失败原因是什么。
- 哪些文件是重点 review 文件。
- 下一步建议从哪里继续。
- 是否有子 Agent 未完成任务。
- 是否有本地服务正在运行。

子 Agent 工作要求：

- 说明自己负责的模块。
- 列出修改的文件。
- 标出关键入口文件。
- 说明如何验证。
- 说明未完成事项。
- 说明风险点。
- 不允许只说“完成了”。

主 Agent 必须整合子 Agent 输出，形成中文总交付说明。

中断恢复流程：

1. 阅读 `PROJECT_CONTEXT.md`。
2. 阅读 `docs/handoff/CURRENT_STATE.md`。
3. 查看 `docs/plans/` 中当前任务计划。
4. 检查当前文件结构。
5. 运行最小验证命令。
6. 再继续开发。

禁止事项：

- 禁止只依赖聊天上下文保存项目状态。
- 禁止子 Agent 修改代码后不说明改动。
- 禁止跨模块大改但不写计划。
- 禁止验证失败却不记录原因。

### 9.13 文档、注释与复盘语言规范

本项目的主要学习目标是 RAG 技术沉淀，因此项目文档、计划、复盘和关键代码注释默认使用中文，方便后续 review、复习和二次迭代。必要的英文技术名词、命令、类名、接口路径和配置项可以保留英文。

以下内容必须使用中文描述：

- `PROJECT_CONTEXT.md`
- `README.md`
- 各模块 `README.md`
- `docs/plans/` 下的计划文档
- `docs/handoff/` 下的交接文档
- `docs/testing/failures/` 下的失败经验复盘
- `docs/architecture/` 下的架构说明
- RAG 策略说明、评估说明、实验对比说明
- 数据库迁移说明和关键表设计说明
- PR / 阶段总结 / 子 Agent 交付总结

代码注释默认使用中文，但注释密度按模块区分。RAG 相关代码可以写更详细的中文注释，包括：

- query rewrite 的目的和输入输出。
- retriever 的召回逻辑。
- hybrid search 的分数融合方式。
- reranker 的输入、输出和排序依据。
- prompt builder 的变量来源。
- context compression 的保留 / 丢弃规则。
- generator 如何约束引用来源。
- trace 记录了哪些关键字段。
- 评估指标的计算含义。
- 某个策略适合哪类文档，例如技术笔记、项目经验、招聘 JD。

非 RAG 代码注释保持简洁，只在以下情况补充：

- 业务规则不直观。
- 跨服务调用容易误解。
- 数据库字段或状态流转有约束。
- 前端交互状态有特殊处理。
- 为了兼容本地环境、框架限制或后续扩展做了特殊写法。

禁止写无意义注释，例如：

- “设置变量”。
- “调用方法”。
- “返回结果”。
- 对代码逐行翻译。

失败经验复盘规范：

- 每次测试、启动、构建、集成或 RAG 评估中遇到值得沉淀的问题时，在 `docs/testing/failures/` 下新增中文复盘文档。
- 复盘文档建议包含：问题现象、触发场景、报错信息摘要、根因分析、解决方案、后续避免方式、是否补充了自动化测试。
- 如果问题与本地环境有关，也要记录，例如 npm 缓存目录权限问题、Maven 本地仓库权限问题、Python 依赖版本与 Python 版本不兼容、Docker 未在 PATH 中、Vite 配置加载被沙箱限制。

Agent 输出规范：

- 每次 Agent 完成开发后，必须用中文输出本次完成了什么。
- 必须说明修改了哪些文件。
- 必须给出重点 review 顺序。
- 必须说明验证了什么。
- 必须说明哪些地方还只是占位实现。
- 必须给出下次继续建议。
- 如果使用子 Agent，主 Agent 必须把所有子 Agent 的结果整理成中文总交付说明。

### 9.14 模块 README 规范

每个一级模块都必须提供中文 README，用于帮助开发者快速理解模块职责、启动方式、关键代码入口和 review 顺序。

必须包含 README 的模块包括：

- `frontend/README.md`
- `backend-java/README.md`
- `ai-service/README.md`
- `infra/README.md`
- `scripts/README.md`
- 后续新增的重要模块目录

每个模块 README 建议包含：

- 模块职责。
- 技术栈。
- 目录结构说明。
- 本地启动方式。
- 常用命令。
- 环境变量说明。
- 关键代码入口。
- 重点 review 文件。
- 与其他模块的调用关系。
- 当前已实现能力。
- 当前占位实现。
- 后续待补能力。
- 常见问题。

各模块 README 重点：

- `frontend/README.md` 需要重点说明页面结构、API client 位置、路由结构、状态管理、如何对接后端接口、如何运行类型检查和构建。
- `backend-java/README.md` 需要重点说明 Controller / Service / Repository 分层、Java 后端如何调用 Python AI 服务、Flyway 迁移目录、`trace_id` 如何生成和透传、主要 API 路径、如何启动服务和运行测试。
- `ai-service/README.md` 需要重点说明 RAG 主链路、文档解析流程、retriever / reranker / generator / evaluator 的位置、Prompt 存放位置、trace 结构、MinerU PDF parser 预留位置、哪些是占位实现，哪些是真实逻辑。
- `infra/README.md` 需要重点说明 PostgreSQL / pgvector / Redis 本地依赖、Docker Compose 使用方式、数据卷说明、初始化 SQL 说明。
- `scripts/README.md` 需要重点说明每个脚本的用途、运行前置条件、是否会修改本地数据、是否有危险操作。

README 更新规则：

- 新增模块、修改模块启动方式、调整目录结构、改变跨服务调用方式时，必须同步更新对应模块 README。
- 如果 Agent 修改了某个模块但没有更新 README，需要在最终交付说明中明确说明原因。

## 10. 阶段目标

### Phase 0：项目初始化

状态：已完成

目标：完成 Monorepo 骨架、环境模板、基础 README 和开发约定。

### Phase 1：数据库与基础服务

状态：已完成

目标：完成 PostgreSQL + pgvector、Spring Boot、FastAPI 和 health check 骨架。

### Phase 2：知识库与文档入库

状态：已完成

目标：完成文档上传、基础解析、清洗、切分、embedding 和数据库入库链路。

### Phase 3：基础 RAG 问答

状态：已完成

目标：完成向量检索、问答接口、引用来源和基础聊天界面。

### Phase 4：Advanced RAG 策略

状态：已完成

目标：完成 hybrid search、rerank、query rewrite、multi-query、parent-child、metadata filter 与按文档类型选策略。

### Phase 5：LangGraph Agent 编排

状态：已完成

目标：完成问题分类、策略选择、追问、补救检索、assistant-turn 和学习闭环。

### Phase 6：GraphRAG / 知识图谱增强

状态：已完成

目标：完成实体/关系抽取、图谱事实持久化和前端查看入口。

### Phase 7：RAG 评估与实验平台

状态：已完成

目标：完成实验 CRUD、run 评估、历史记录、汇总与对比页。

### Phase 8：复习与面试辅助能力

状态：已完成

目标：完成复习计划、复习卡片、薄弱点练习、反馈与阶段性学习辅助。

### Phase 9：Coze 风格前端重构

状态：已完成本轮重构

目标：统一前端工作台的布局壳、视觉 token、页面密度和 README 口径，向 Coze Studio 风格收敛。

## 11. 当前待办

- [x] 确认第一版架构：采用 Vue + Spring Boot + FastAPI + PostgreSQL/pgvector 三服务架构
- [x] 创建项目基础目录
- [x] 初始化 Git 本地仓库
- [x] 初始化前端 Vue 项目
- [x] 初始化 Spring Boot 后端项目
- [x] 初始化 FastAPI AI 服务
- [x] 配置 PostgreSQL + pgvector
- [x] 编写第一版数据库设计文档
- [x] 完成 `POST /api/documents/upload` 单篇 JSON 文档入库 Demo，并按规则暂停 review
- [x] 增强 `GET /api/documents` 文档列表状态展示，并按规则暂停 review
- [x] 增强 `GET /api/documents/{id}` 文档详情与 chunk 摘要，并按规则暂停 review
- [x] 增强 `POST /api/documents/upload` multipart 单文件上传，并按规则暂停 review
- [x] 实现 Markdown / TXT / Word / PDF / Excel 入库 Demo（MinerU PDF + python-docx 已接入，真实 multipart 上传已闭环）
- [x] 调研并接入 MinerU 作为 PDF 提取工具
- [x] 实现基础向量检索 Demo
- [x] 实现第一版 RAG 对话接口
- [x] 将 `GET /api/rag/experiments` 从硬编码占位改为数据库读取
- [x] 实现 `POST /api/rag/experiments` 创建实验记录接口
- [x] 实现 `GET /api/rag/experiments/{id}` 查询实验详情接口
- [x] 实现 `PUT /api/rag/experiments/{id}` 更新实验记录接口
- [x] 实现 `DELETE /api/rag/experiments/{id}` 删除实验记录接口
- [x] 完成 RAG 实验接口数据库 + HTTP smoke 验证
- [x] 重构实验评估页面为评测集管理工具：持久化样本、标注管理、单样本评估、批量评估与历史查看
- [x] 配置远程 Git 仓库并推送 `main` 分支
- [x] 补齐 API 设计文档：Spring Boot `/api/*` 对外接口、FastAPI `/ai/*` 内部接口、前端调用映射
- [x] 补齐前端 API 模块：feedback.ts（新建）、chat.ts（会话/消息 CRUD）、experiments.ts（完整 CRUD）、knowledgeBases.ts（create）、rag.ts（新建）
- [x] 补齐前端 TypeScript 类型：ChatSession、ChatMessageRecord、FeedbackRecord、ExperimentRequest、RagRunDetail、RetrievalResult 等共 11 个
- [x] 修复前端 client.ts 错误提取路径对齐 Spring Boot `{error: {code, message}}` 结构
- [x] 前端 Store 升级：hydrate 部分失败容错、新增会话/实验/反馈/知识库/文档全部 actions
- [x] 前端页面补齐：ExperimentsPage 增删改 UI、SettingsPage 可编辑+localStorage、FeedbackPage 新建、ChatPage 会话管理面板
- [x] 前端路由补齐：/feedback 路由 + 侧边栏导航入口
- [x] 为文档解析引入异步任务模型（上传先返回 PROCESSING，前端轮询或新增任务状态接口）
- [x] 为 Spring Boot `/api/*` 请求补齐统一接口调用日志，并补充知识库创建 / 更新 / 删除操作日志
- [x] 为 Chat 问答建立单一业务接口（创建 user message → 调用 RAG → 保存 assistant message → 返回完整对话状态）
- [x] 将 LLM / embedding / reranker adapter 从 stub 升级为真实模型调用（OpenAI-compatible adapter，已按 DashScope 文档完成小流量 smoke）
- [x] 实现 Advanced RAG 策略（Hybrid Search、Rerank、Query Rewrite、Multi-query、Parent-Child 等；当前为工程闭环第一版）
- [x] 实现 LangGraph Agent 编排
- [x] 实现 GraphRAG / 知识图谱增强
- [x] 完成 Coze 风格前端工作台重构：全局壳、聊天三栏、管理页密度、移动端单栏与 `/api/*` 边界验证
- [ ] 后续增强：拆分 `ChatPage.vue`、收敛 `workbench` store、为关键 UI primitives 增加更细粒度组件化

## 12. 会话交接规则

每次开启新的开发对话时，建议先提供以下信息：

1. 当前最新的 `PROJECT_CONTEXT.md`
2. `docs/handoff/CURRENT_STATE.md`
3. 当前正在做的阶段
4. 上一次完成了什么
5. 当前遇到的问题或下一步目标
6. 当前重点 review 文件

每次完成任务后，需要更新：

- `项目状态`
- `阶段目标状态`
- `当前待办`
- `变更记录`
- `docs/handoff/CURRENT_STATE.md`
- 必要时更新目录结构、接口规划、数据库规划、迁移规范、测试策略、可观测性规范、RAG 策略规划和模块 README

## 13. 变更记录

### 2026-06-18

- 完成 RAGAS 测评集生成增强：`generate_ragas_testset_draft.py` 和 PowerShell 包装脚本支持 `rule / llm / ragas / auto` 四种模式；LLM 模式复用现有 adapter 生成复杂题型，RAGAS 模式懒加载 `TestsetGenerator` 和 LangChain 模型，保持主 FastAPI 服务热路径不引入 RAGAS / Pydantic v2 依赖。
- 完成 RAGAS 离线评估结果回填：`export_ragas_dataset.py` 保留 evaluation / run / experiment 定位元数据，`run_ragas_evaluation.py` 可选调用 Spring Boot `PUT /api/rag/experiment-evaluations/ragas-report` 回填 `ragasScores`、指标名、RAGAS 版本、裁判模型和报告 URI；Spring Boot 追加 Flyway 迁移、Entity / DTO / Repository / Service / Controller 支持，并收紧非 `evaluationId` 回填必须提供 `runId + experimentId`。
- 完成 React 实验页页面内人工审核流：支持按待审、已通过、已拒绝筛选，逐条编辑问题、标准答案、证据 chunk ID、备注和召回数量，并通过 Spring Boot `/api/rag/evaluation-cases/{id}` 保存通过 / 拒绝 / 待审状态；React 导入解析兼容 `{ experimentId, items }` 包装层，并与 Python finalize 的审核决策优先级保持一致。
- 补齐 React 实验页删除能力：页面内支持删除单条样本、删除最近导入样本、删除当前筛选样本和删除当前实验，所有危险操作均有确认提示，并复用 Spring Boot `/api/rag/evaluation-cases/{id}` 与 `/api/rag/experiments/{id}` 删除接口。
- 新增售后多 Agent supervisor 架构计划：建议采用受控 Supervisor + 显式状态图 + 强制安全闸门，拆分澄清、检索、代码/日志分析、诊断、风险审查、工单升级和评估审查 7 个节点；先保持 Pydantic v1 兼容和本地状态图实现，后续再按依赖条件迁移 LangGraph runtime。
- 完成售后 Support Supervisor 多 Agent 第一版开发：AI 服务新增本地状态图和 7 个专业节点，售后请求自动走 `SupportSupervisorWorkflow`，信息不足时提前澄清，含日志/错误码/trace id 时触发代码/日志分析，高风险或证据不足时生成工单升级草稿，最终强制经过风险审查和评估审查；普通 `study-agent` 继续走旧 workflow。
- 继续加固售后 Agent：补真实 UTF-8 中文售后/故障/风险关键词识别，风险审查会扫描用户输入、RAG 原始回答、诊断步骤和最终草稿，评估审查改为审查已生成的草稿回答；无 citation 即使已升级也会标记为待人工复核，并为通过/失败场景生成可导入人工审核流的 `candidate_eval_case` 草稿。
- 修复代码审查发现的关键风险：RAGAS 生成结果缺少项目 chunk ID 时不再按行号伪造 gold evidence，而是标记 `evidence_needs_review` 并要求人工补证据；前端审核保存会保留原有 `relevantChunkIds` / `expectedCitationChunkIds`，避免只点保存就丢失 gold label。
- 关键文档：`docs/plans/2026-06-18-ragas-testset-generation-report-review-flow.md`、`docs/plans/2026-06-18-support-supervisor-multi-agent-workflow.md`、`docs/reviews/2026-06-18-ragas-testset-generation-report-review-flow-review-prompt.md`、`docs/reviews/2026-06-18-react-evaluation-delete-actions-review-prompt.md`、`docs/reviews/2026-06-18-support-supervisor-multi-agent-workflow-review-prompt.md`、`scripts/README.md`。
- 验证通过：`ai-service\.venv\bin\python.exe -m pytest ai-service\tests\test_ragas_bridge.py ai-service\tests\test_ragas_testset_generation.py -q`、`mvn.cmd -f backend-java/pom.xml test`、`npm.cmd --prefix frontend-react run typecheck`、`npm.cmd --prefix frontend-react run build`。

### 2026-06-17

- 新增 RAGAS 评估体系第一阶段：AI 服务增加 RAGAS bridge，将现有 `RagEvaluateRequest` 映射为 `user_input`、`retrieved_contexts`、`response`、`reference`、`retrieved_context_ids` 和 `reference_context_ids`；RAGAS 依赖保持懒加载，避免 Pydantic v2 与当前 FastAPI/Pydantic v1 主服务冲突。
- 新增测评集草稿生成与人工半自动审核脚本：可从已上传文档生成的 `document_chunks` 或离线 chunk JSON 生成 `DRAFT` 样本 JSON，并同步输出带 `humanDecision` / `humanNotes` 的审核 CSV；草稿字段对齐现有 Spring Boot `rag_evaluation_cases` 导入 schema。
- 新增离线 RAGAS 执行入口：`export_ragas_dataset.py` 导出 RAGAS JSONL，`run_ragas_evaluation.py` 在独立 RAGAS 环境中运行默认 ID-based metrics，根目录 PowerShell 包装脚本便于 Windows 本地使用；验证 RAGAS bridge、草稿生成和既有 strategy comparison 测试通过。
- 新增企业售后技术支持知识库 Agent 第一版编排：AI 服务在 support / after-sales / technical-support 场景下默认进入售后模式，路由到 `advanced-rag`，生成结构化 `supportPlan`；Spring Boot DTO 和 assistant-turn 响应已透传 `supportPlan`，保持 Java 只做桥接不实现诊断逻辑。
- 完成 `frontend-react/` 售后支持工作台中文化与美学优化：对话页新增知识库选择、售后模式变量、示例故障问题和结构化 `supportPlan` 诊断卡片；全局导航、文档中心、评测页、图谱页和设置页继续中文化；色彩 token 收敛到冷灰 / 深青 / 告警橙，并修复 Vite dev/build root 显式配置。验证 React typecheck、build 和 Playwright + Edge stub 后端渲染通过。
- 完成 chunk 切分与检索三项优化并升级为动态策略：AI 服务入库不再使用全局唯一默认，而是按文档类型和文件类型路由，技术笔记/课程/开发经验/项目经验等长文档走 `parent-child`，表格文件走 `table-row-group`，招聘 JD 走 `recursive-overlap`，显式 `chunk_strategy` 仍可覆盖；查询侧按问题类型决定 Advanced RAG 是否启用 Parent-Child 上下文，概念/实现/排障/面试/总结/对比类问题启用，事实查找默认保持 chunk 级精确召回；chunk metadata 新增 heading-aware `embedding_text`、`block_type`、`quality_score` 和 `low_quality_reasons`，Advanced RAG 在 parent-child 模式下按 `parent_chunk_id` 聚合 child 命中并扩展 parent 上下文，降低图片说明、目录、prompt 示例和弱 OCR 对召回排序的污染。
- 补充 parent-child 入库自动降级：当文档总长度过短或章节长度整体低于 child 阈值时，AI 服务会把自动路由到的 `parent-child` 降级为 `recursive-overlap`，避免短文档生成内容重复的 parent/child 块；显式 `chunk_strategy=parent-child` 仍保持原行为。新增 `ingest_service` trace 字段记录 `requested_chunk_strategy`、`resolved_chunk_strategy` 和降级原因，并补充短文档降级测试。
- 修复 parent-child chunker 层的一父一子内容一致问题：即使显式 `chunk_strategy=parent-child`，当某个 parent 只能切出一个与 parent 内容完全相同的 child 时，也会降级为单条 `recursive-overlap` child chunk，metadata 记录 `parent_child_downgrade_reason=single-child-identical-parent`；同时对同章节重复 chunk 内容做去重，避免重复模板段落产生多条相同 chunk。
- 修复 DOCX 表格上传失败时错误被吞的问题：`DocxParser` 不再静默吞掉 `python-docx` 缺失、base64 损坏或 DOCX zip 解析失败，而是抛出带 `python-docx-unavailable` / `docx-parse-failed` 的明确异常；本地项目虚拟环境可正常解析 `03_docx_tables.docx`，日志中的 `C:\Users\admin\PyCharmMiscProject\.venv` 缺少 `docx` 依赖是此次空内容报错的直接原因。
- 增强 DOCX 表格解析输出：保留原 Markdown pipe table 的同时新增 `Table N Rows` 行坐标描述，按 `R行C列=值` 展开单元格；嵌套表格会递归写入所在单元格，横向合并单元格会标记 `continues into C...`，提升复杂表格 chunk 的检索可读性。
- 调整 MinerU PDF 轮询默认参数：`MINERU_POLL_TIMEOUT_SECONDS` 默认从 120 秒提升到 300 秒，`MINERU_POLL_INTERVAL_SECONDS` 默认从 2 秒调整为 5 秒，减少日志刷屏并给标准 API 更充分的解析时间；两个参数均可通过环境变量覆盖。
- 修复 MinerU 标准 batch 上传后的轮询端点错误：`/api/v4/file-urls/batch` 返回的是 `batch_id`，现在文件上传模式会轮询 `/api/v4/extract-results/batch/{batch_id}` 并读取 `extract_result[0]` 的 `state`、`full_zip_url` 和失败原因，避免把 `batch_id` 当单任务 id 查询 `/api/v4/extract/task/{batch_id}` 后一直吞掉错误并超时。
- 增强 MinerU 完成态结果下载：当 batch 完成但 `full_zip_url` / `markdown_url` 不在 `extract_result[0]` 中时，会继续从 batch 顶层 `data` 和嵌套字段递归查找 zip / markdown 链接；zip 中没有 `.md` 时会尝试解析 MinerU 常见的 `content_list.json`，并在空内容错误中带上 `status` 与 `last_poll_error`。
- 修复 MinerU 结果 zip 下载受系统代理影响的问题：保留提交、上传和轮询阶段继承环境代理，但下载 `full_zip_url` / `markdown_url` 时使用独立 `httpx.AsyncClient(trust_env=False)`，绕开本机代理变量导致的 `cdn-mineru.openxlab.org.cn` `ConnectError`；本地探针验证 API 通、轮询 done、关闭代理后 zip 下载 HTTP 200。
- 完成 chunk 优化优先级第 1 项：Excel / CSV 表格类文件自动路由到 `table-row-group`，新增 `TableRowGroupChunker` 按表头和行组生成 chunk，内容包含 sheet、columns 和逐行 `column=value`，metadata 保留 `sheet_name`、`row_range`、`row_start`、`row_end`、`column_names`、`row_group_index` 与 `block_type=table_rows`；默认 `table_row_group_size=25`，可由上传 metadata 覆盖。
- 修复 XLSX 入库后 RAG context 显示 ZIP/XML 乱码的问题：`SpreadsheetParser` 现在直接从 `.xlsx` 的 OpenXML 包读取 workbook、sharedStrings 和 worksheet XML，生成结构化 `spreadsheet_tables`，`TableRowGroupChunker` 优先使用该结构按 sheet 与真实行号生成 `Sheet / Columns / Row` context；文档级 metadata 仅保留表数量和 sheet 摘要，避免大表结构写入 documents metadata。
- 统一文档上传 multipart 默认上限为 50MB：Spring Boot 新增 `DOCUMENT_UPLOAD_MAX_FILE_SIZE` / `DOCUMENT_UPLOAD_MAX_REQUEST_SIZE` 环境变量默认值，并同步 `.env.example` 与后端 README；React 上传入口已是 50MB，Vue 仅保留上一项 50MB 校验，不参与本次 XLSX 前端入口调整。
- 完成后续 chunk 切分优化：Markdown recursive-overlap 支持 block-aware 原子块，fenced code block 不拆分且图片引用单独标记；DOCX 解析保留 Word 标题层级和表格结构；MinerU PDF 完成态 metadata 增加 heading、image、table、code、formula、page marker 统计；面试经验默认路由到 `qna-pair` 并按问答对切分；代码片段默认路由到 `code-aware` 并按 fenced code block 或顶层函数/类/方法符号切分。
- 修复 React Chat 页面发送消息后引用侧栏崩溃：`ChatPage` 现在会将后端 `citations` 中的 `chunk_id` / `chunkId` / `document_id` / `documentId` 等原始来源对象归一化为前端 `CitationSource`，避免缺失 `id` 时触发 `Cannot read properties of undefined (reading 'slice')`；验证 React typecheck 与 build 通过。
- 完成 `RAG相关` 文件夹测评集 schema 对齐：`datasets/processed/rag-folder-evaluation-cases-20260616.json` 的 18 条样例已补齐 `requiredChunkIds`、`supportingChunkIds`、`acceptableChunkIds`、`citationChunkIds`，并同步旧兼容字段 `relevantChunkIds` / `expectedCitationChunkIds`；通过 PostgreSQL 真实数据校验 65 个唯一 chunk ID 与 22 个文档 ID 均存在。
- React 实验评估页面完成三类 Recall 展示适配：Leaderboard、Batch 结果、Recent Evaluations 和策略对比页统一展示 `evidenceRecallAtK`、`chunkRecallAtK`、`documentRecallAtK`，并保留 Precision、MRR、Citation 指标；评测样本详情新增 required / supporting / acceptable / citation / relevant document 分层标注展示。
- 验证 `npm.cmd --prefix frontend-react run typecheck`、`npm.cmd --prefix frontend-react run build`、`mvn.cmd -f backend-java/pom.xml test`、`ai-service/.venv/bin/python.exe -m pytest tests/test_strategy_comparison_evaluator.py` 通过。

### 2026-06-16

- 完成文档上传链路升级：前端上传入口支持单篇、多篇和文件夹上传，文件夹上传会把浏览器 `webkitRelativePath` 传给 Spring Boot 并保存为 `sourcePath`。
- Spring Boot 新增 `POST /api/documents/upload/batch`，按文件创建多条 `PROCESSING` 文档记录，并保留原有 `POST /api/documents/upload` JSON / multipart 单篇上传兼容。
- 文档入库任务新增 `DocumentIngestDispatcher`：默认 `DOCUMENT_INGEST_MODE=local` 使用 Spring `@Async` 线程池；配置为 `rabbitmq` 时发布 `DocumentIngestMessage` 到 RabbitMQ 并由 listener 消费。
- 当前 RabbitMQ 消费者仍在 Spring Boot 内调用 FastAPI `/ai/ingest/document`，FastAPI 继续只负责单文档解析、切分、embedding 与 RAG 派生数据写入；后续可在相同消息结构上替换为 Python Celery/RQ worker。
- 完成 `RAG相关` 文件夹测评集 chunkId 二次审计：`datasets/processed/rag-folder-evaluation-cases-20260616.json` 已收紧 18 条样例的 `relevantChunkIds` / `expectedCitationChunkIds`，移除目录、图片说明、GraphRAG 关系表和 prompt 示例数据等弱证据 chunk，并通过数据库存在性与文档归属校验。
- 实验评估页支持导入评测集后自动运行一次 RAG 全链路并写入评估结果；修复本地文件选择后“导入到当前实验”按钮因未选择左侧实验筛选而不可点击的问题，并补充 chunk 证据查询 SQL。
- 新增 `frontend-react/` React + TypeScript 并行迁移工作区：按 Stitch RAG Knowledge Studio 页面实现 Workbench shell、文档中心、实验评估、评估对比、对话、知识库、图谱、反馈和设置第一版。
- React 文档中心支持单文件、多文件和文件夹上传，保留 `relativePath` 并通过 Spring Boot `/api/documents/upload/batch` 提交；实验页支持导入 JSON / CSV 测评集后自动触发 batch RAG run。
- React 迁移已通过 `npm.cmd --prefix frontend-react run typecheck` 与 `npm.cmd --prefix frontend-react run build`；审查 agent 发现的导入后自动运行旧 state 闭包问题已修复。
- 完成 React 工作台真实链路 QA：修复 Spring Boot CORS 白名单遗漏 `localhost:5174` 导致 React POST 写请求 403 的问题，修复文档中心误用 `default-kb` 兜底导致批量上传传入非法 UUID 的问题；使用真实 Spring Boot + FastAPI stub + PostgreSQL 验证 `RAG相关` 文件夹上传 39 个支持文件并进入异步解析，以及评测集导入后自动 batch RAG run 18/18 成功。
- 完成 `frontend-react/` Stitch 视觉二次对齐：重做全局 Workbench shell、Material Symbols 图标体系、知识库 Pipeline 卡片、GraphRAG 画布、Chat 三栏 trace 面板，并增强实验页 leaderboard / pipeline health 首屏；文档中心保持既有上传功能并收敛到 Stitch 数据入库布局。验证 `npm.cmd --prefix frontend-react run typecheck` 与 `npm.cmd --prefix frontend-react run build` 通过，并用 Edge headless 截图检查 `/chat`、`/knowledge-base`、`/documents`、`/experiments`、`/graph`。
- 完成 RAG 评估指标口径升级：评测集 schema 新增 `requiredChunkIds`、`supportingChunkIds`、`acceptableChunkIds`、`citationChunkIds` 并兼容旧 `relevantChunkIds` / `expectedCitationChunkIds`；Evaluator 将 Recall 拆为 `chunkRecallAtK`、`documentRecallAtK`、`evidenceRecallAtK`，旧 `recallAtK` 保持为 evidence recall 兼容别名；`precisionAtK` 分母改为实际返回结果数，避免请求 topK 大于实际 citation 数时被硬性压低。新增 Flyway 迁移落库三类 recall 与分层标注字段，验证 Java / AI evaluator / React typecheck 与 build 通过。
- 关键文档：`docs/plans/2026-06-16-multi-document-folder-upload-async-queue.md`、`docs/plans/2026-06-16-react-stitch-frontend-rebuild.md`、`docs/reviews/2026-06-16-multi-document-folder-upload-async-queue-review-prompt.md`、`docs/reviews/2026-06-16-react-stitch-frontend-rebuild-review-prompt.md`、`docs/handoff/CURRENT_STATE.md`。

### 2026-06-15

- 完成 Advanced RAG preset 评测增强：将 `hybrid-rerank`、`metadata-filter`、`parent-child`、`advanced-rag`、`graph-rag` 收敛为统一 preset 配置，并支持按同一批评测样本批量生成 RAG run 后评估。
- 评测历史新增结构化指标和运行成本维度：`recall@k`、`precision@k`、`MRR`、`citation_hit`、GraphRAG 指标、token usage、estimated cost、embedding / retrieval / rerank / LLM latency。
- AI 服务 trace 会汇总真实 provider `usage` 和分阶段耗时；Java 只负责从 trace 中提取并持久化，不实现 RAG / evaluator 算法。
- 前端 RAG 对比页展示策略聚合的 Recall、Precision、MRR、Citation、Tokens、Cost 和阶段耗时，便于做可量化 RAG 优化闭环。
- 完成默认 chunk 切分升级：`SimpleChunker` 改为 `recursive-overlap` 递归切分，优先按标题、段落、句子和字符窗口切分；`ParentChildChunker` 改为章节感知 parent / child 切分，子块保留 overlap 和章节 metadata；同时保留显式 `simple-window` 兼容路径。
- chunk metadata 新增 `chunk_algorithm`、`chunk_size`、`chunk_overlap`、`char_start`、`char_end`、`split_level`、`heading_path`、`section_index`、`section_title`、`parent_heading`、`child_index_in_parent` 等字段，便于后续做评测和检索归因。
- 已补充 `ai-service/tests/test_parent_child_chunker.py` 覆盖默认 recursive-overlap、显式 simple-window 兼容和章节化 parent-child 行为。
- 关键文档：`docs/plans/2026-06-15-advanced-rag-preset-evaluation-runner.md`、`docs/plans/2026-06-15-recursive-overlap-parent-child-chunking.md`、`docs/reviews/2026-06-15-rag-evaluation-token-cost-observability-review-prompt.md`、`docs/handoff/CURRENT_STATE.md`。

### 2026-06-10

- 修复 PDF 经 MinerU 解析超时后仍被标记为入库成功的问题：AI 服务现在拒绝空解析文本和 0 chunk 结果，Java 异步入库也会把 `chunk_count <= 0` 视为失败并写回 `FAILED`；新增 `docs/testing/failures/2026-06-10-mineru-pdf-zero-chunk-indexed-notes.md` 记录根因和验证。
- 完成实验评估页到评测集管理工具的重构：新增 `rag_evaluation_cases` 持久化模型和 `/api/rag/evaluation-cases` 系列接口，`/experiments` 支持样本创建、编辑、归档、删除、筛选、单样本评估、批量评估和历史查看。
- case-based 评估支持临时覆盖标准答案，后端单元测试覆盖样本标签、topK、期望引用与标准答案覆盖透传；验证 `mvn.cmd -f backend-java/pom.xml test`、`npm.cmd --prefix frontend run typecheck`、`npm.cmd --prefix frontend run build` 通过。
- 完成前端 Coze 风格工作台重构：`WorkbenchLayout` 改为窄主导航 + 二级侧栏 + 顶栏，`styles.css` 统一为浅色 IDE token，`ChatPage` 形成三栏会话工作台，文档 / 知识库 / 图谱 / 实验 / 反馈 / 设置页统一为两栏或三栏工作台密度。
- 验证 `frontend` 类型检查与构建通过；使用 Edge headless 检查 `/chat` 桌面与移动端、`/documents`、`/experiments`、`/graph`、`/settings` 预览截图。
- 前端边界检查通过：页面未直接调用 `/ai/*`，浏览器请求仍经由统一 API client 进入 Spring Boot `/api/*`；`SettingsPage` 文案回收为后端桥接诊断口径。
- 关键文档：`docs/plans/2026-06-09-chat-workbench-layout-refactor.md`、`docs/plans/2026-06-09-coze-inspired-frontend-refactor-prep.md`、`docs/reviews/2026-06-10-coze-workbench-frontend-refactor-review-prompt.md`。

### 2026-06-09

- 完成后端接口日志与 trace 统一：Spring Boot 统一记录 `/api/*` 调用日志，FastAPI 与前端的 `X-Trace-Id` 贯通，Agent 内部 RAG run 也可持久化回查。
- 统一数据库环境变量为 `DB_URL`、`DB_USERNAME`、`DB_PASSWORD`；AI 服务从 JDBC URL 推导 Python PostgreSQL URL，避免回退到内存模式。
- 修复文档异步入库使用保存前 `documentId` 的问题，延长知识库对话 AI 调用超时，并补齐 Java / FastAPI 关键请求日志。
- 完成 Coze 风格前端重构准备：确认参考边界、Figma 工具限制、多 agent 分工和第一阶段工作台重构方向。

### 2026-06-08

- Advanced RAG 工程闭环第一版完成，覆盖 hybrid-rerank、metadata-filter、parent-child、query rewrite、multi-query、query-aware compression 和请求级检索权重。
- OpenAI-compatible LLM / embedding / rerank adapter 接入并完成小流量 smoke；查询改写改为自然主问题，多查询扩展承载语义扩展。
- Agent 与学习闭环完成，覆盖问题分类、策略选择、assistant-turn、追问、学习计划、复习卡片、薄弱点练习和自动评分。
- GraphRAG 与评估体系完成，覆盖实体/关系持久化、图谱事实前端入口、run 评估、评估历史、汇总接口与对比页。
- 新增本地全链路脚本 `scripts/test-fullchain-local.ps1`，覆盖 Spring Boot -> FastAPI -> RAG 的非 Docker 验证路径。

### 2026-06-05

- 前端 API、TypeScript 类型、Pinia store、页面和路由补齐，`/feedback`、实验 CRUD、知识库 CRUD、聊天会话与 RAG run 详情形成统一前端调用面。
- `client.ts` 错误提取对齐 Spring Boot `{error: {code, message}}` 结构，`hydrate()` 支持部分失败容错。

### 2026-06-04

- 新增 `docs/architecture/api-design.md`，沉淀 Spring Boot `/api/*` 对外接口、FastAPI `/ai/*` 内部接口、统一响应结构、核心字段和前端调用映射。
- 明确前端只调用 Spring Boot，Spring Boot 只做业务 / 桥接 / 持久化，FastAPI 负责 AI / RAG / Agent / GraphRAG / evaluator 逻辑。

### 2026-05-31

- Word `.docx` 解析器接入 `python-docx`，支持 base64 `.docx` 段落和表格文本提取。
- MinerU PDF 解析器从预留 stub 升级为 v2，支持 URL / base64 提交、轮询和 Markdown 下载。

### 2026-05-29

- 文档入库链路完成：`POST /api/documents/upload` 支持 JSON 与 multipart，`GET /api/documents` 和 `GET /api/documents/{id}` 展示状态、解析器、chunk 数量与摘要。
- 知识库 CRUD、文档删除、`chunks=[]` 修复、documentType 枚举修复和全链路 HTTP smoke 相继完成。
- 前端完成上传入口、文档列表/详情、基础工作台视觉升级，并记录对应计划、review 与失败复盘文档。

### 2026-05-27

- RAG 实验接口完成数据库 CRUD 与 HTTP smoke；完成本地 `.env` 模板、数据库设计文档、Git 远程仓库配置与 `main` 分支推送。
- `PROJECT_CONTEXT.md` 维护规则调整为“阶段摘要 + 文档索引”，接口级细节沉淀到 `docs/plans/`、`docs/reviews/`、`docs/testing/failures/` 和 `docs/handoff/`。

### 2026-05-26

- Basic RAG 主链路第一版完成：Spring Boot `POST /api/rag/query` 调用 FastAPI `/ai/rag/query`，FastAPI 从 PostgreSQL + pgvector 检索并返回答案、引用和 trace。
- AI 服务新增数据库 repository、`DatabaseRetriever`、chunk / embedding 写入与混合检索；Spring Boot 保存 `rag_runs` 与 `rag_retrieval_results`。
- README 中文化、当前交接文档、基础测试和失败复盘完成。

### 2026-05-25

- 创建项目上下文文档，明确项目目标、技术栈、目录结构、开发规范、文档命名、review 规则和子 Agent 协作规则。
