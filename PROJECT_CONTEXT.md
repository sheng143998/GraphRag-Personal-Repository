# 本地知识库 Agent 项目上下文

更新时间：2026-05-27  
项目状态：Phase 3 基础 RAG 后端链路已形成第一版闭环，Phase 7 RAG 实验平台已完成实验记录 CRUD 与本地 HTTP smoke；Phase 2 文档入库与前端完整对齐待继续  
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
| 面试经验 | Query Expansion + Rerank + Answer Template |
| 代码片段 | Keyword Search + Metadata Filter + 精确引用 |
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

### 9.9 Plan 文档规范

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

Plan 文档不需要写时间线，也不需要写回滚计划。实现过程中如果发现计划明显不准确，需要更新计划或在最终变更记录中说明偏差原因。

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

目标：

- 创建 Monorepo 基础目录
- 初始化 Git
- 创建基础 README
- 创建 `.env.example`
- 创建 Docker Compose
- 确认是先走完整三服务架构，还是先用 Vue + FastAPI 快速起步

完成标准：

- 本地能看到清晰目录结构
- 文档和环境配置初步齐全
- PostgreSQL 服务可启动

### Phase 1：数据库与基础服务

状态：已完成

目标：

- 配置 PostgreSQL + pgvector
- 设计知识库、文档、chunk、会话相关表
- 搭建 Spring Boot 基础项目
- 搭建 FastAPI 基础项目
- 提供 health check

完成标准：

- 数据库可连接
- 后端服务可启动
- AI 服务可启动
- 基础接口可访问

### Phase 2：知识库与文档入库

状态：进行中

目标：

- 实现文档上传
- 实现 Markdown / TXT / Word / PDF / Excel 初始解析
- PDF 提取工具可使用 MinerU
- 实现文本清洗
- 实现基础 chunk 切分
- 生成 embedding
- 存入 PostgreSQL + pgvector

完成标准：

- 能上传一批本地技术笔记、招聘 JD 或项目资料
- 能解析 Markdown、TXT、Word、PDF、Excel 等常见格式
- 能在数据库中看到文档、chunk、embedding
- 能根据 metadata 查询文档内容

### Phase 3：基础 RAG 问答

状态：进行中

目标：

- 实现向量检索
- 实现基础 Prompt
- 实现问答接口
- 返回答案和引用来源
- 前端实现基础聊天界面

完成标准：

- 可以围绕本地知识库提问
- 回答能展示引用来源
- 能保存对话历史

### Phase 4：Advanced RAG 策略

状态：未开始

目标：

- 实现 Hybrid Search
- 实现 Rerank
- 实现 Query Rewrite
- 实现 Multi-query Retrieval
- 实现 Parent-Child Retrieval
- 实现 Metadata Filter
- 为不同文档类型选择不同策略

完成标准：

- 前端或配置中可以选择 RAG 策略
- 每次回答记录使用的策略
- 能对比不同策略的检索结果

### Phase 5：LangGraph Agent 编排

状态：未开始

目标：

- 建立基础 LangGraph 工作流
- 实现问题分类节点
- 实现策略选择节点
- 实现上下文质量检查节点
- 实现回答校验节点
- 支持必要时重新检索

完成标准：

- Agent 能根据问题自动选择检索路径
- 检索质量不足时能触发补救流程
- 每个节点的执行过程可追踪

### Phase 6：GraphRAG / 知识图谱增强

状态：未开始

目标：

- 从文档中抽取实体和关系
- 存储实体、关系和来源 chunk
- 建立技术概念图谱
- 支持图检索辅助回答
- 支持概念关联追问

完成标准：

- 能查看某个技术点相关概念
- 能回答跨文档、跨主题的问题
- 图检索结果可解释

### Phase 7：RAG 评估与实验平台

状态：进行中

目标：

- 建立固定评估问题集
- 记录命中率、相关性、答案质量
- 对比不同 chunk 策略
- 对比不同 embedding 模型
- 对比不同 retriever / reranker
- 前端展示实验结果

