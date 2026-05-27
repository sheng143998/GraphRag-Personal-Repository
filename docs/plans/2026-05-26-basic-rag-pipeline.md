# 2026-05-26 基础 RAG 主链路

## 背景

当前 RAG 骨架已经具备 Spring Boot 对外接口、FastAPI 内部接口和数据库 schema，但 AI 服务只使用内存仓库，Java 后端默认返回 mock AI 结果。项目需要先完成可验证的基础 RAG 闭环。

## 范围

- FastAPI AI 服务从 PostgreSQL 读取 `document_chunks` 与 `chunk_embeddings`。
- 文档 ingest 写入 `documents`、`document_chunks` 和 `chunk_embeddings`。
- 基础 RAG 使用 stub embedding + pgvector 相似度 + 关键词匹配组合排序。
- Java 后端调用真实 FastAPI `/ai/rag/query` schema，并保存 `rag_runs` 与 `rag_retrieval_results`。
- 保留 mock AI 开关，便于 AI 服务未启动时本地调试。

## 非范围

- 暂不接真实 LLM、真实 embedding 或外部 rerank 服务。
- 暂不实现 Query Rewrite、Multi-query、Parent-Child、GraphRAG。
- 暂不做浏览器 E2E。

## 验证计划

- Python 编译与单元测试。
- Java `mvn test`。
- 本地 PostgreSQL 上运行后端启动、Flyway 校验、健康接口。
- 条件允许时联调 FastAPI ingest + Spring Boot RAG query。
