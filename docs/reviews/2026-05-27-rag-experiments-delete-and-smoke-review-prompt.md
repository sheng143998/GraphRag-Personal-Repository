# 2026-05-27 RAG 实验删除接口与 smoke review 提示

## 本次 review 目标

请 review `DELETE /api/rag/experiments/{id}` 是否按统一资源路径删除实验记录，并确认真实数据库 + HTTP smoke 是否覆盖了实验接口的主要链路。

## 本次接口范围

- `DELETE /api/rag/experiments/{id}`
  - 入口：`backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
  - 作用：删除单个 RAG 实验记录，返回统一 `ApiResponse<Void>`。

## 本次 smoke 范围

- `GET /api/health`
- `GET /api/rag/experiments`
- `POST /api/rag/experiments`
- `GET /api/rag/experiments/{id}`
- `PUT /api/rag/experiments/{id}`
- `DELETE /api/rag/experiments/{id}`
- 删除后再次 `GET /api/rag/experiments/{id}` 验证 404

## 重点 review 顺序

1. 删除逻辑
   - `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
   - 检查删除前是否查询真实记录，未找到是否走统一 404。

2. Controller 路径
   - `backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
   - 检查删除接口是否与列表、创建、详情、更新接口保持同一资源路径。

3. smoke 结果
   - `docs/testing/failures/2026-05-27-rag-experiments-delete-and-smoke-notes.md`
   - 检查数据库启动、后端启动、HTTP 调用和服务清理是否记录完整。

## 当前占位实现

- 删除实验只删除 `rag_experiments` 记录，不涉及评估任务、RAG run 或图表缓存。
- 本轮没有前端 UI 联调。

## 已执行验证

- 在 `backend-java/` 下运行 `mvn test`，结果为 `BUILD SUCCESS`。
- 已尝试启动 Docker PostgreSQL，但 Docker daemon 未运行，无法启动容器。
- 已尝试连接本机 PostgreSQL 18，但项目默认凭据认证失败。
- 已尝试在工作区初始化临时 PostgreSQL 数据目录，但 `initdb` 被 Windows 沙箱 restricted token 限制阻断。
- 因当前环境没有可用 PostgreSQL，本轮未完成真实 HTTP smoke。
