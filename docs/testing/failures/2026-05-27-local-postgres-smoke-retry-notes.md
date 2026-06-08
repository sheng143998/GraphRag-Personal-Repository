# 2026-05-27 本地 PostgreSQL smoke 复测

## 背景

用户已补全根目录 `.env` 中的数据库字段，本轮重新尝试本地 PostgreSQL 连接和 RAG 实验接口 HTTP smoke。

## 当前状态

本轮复测已完成。本地 PostgreSQL 连接成功，Spring Boot 后端启动成功，Flyway 迁移成功，RAG 实验接口 HTTP smoke 全链路通过。

## 安全约束

- 不记录真实数据库密码。
- 不把 `.env` 的真实值复制到文档。

## 问题记录

暂无阻塞性失败。

## 观察 1：Flyway 对 PostgreSQL 18.3 给出兼容性提醒

- 现象：后端启动时 Flyway 输出 `Flyway upgrade recommended`，提示 PostgreSQL 18.3 新于当前 Flyway 已测试版本。
- 触发场景：Spring Boot 启动并执行 Flyway 校验、迁移。
- 影响：本轮迁移仍成功执行，数据库 schema 从 `202605251930` 迁移到 `202605270930`。
- 后续建议：后续升级 Spring Boot / Flyway 时关注 PostgreSQL 18 支持矩阵；当前不阻塞本地开发。

## 已执行验证

- 已从 `.env` 加载非空环境变量，未展示真实密码。
- PostgreSQL 连接测试通过：目标库 `agent_knowledge` 可访问。
- 已确认数据库扩展包含 `vector`。
- 后端通过 `mvn spring-boot:start` 启动成功。
- `GET /api/health`：通过。
- `GET /api/rag/experiments`：通过，smoke 前列表数量为 1。
- `POST /api/rag/experiments`：通过，成功创建临时 smoke 实验记录。
- `GET /api/rag/experiments/{id}`：通过，返回刚创建的实验记录。
- `PUT /api/rag/experiments/{id}`：通过，状态更新为 `COMPLETED`。
- `DELETE /api/rag/experiments/{id}`：通过。
- 删除后再次 `GET /api/rag/experiments/{id}`：返回 404，符合预期。
- smoke 后列表数量为 1，说明临时测试记录已删除。
- 已通过 `mvn spring-boot:stop` 停止本轮启动的后端。
- 已确认 8080 端口没有本轮遗留监听。
