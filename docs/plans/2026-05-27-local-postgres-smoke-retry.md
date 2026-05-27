# 2026-05-27 本地 PostgreSQL smoke 复测

## 背景

上一轮 RAG 实验接口 HTTP smoke 被数据库连接阻塞。用户已补全根目录 `.env` 中的数据库字段，本轮使用本地 PostgreSQL 连接信息重新验证实验接口链路。

## 当前目标

- 加载根目录 `.env` 到当前 PowerShell 进程。
- 验证 PostgreSQL 可连接。
- 确认或创建 `agent_knowledge` 数据库。
- 启动 Spring Boot 后端。
- 通过 HTTP smoke 验证 RAG 实验接口：列表、创建、详情、更新、删除、删除后 404。

## 涉及模块

- 本地 `.env`
- PostgreSQL
- Spring Boot 后端
- RAG 实验接口

## 预计修改文件

- `docs/reviews/2026-05-27-local-postgres-smoke-retry-review-prompt.md`
- `docs/testing/failures/2026-05-27-local-postgres-smoke-retry-notes.md`
- `docs/handoff/CURRENT_STATE.md`

## 非范围

- 不把真实数据库密码写入文档或代码。
- 不修改 `.env` 内容。
- 不启动 Docker。

## 验证方式

- `psql` 连接测试。
- `mvn test`。
- 后端健康检查。
- RAG 实验接口 HTTP smoke。

## 当前风险

- `.env` 值可能不完整或数据库不存在。
- 本地 PostgreSQL 账号可能没有建库或创建扩展权限。
- 后端启动时 Flyway 可能因 pgvector 或权限失败。
