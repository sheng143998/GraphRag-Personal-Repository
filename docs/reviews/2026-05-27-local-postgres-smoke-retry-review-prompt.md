# 2026-05-27 本地 PostgreSQL smoke 复测 review 提示

## 本次 review 目标

请 review 本轮是否在不泄露真实 `.env` 值的前提下，完成本地 PostgreSQL 连接验证和 RAG 实验接口 HTTP smoke。

## 本次验证范围

- PostgreSQL 连接。
- `agent_knowledge` 数据库准备。
- Spring Boot 启动与 Flyway 迁移。
- RAG 实验接口：
  - `GET /api/rag/experiments`
  - `POST /api/rag/experiments`
  - `GET /api/rag/experiments/{id}`
  - `PUT /api/rag/experiments/{id}`
  - `DELETE /api/rag/experiments/{id}`
  - 删除后再次详情查询 404。

## 重点 review 顺序

1. 过程记录
   - `docs/testing/failures/2026-05-27-local-postgres-smoke-retry-notes.md`
   - 检查是否记录了成功项、失败项和阻塞原因。

2. handoff
   - `docs/handoff/CURRENT_STATE.md`
   - 检查下一步建议是否清楚。

## 安全要求

- 不在文档、日志摘要或最终回复中写出真实密码。
- 不提交 `.env` 中的真实值。

## 已执行验证

- 已从 `.env` 加载非空环境变量，未展示真实密码。
- PostgreSQL 连接测试通过，目标库 `agent_knowledge` 可访问。
- 已确认 `vector` 扩展存在。
- Spring Boot 通过 `mvn spring-boot:start` 启动成功，并执行 Flyway 迁移。
- RAG 实验接口 HTTP smoke 全链路通过：列表、创建、详情、更新、删除、删除后 404。
- 已通过 `mvn spring-boot:stop` 停止后端。
- 已确认 8080 端口没有本轮遗留监听。