完成标准：

- 每次策略变化都可以量化比较
- 能看到检索结果和最终答案的差异
- 项目成为可持续练习 RAG 的实验台

### Phase 8：复习与面试辅助能力

状态：未开始

目标：

- 根据知识库生成复习题
- 根据技术栈生成面试题
- 针对用户回答进行追问
- 记录薄弱知识点
- 生成阶段性复习计划

完成标准：

- 系统能主动帮用户复习
- 能围绕项目经验进行模拟面试
- 能根据历史表现推荐复习重点

## 11. 当前待办

- [x] 确认第一版架构：采用 Vue + Spring Boot + FastAPI + PostgreSQL/pgvector 三服务架构
- [x] 创建项目基础目录
- [x] 初始化 Git 本地仓库
- [x] 初始化前端 Vue 项目
- [x] 初始化 Spring Boot 后端项目
- [x] 初始化 FastAPI AI 服务
- [x] 配置 PostgreSQL + pgvector
- [ ] 编写第一版数据库设计文档
- [ ] 实现 Markdown / TXT / Word / PDF / Excel 入库 Demo
- [ ] 调研并接入 MinerU 作为 PDF 提取工具
- [x] 实现基础向量检索 Demo
- [x] 实现第一版 RAG 对话接口
- [x] 将 `GET /api/rag/experiments` 从硬编码占位改为数据库读取
- [x] 实现 `POST /api/rag/experiments` 创建实验记录接口
- [x] 实现 `GET /api/rag/experiments/{id}` 查询实验详情接口
- [x] 实现 `PUT /api/rag/experiments/{id}` 更新实验记录接口
- [x] 实现 `DELETE /api/rag/experiments/{id}` 删除实验记录接口
- [x] 完成 RAG 实验接口数据库 + HTTP smoke 验证
- [ ] 配置远程 Git 仓库并推送 `main` 分支

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

### 2026-05-25

- 创建项目上下文文档
- 明确项目目标、技术栈、推荐架构、目录结构、开发规范和阶段目标
- 新增两份 Agent 项目上下文文档学习参考：`docs/reference/onyx-agents-cn.md` 与 `docs/reference/cognee-claude-cn.md`
- 补充 Agent 关键规则、数据库与迁移规范、测试策略、日志与可观测性、LLM 调用规范和 Plan 文档规范
- 在建议目录结构中新增 `docs/plans/`、`docs/testing/failures/`、`docs/experiments/eval-questions.md` 与 `ai-service/app/prompts/`
- 补充招聘 JD 文档类型、常见文档格式支持范围，并明确 PDF 提取工具可使用 MinerU
- 补充代码审查与关键链路说明规范、重点 review 文件清单、Agent 中断恢复规范、中文文档/注释/复盘规范和模块 README 中文规范
- 补充接口级 review 暂停规则：每完成一个接口后必须在 Codex 对话中提示用户 review，并等待确认后再继续
- 补充子 Agent 代码风格一致性规则：并行开发后必须由主 Agent 统一码风、命名、接口契约和 trace 结构

### 2026-05-26

