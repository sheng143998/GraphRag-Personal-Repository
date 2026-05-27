# 数据库设计文档 v1

更新时间：2026-05-27

## 1. 设计目标

本项目使用 PostgreSQL 同时承载业务元数据、RAG 派生数据和向量数据。当前第一版数据库设计服务于三个目标：

- 支撑知识库、文档、chunk、embedding 的基础入库与检索。
- 支撑基础 RAG 问答链路的 trace、召回结果、回答和反馈沉淀。
- 支撑 RAG 实验平台的第一版实验配置与指标记录。

当前 schema 以 Spring Boot 的 Flyway 迁移为准，迁移目录为：

- `backend-java/src/main/resources/db/migration/V202605251930__init_agent_knowledge_schema.sql`
- `backend-java/src/main/resources/db/migration/V202605270930__create_rag_experiments.sql`

## 2. 扩展依赖

当前迁移启用两个 PostgreSQL 扩展：

| 扩展 | 用途 |
| --- | --- |
| `pgcrypto` | 提供 `gen_random_uuid()`，用于 UUID 主键默认值。 |
| `vector` | 提供 pgvector 向量字段和向量相似度索引能力。 |

向量字段当前固定为 `vector(1536)`，对应第一版 embedding 占位实现和后续 1536 维模型接入。后续如果切换 3072 维或多模型并存，需要追加新迁移，不修改历史迁移。

## 3. 表分组

### 3.1 知识库与文档表

| 表名 | 职责 | 主要写入方 |
| --- | --- | --- |
| `knowledge_bases` | 记录知识库基础信息、状态和默认 RAG 策略。 | Spring Boot |
| `documents` | 记录文档元信息、文件类型、解析器、解析状态、摘要和 metadata。 | Spring Boot，后续解析状态优先经 Spring Boot 回写 |
| `document_chunks` | 记录文档切分后的文本块、父子 chunk、页码、sheet、行范围和 metadata。 | FastAPI AI 服务 |
| `chunk_embeddings` | 记录 chunk 对应 embedding 模型和向量。 | FastAPI AI 服务 |

核心关系：

```text
knowledge_bases
-> documents
-> document_chunks
-> chunk_embeddings
```

设计说明：

- `documents.knowledge_base_id` 使用级联删除，删除知识库会删除其文档。
- `document_chunks.document_id` 与 `document_chunks.knowledge_base_id` 都使用级联删除，保证文档删除后 chunk 不残留。
- `document_chunks.parent_chunk_id` 预留 Parent-Child Retrieval，父 chunk 删除后子 chunk 保留但父引用置空。
- `chunk_embeddings.chunk_id` 使用级联删除，chunk 删除后对应向量同步删除。
- `documents.metadata`、`document_chunks.metadata`、`chunk_embeddings.metadata` 都使用 JSONB，承载文档类型、标签、技术栈、解析细节和后续扩展字段。

### 3.2 对话与 RAG trace 表

| 表名 | 职责 | 主要写入方 |
| --- | --- | --- |
| `chat_sessions` | 记录一次对话会话，可关联知识库。 | Spring Boot |
| `chat_messages` | 记录用户和助手消息、引用来源和 trace id。 | Spring Boot |
| `rag_runs` | 记录每次 RAG 执行的输入、策略、prompt、模型、答案、耗时和状态。 | Spring Boot |
| `rag_retrieval_results` | 记录每次 RAG run 的召回 chunk、排序、分数、重排分数和是否进入上下文。 | Spring Boot |
| `rag_feedback` | 记录用户对某次回答的评分、类型和评论。 | Spring Boot |

核心关系：

```text
chat_sessions
-> chat_messages
-> rag_runs
-> rag_retrieval_results

rag_runs
-> rag_feedback
```

设计说明：

- `rag_runs.trace_id` 是跨前端、Spring Boot、FastAPI 和数据库的关键追踪字段。
- `rag_runs.question` 记录原始问题，`rewritten_query` 预留 Query Rewrite 结果。
- `rag_runs.strategy_name`、`retriever_type`、`prompt_name`、`prompt_version` 和 `model_name` 用于后续实验对比。
- `rag_retrieval_results.rank` 与 `selected_for_context` 用于还原召回列表和最终上下文选择。
- `rag_feedback.rating` 限制在 1 到 5，用于后续评估和人工反馈分析。

### 3.3 RAG 实验平台表

| 表名 | 职责 | 主要写入方 |
| --- | --- | --- |
| `rag_experiments` | 记录实验名称、策略、评估集、样本数、precision、recall、状态和备注。 | Spring Boot |

设计说明：

- 当前实验表是 Phase 7 的第一版雏形，用于记录不同 RAG 策略、数据集和指标结果。
- `knowledge_base_id` 可为空，允许先创建全局实验或尚未绑定知识库的实验。
- `precision_score` 和 `recall_score` 当前可为空，后续接入评估集后回填。
- 当前还没有单独的评估样本表、实验运行明细表和指标快照表，后续需要追加迁移扩展。

## 4. 服务写入职责

### 4.1 Spring Boot

Spring Boot 是业务数据入口，默认负责写入：

- `knowledge_bases`
- `documents`
- `chat_sessions`
- `chat_messages`
- `rag_runs`
- `rag_retrieval_results`
- `rag_feedback`
- `rag_experiments`

Spring Boot 负责对外 API、统一响应、业务校验、实验配置和 AI 服务调用结果落库。前端不直接访问 FastAPI，也不直接写数据库。

### 4.2 FastAPI AI 服务

FastAPI AI 服务负责 RAG 内部能力，默认负责写入：

