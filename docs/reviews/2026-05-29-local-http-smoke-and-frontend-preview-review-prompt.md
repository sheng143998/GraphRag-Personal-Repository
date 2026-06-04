# 2026-05-29 本地 HTTP Smoke 与前端预览 review 提示

## 本次 review 目标

请 review 本地数据库模式下三端服务是否已经可启动，HTTP smoke 是否覆盖当前关键链路，以及前端页面是否能正常打开。

## 本次范围

- 使用本地 PostgreSQL，不启动 Docker。
- 启动 FastAPI AI 服务、Spring Boot 后端和 Vue 前端。
- 检查健康接口。
- 检查知识库创建、文档上传、文档列表和文档详情最小链路。
- 打开前端页面。

## 验证结果

- 前端：`http://127.0.0.1:5173/chat` 已在 Codex 浏览器打开。
- AI 服务：`GET http://127.0.0.1:8001/ai/health` 通过。
- Java 后端：`GET http://127.0.0.1:8080/api/health` 通过。
- 知识库创建：`POST /api/knowledge-bases` 通过。
- 文档上传：`POST /api/documents/upload` JSON 通过，返回 `INDEXED`。
- 文档列表：`GET /api/documents?knowledgeBaseId=...` 通过。
- 文档详情：`GET /api/documents/{id}` 可访问，但 chunk 摘要为空。

## 重点 review 顺序

1. 先看前端页面是否符合当前工作台预期，尤其是文档上传入口是否清晰。
2. 再看本地服务启动方式是否可以接受：本轮未用 Docker，后端通过 jar 启动，并把临时目录指到 `backend-java/.tmp`。
3. 最后看 HTTP smoke 异常：上传响应 `chunkCount=1`，详情响应 `chunkCount=0`，后续应优先排查这一点。

## Review 时特别注意

- 不要把真实 `.env` 内容写入文档或提交。
- 本轮只完成重启和 smoke，没有新增接口。
- 前端当前仍有 mock/demo 数据展示，页面能打开不代表所有业务数据已经完全实时化。