- 完成 Basic RAG 主链路第一版：Spring Boot `POST /api/rag/query` 真实调用 FastAPI `/ai/rag/query`，FastAPI 从 PostgreSQL + pgvector 检索 chunk，并返回 answer、citations 和 trace。
- AI 服务新增数据库 repository 与 `DatabaseRetriever`，支持文档 chunk、embedding 写入，以及基于向量分数和关键词分数的混合检索。
- Spring Boot 保存 `rag_runs` 和 `rag_retrieval_results`，并将 retrieval metadata 调整为结构化 `Map<String, Object>` 以匹配 JSONB。
- 默认关闭 Java AI mock：`AI_SERVICE_MOCK_ENABLED=false`，本地联调默认走真实 FastAPI 服务。
- 新增 Basic RAG 计划文档：`docs/plans/2026-05-26-basic-rag-pipeline.md`。
- 新增 RAG review 提示文档：`docs/reviews/2026-05-26-basic-rag-review-prompt.md`，记录接口路径、涉及文件、调用链路、重点 review 顺序、验证命令和当前占位实现。
- 新增失败经验复盘：`docs/testing/failures/2026-05-26-basic-rag-dev-failures.md`，记录 Maven 依赖、数据库连接、Python 驱动、Pydantic 版本、JSONB 类型、PowerShell JSON 转义和完整联调耗时等问题。
- 新增当前交接状态：`docs/handoff/CURRENT_STATE.md`，记录已完成内容、验证结果、重点 review 文件、占位实现和下一步建议。
- 已验证：Python compileall、Python pytest、Java `mvn test`、后端健康检查、AI 服务数据库 smoke、完整 Spring -> FastAPI -> PostgreSQL HTTP 联调。
- 当前仍是占位：LLM generator、embedding、reranker 仍为 stub；真实文件上传、多格式解析、MinerU PDF 解析、Advanced RAG 和前端完整对齐尚未完成。
- 修复模块 README 中文化：更新根目录、AI 服务和计划目录 README，新增 `frontend/README.md`、`backend-java/README.md`、`infra/README.md`、`scripts/README.md`，并补充 `docs/reviews/2026-05-26-readme-localization-review-prompt.md` 与 `docs/testing/failures/2026-05-26-readme-localization-notes.md`。

### 2026-05-27

- 完成 AI 服务环境配置定位：确认 `ai-service/` 没有独立 `.env`，配置入口为 `ai-service/app/core/config.py`，运行时读取 `AI_DATABASE_URL`、`DATABASE_URL` 和 `AI_RAG_USE_DATABASE`。
- 完成 RAG 实验接口阶段能力：新增 `rag_experiments` 表，Spring Boot 支持实验记录列表、创建、详情、更新和删除。
- 完成本地配置与联调验证：创建根目录本地 `.env` 空字段文件，由用户自行补全真实数据库连接信息；使用本地 PostgreSQL 完成 Spring Boot Flyway 迁移和 RAG 实验接口 HTTP smoke，验证列表、创建、详情、更新、删除和删除后 404 全链路通过。
- 维护规则调整为“阶段摘要 + 文档索引”：`PROJECT_CONTEXT.md` 不再记录接口级流水账，接口级计划、review、失败复盘和交接细节分别沉淀在 `docs/plans/`、`docs/reviews/`、`docs/testing/failures/` 和 `docs/handoff/`。
- 完成项目阶段状态校准与 Git 本地仓库初始化准备：将 Phase 0、Phase 1 标记为已完成，Phase 2、Phase 3、Phase 7 标记为进行中；远程仓库推送等待用户提供仓库 URL。
- 关键文档索引：
  - RAG 实验接口：`docs/plans/2026-05-27-rag-experiments-list.md`、`docs/plans/2026-05-27-rag-experiments-create.md`、`docs/plans/2026-05-27-rag-experiments-detail.md`、`docs/plans/2026-05-27-rag-experiments-update.md`、`docs/plans/2026-05-27-rag-experiments-delete-and-smoke.md`
  - 本地环境与 smoke：`docs/plans/2026-05-27-ai-service-env-location.md`、`docs/plans/2026-05-27-local-env-template.md`、`docs/plans/2026-05-27-local-postgres-smoke-retry.md`
  - 失败与观察记录：`docs/testing/failures/2026-05-27-rag-experiments-delete-and-smoke-notes.md`、`docs/testing/failures/2026-05-27-local-postgres-smoke-retry-notes.md`
  - Git 初始化与阶段更新：`docs/plans/2026-05-27-git-init-and-stage-update.md`、`docs/reviews/2026-05-27-git-init-and-stage-update-review-prompt.md`、`docs/testing/failures/2026-05-27-git-init-and-stage-update-notes.md`