- `document_chunks`
- `chunk_embeddings`

FastAPI 可以读取业务表，例如按 `knowledge_base_id` 检索文档和 chunk；如果需要更新文档解析状态，优先通过 Spring Boot API 回写，避免多个服务直接修改同一业务字段。

### 4.3 共享约束

- 所有数据库结构变更必须新增 Flyway 迁移。
- 已合入迁移不直接改历史，只能追加新迁移修正。
- 不允许只改 Entity、DTO、Pydantic Schema 或 Repository 而不写迁移。
- 真实数据库密码只放本地 `.env` 或部署环境变量，不写入文档、代码或测试。

## 5. 索引与查询路径

### 5.1 文档与 metadata 查询

| 索引 | 用途 |
| --- | --- |
| `idx_documents_knowledge_base_id` | 按知识库查询文档列表。 |
| `idx_documents_status` | 按解析状态筛选文档。 |
| `idx_documents_metadata_gin` | 支持文档 metadata 条件过滤。 |
| `idx_document_chunks_document_id` | 按文档查询 chunk。 |
| `idx_document_chunks_knowledge_base_id` | 按知识库召回 chunk。 |
| `idx_document_chunks_metadata_gin` | 支持 chunk metadata 过滤。 |

### 5.2 向量检索

| 索引 | 用途 |
| --- | --- |
| `idx_chunk_embeddings_chunk_id` | 从 embedding 回到 chunk。 |
| `idx_chunk_embeddings_embedding_hnsw` | 使用 HNSW 支持向量近邻检索。 |
| `idx_chunk_embeddings_metadata_gin` | 支持 embedding metadata 过滤。 |

当前向量索引使用 `vector_cosine_ops`，默认按余弦相似度组织检索。后续如果引入不同 embedding 模型，需要同时明确维度、距离度量和索引策略。

### 5.3 对话、trace 与实验查询

| 索引 | 用途 |
| --- | --- |
| `idx_chat_messages_session_id_created_at` | 按会话时间顺序加载消息。 |
| `idx_rag_runs_trace_id` | 根据 trace id 定位一次 RAG 执行。 |
| `idx_rag_runs_session_id` | 查询某个会话下的 RAG 执行记录。 |
| `idx_rag_retrieval_results_run_id_rank` | 按 run 和 rank 还原召回列表。 |
| `idx_rag_feedback_run_id` | 查询某次 RAG run 的用户反馈。 |
| `idx_rag_experiments_updated_at` | 实验列表按更新时间排序。 |
| `idx_rag_experiments_strategy_name` | 按策略筛选实验。 |
| `idx_rag_experiments_knowledge_base_id` | 按知识库筛选实验。 |

## 6. 状态字段约定

当前状态字段先使用字符串，便于早期快速迭代：

| 字段 | 当前示例 | 说明 |
| --- | --- | --- |
| `knowledge_bases.status` | `ACTIVE` | 知识库是否可用。 |
| `documents.status` | `UPLOADED` | 文档解析和入库状态。 |
| `chat_sessions.session_status` | `ACTIVE` | 会话状态。 |
| `rag_runs.status` | `PENDING` | RAG 执行状态。 |
| `rag_experiments.status` | `PLANNED` | 实验状态。 |

后续当状态流转稳定后，可以补充枚举约束或 check 约束，但需要通过追加迁移实现。

## 7. 当前限制

- `chunk_embeddings.embedding` 当前固定为 `vector(1536)`，暂不支持同表多维度向量混存。
- `graph_entities` 和 `graph_relationships` 仍处于规划阶段，当前迁移尚未创建。
- 文档上传、多格式解析、MinerU PDF 解析还未完整落地，`parser_name`、`parser_version`、`page_number`、`sheet_name`、`row_range` 等字段先作为预留能力。
- `rag_experiments` 当前只记录实验摘要指标，还没有评估样本、逐题结果、实验运行批次和指标历史。
- 当前没有用户、权限和审计表，`owner_id` 只是知识库层面的预留字段。

## 8. 后续演进建议

### 8.1 文档入库增强

- 增加文档解析任务表，记录解析开始、结束、失败原因和重试次数。
- 增加文件存储元信息，例如文件大小、hash、对象存储 key。
- 为常用 metadata 字段补充结构化列，例如 `document_type`、`file_type`、`created_at` 的组合索引。

### 8.2 RAG 评估增强

- 增加评估数据集表，记录标准问题、期望答案、知识库范围和标签。
- 增加实验运行表，区分一次实验配置和多次执行结果。
- 增加逐题评估结果表，记录命中 chunk、答案质量、人工评分和自动指标。

### 8.3 GraphRAG 增强

- 增加 `graph_entities`，记录实体名称、类型、别名、摘要和来源 chunk。
- 增加 `graph_relationships`，记录实体关系、关系类型、置信度和来源 chunk。
- 后续如果图查询复杂度上升，再评估是否接入专门图数据库；早期可以先在 PostgreSQL 中沉淀实体和关系。

### 8.4 运维与安全

- 增加用户表、权限表和知识库访问控制。
- 增加审计日志，记录重要配置变更和实验状态变更。
- 增加数据库迁移测试，确保空库可按顺序执行所有迁移。

## 9. Review 清单

- 表名、字段名和索引名是否与 Flyway 迁移一致。
- Spring Boot 与 FastAPI 的写入边界是否清晰。
- RAG trace 字段是否足够支撑后续调试、评估和复盘。
- 向量维度、索引类型和 metadata 过滤限制是否已明确。
- 未落地能力是否清楚标注为后续演进。
