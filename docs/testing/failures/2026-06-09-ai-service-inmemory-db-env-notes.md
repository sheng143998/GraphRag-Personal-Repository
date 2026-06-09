# 2026-06-09 AI 服务回退内存仓库记录

## 现象

上传文档后，`documents` 表有记录，但 `document_chunks` 和 `chunk_embeddings` 表没有数据。

## 原因

Spring Boot 会先写 `documents`，而 chunks / embeddings 由 FastAPI AI 服务写入。此前 `.env` 中 `AI_RAG_USE_DATABASE` 留空时，AI 服务可能回退到 `InMemoryDocumentRepository`，导致 chunks / embeddings 写入内存而不是 PostgreSQL。

## 修复

- `.env` 明确使用 `AI_RAG_USE_DATABASE=true`
- AI 服务数据库 URL 改为从 `DB_URL` / `DB_USERNAME` / `DB_PASSWORD` 推导
- `.env.example`、Spring Boot 默认配置和文档统一为用户本地 PostgreSQL 配置

## 验证

AI 服务配置检查结果：

```text
postgresql://postgres:123456@localhost:5432/agent_knowledge
True
PostgresDocumentRepository
```
