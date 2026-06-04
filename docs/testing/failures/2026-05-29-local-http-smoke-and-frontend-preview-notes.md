# 2026-05-29 本地 HTTP Smoke 与前端预览过程记录

## 背景

用户要求先做一次 HTTP smoke 并查看前端，随后明确要求使用本地数据库，不启动 Docker。

## 已确认环境

- 本机 PostgreSQL 服务 `postgresql-x64-18` 正在运行。
- `127.0.0.1:5432` 端口可连接。
- `.env` 中存在本地数据库相关变量，但本文档不记录真实值。

## 遇到的问题

### 1. 系统 Python 缺少 uvicorn

现象：首次启动 AI 服务时，系统 Python 报错 `No module named uvicorn`。

根因：命令使用了系统 Python，而不是项目内虚拟环境。

处理：改用 `ai-service/.venv/bin/python.exe` 启动 FastAPI，AI 服务启动成功。

后续避免：本地启动 AI 服务时优先使用项目内虚拟环境。

### 2. Spring Boot 默认临时目录不可写

现象：后端 jar 启动时 Tomcat 创建临时目录失败，错误位置在用户临时目录。

根因：当前运行环境对用户临时目录写入受限。

处理：创建 `backend-java/.tmp`，并通过 `-Djava.io.tmpdir`、`TEMP`、`TMP` 将 Java 临时目录指向项目内可写路径。

后续避免：本地 smoke 或脚本启动后端时显式设置项目内临时目录。

### 3. 默认数据库密码与本机 `.env` 不一致

现象：后端连接 PostgreSQL 时，默认账号密码认证失败。

根因：本机 PostgreSQL 的真实密码与 `application.yml` 默认占位值不同。

处理：启动后端和 AI 服务时从根目录 `.env` 读取本地数据库配置，不在日志或文档中输出真实密码。

后续避免：本地联调统一从 `.env` 注入数据库配置。

### 4. 文档详情 chunk 摘要为空

现象：`POST /api/documents/upload` JSON 返回 `status=INDEXED`，上传响应 `chunkCount=1`；但随后 `GET /api/documents/{id}` 返回 `chunkCount=0` 且 `chunks=[]`。

可能原因：需要继续核对 Java 文档 ID、AI `/ai/ingest/document` 写入的 `document_id`、`document_chunks` 查询条件是否完全一致。

处理：本轮先记录为 smoke 发现的问题，不在本轮新增接口或修改业务逻辑。

后续避免：下一轮优先补一个针对文档入库后详情 chunk 可见性的集成测试。

## 已执行验证

- 前端首页 HTTP：通过。
- AI health：通过。
- Java health：通过。
- 知识库创建：通过。
- JSON 文档上传：通过，返回 `INDEXED`。
- 文档列表：通过。
- 文档详情：接口可访问，但 chunk 摘要为空，需要后续排查。
- Codex 浏览器前端预览：已打开。
