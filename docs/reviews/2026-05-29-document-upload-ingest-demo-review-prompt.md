# 2026-05-29 文档上传入库 Demo 接口 review 提示

## 本次 review 目标

请 review `POST /api/documents/upload` 是否已经从元数据创建推进为可触发 AI 服务入库的 Demo 接口，并确认 Spring Boot 与 FastAPI 的请求字段、状态语义和 trace 传递是否一致。

## 本次接口范围

- `POST /api/documents/upload`
  - 入口：`backend-java/src/main/java/com/example/agentknowledge/controller/DocumentController.java`
  - 作用：接收单篇文档 Demo 内容，调用 FastAPI `/ai/ingest/document` 完成解析、切块和 embedding 入库，返回文档记录与 chunk 数量。

## 重点 review 顺序

1. 请求与响应 DTO
   - `backend-java/src/main/java/com/example/agentknowledge/dto/document/CreateDocumentRequest.java`
   - `backend-java/src/main/java/com/example/agentknowledge/dto/document/DocumentResponse.java`
   - 检查必填字段、枚举值约定、正文内容长度和 metadata 默认值是否合理。

2. Spring Boot 调用链路
   - `backend-java/src/main/java/com/example/agentknowledge/service/DocumentService.java`
   - `backend-java/src/main/java/com/example/agentknowledge/client/AiServiceClient.java`
   - 检查是否由 Service 负责编排，Controller 是否保持薄层，trace header 是否继续透传。

3. FastAPI 兼容性
   - `ai-service/app/schemas/ingest.py`
   - `ai-service/app/services/ingest_service.py`
   - 检查 Spring Boot 发送的 document type、file type、content、metadata 是否符合现有 AI 入库链路。

4. 前端 Demo 表单
   - `frontend/src/components/UploadEntry.vue`
   - `frontend/src/types/index.ts`
   - 检查前端是否只提交单篇 Demo 内容，避免和后续真实批量上传混淆。

## 当前占位实现

- 仍不处理 multipart 文件流。
- PDF、Word、Excel 解析目前主要复用纯文本占位解析器；MinerU PDF adapter 仍是预留实现。
- embedding adapter 仍是 stub，后续需要替换为真实 embedding 模型。

## 已执行验证结果

- Java 构建：`mvn.cmd test` 通过，结果为 `BUILD SUCCESS`。编译结束阶段仍出现历史 Maven 本地 jar 访问拒绝日志，但未阻塞构建。
- 前端构建：`npm.cmd run build` 通过，类型检查和生产构建成功。
- AI 服务语法验证：`python -m compileall app tests` 通过。
- AI 服务 pytest：`python -m pytest` 失败，原因是当前 Python 环境未安装 pytest。
- HTTP smoke：未执行，本轮没有启动 PostgreSQL、Spring Boot 和 FastAPI。

## Review 时特别注意

- 不要让前端绕过 Spring Boot 直接调用 FastAPI。
- 不要让 Controller 直接写数据库或拼装 AI 入库细节。
- 文档状态应能表达入库结果，避免成功响应里仍显示纯 `UPLOADED`。
