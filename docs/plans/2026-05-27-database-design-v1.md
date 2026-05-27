# 第一版数据库设计文档计划

更新时间：2026-05-27

## 当前目标

补齐 `docs/architecture/database-design.md`，把当前 Flyway 迁移中的 PostgreSQL + pgvector 表结构、写入职责、索引和后续演进约束沉淀为中文设计文档。

## 背景

`PROJECT_CONTEXT.md` 的当前待办中仍有“编写第一版数据库设计文档”。当前项目已经有两份 Flyway 迁移：

- `V202605251930__init_agent_knowledge_schema.sql`
- `V202605270930__create_rag_experiments.sql`

但 `docs/architecture/` 目录尚未创建，缺少面向 review 和后续开发的数据库设计说明。

## 涉及范围

- 新增 `docs/architecture/database-design.md`。
- 更新 `PROJECT_CONTEXT.md` 当前待办和 2026-05-27 阶段级变更摘要。
- 更新 `docs/handoff/CURRENT_STATE.md`。

## 不涉及范围

- 不修改数据库迁移脚本。
- 不新增或修改接口。
- 不启动本地 PostgreSQL。
- 不写入真实数据库账号、密码或本地 `.env` 内容。

## 设计文档要覆盖

- 数据库总体定位：PostgreSQL 同时承载业务元数据与向量数据。
- 扩展依赖：`pgcrypto` 与 `vector`。
- 核心表分组：知识库与文档、向量与 chunk、对话与 RAG trace、反馈、实验平台。
- 服务写入职责：Spring Boot 与 FastAPI AI 服务的边界。
- 关键关系：知识库、文档、chunk、embedding、RAG run、retrieval result、feedback、experiment。
- 索引与查询路径：metadata GIN、向量 HNSW、trace/session/rank 索引。
- 当前占位和限制：embedding 维度固定为 1536、GraphRAG 表尚未创建、多格式解析字段先预留。
- 后续演进建议：GraphRAG、评估指标表、文档状态流转、审计与多用户权限。

## 验证方式

- 检查文档存在且为中文。
- 检查文档引用的表名与迁移脚本一致。
- 检查 `PROJECT_CONTEXT.md` 待办状态已同步。
- 检查本轮没有改动真实 `.env`。

## 风险

- 当前设计文档以已有迁移为准，部分规划表如 `graph_entities`、`graph_relationships` 尚未落地，只能标注为后续演进。
- 当前没有数据库反向 introspection，本轮不验证真实库结构，只核对迁移脚本。
