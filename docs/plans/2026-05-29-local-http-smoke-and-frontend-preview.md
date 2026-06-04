# 2026-05-29 本地 HTTP Smoke 与前端预览

## 背景

用户要求先做一次 HTTP smoke，并打开前端查看当前界面。用户随后明确要求使用本地 PostgreSQL，不启动 Docker。

## 当前目标

本轮不新增业务接口，只做本地数据库模式的项目重启、HTTP smoke 和前端预览。

## Smoke 范围

- 不启动 Docker。
- 使用本机 PostgreSQL 服务。
- 启动 FastAPI AI 服务。
- 启动 Spring Boot 后端。
- 启动 Vue 前端。
- 检查基础健康接口。
- 执行知识库创建、文档上传、文档列表、文档详情最小链路。
- 在 Codex 浏览器中打开前端页面给用户查看。

## 执行结果

- 本机 PostgreSQL 服务 `postgresql-x64-18` 正在运行，`127.0.0.1:5432` 可连接。
- 前端已启动：`http://127.0.0.1:5173/`，浏览器实际进入 `http://127.0.0.1:5173/chat`。
- AI 服务已启动：`http://127.0.0.1:8001/ai/health` 返回 `status=ok`。
- Java 后端已启动：`http://127.0.0.1:8080/api/health` 返回 `status=UP`。
- 后端启动时使用项目内 `backend-java/.tmp` 作为 Java 临时目录，绕过当前环境用户临时目录写入限制。
- Java 后端和 AI 服务均从根目录 `.env` 读取本地数据库配置；文档中不记录真实密码。

## HTTP Smoke 结果

- `GET /ai/health`：通过。
- `GET /api/health`：通过。
- `GET /` 前端首页：通过。
- `POST /api/knowledge-bases`：通过，创建 smoke 知识库。
- `POST /api/documents/upload` JSON：通过，返回 `status=INDEXED`，上传响应 `chunkCount=1`。
- `GET /api/documents?knowledgeBaseId=...`：通过，能查询到本轮上传文档。
- `GET /api/documents/{id}`：接口可访问，但详情响应 `chunkCount=0` 且 `chunks=[]`，与上传响应 `chunkCount=1` 不一致，已记录为后续需要排查的问题。

## 非范围

- 不新增业务接口。
- 不提交真实 `.env` 内容。
- 不做生产级性能或安全测试。
- 不做真实 PDF / Word / Excel 二进制解析验证。

## 当前风险

- 文档上传链路可以返回 `INDEXED`，但详情 chunk 摘要暂未读出，需要继续排查 Java 文档 ID、AI 写入 chunk、详情查询条件之间是否一致。
- 当前 embedding、LLM generator 仍为 stub。
- FastAPI pytest 依赖仍未补齐，本轮只做 HTTP smoke。
