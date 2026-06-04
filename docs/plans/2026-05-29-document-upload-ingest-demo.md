# 2026-05-29 文档上传入库 Demo 接口

## 背景

当前 Phase 2 仍处于进行中，`POST /api/documents/upload` 只创建文档元数据，尚未串起 Spring Boot 到 FastAPI 的文档解析、切块和 embedding 入库链路。前端上传入口也仍是字段占位，不能提交真实入库内容。

## 当前目标

本轮只完成一个接口：`POST /api/documents/upload` 文档上传入库 Demo。

状态：已完成，等待用户 review。

## 接口边界

- Spring Boot 对外接口仍为 `POST /api/documents/upload`。
- 请求先支持 JSON Demo 载荷，包含单篇文档的知识库、标题、文档类型、文件名、文件类型、正文内容和可选元数据。
- Spring Boot 负责校验知识库、创建文档 ID、调用 FastAPI `/ai/ingest/document`，并返回入库结果。
- FastAPI 继续复用现有 `IngestService`，负责解析、切块、embedding 和数据库写入。

## 涉及模块

- Spring Boot 后端文档 Controller / Service / DTO
- Spring Boot AI 服务客户端
- AI 服务 ingest schema 兼容性
- 前端上传入口的最小字段对齐
- 项目过程文档

## 预计修改文件

- `backend-java/src/main/java/com/example/agentknowledge/controller/DocumentController.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/document/CreateDocumentRequest.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/document/DocumentResponse.java`
- `backend-java/src/main/java/com/example/agentknowledge/client/AiServiceGateway.java`
- `backend-java/src/main/java/com/example/agentknowledge/client/AiServiceClient.java`
- `backend-java/src/main/java/com/example/agentknowledge/client/dto/*`
- `frontend/src/components/UploadEntry.vue`
- `frontend/src/types/index.ts`
- `frontend/src/api/documents.ts`
- `docs/reviews/2026-05-29-document-upload-ingest-demo-review-prompt.md`
- `docs/testing/failures/2026-05-29-document-upload-ingest-demo-notes.md`
- `docs/handoff/CURRENT_STATE.md`
- `PROJECT_CONTEXT.md`

## 非范围

- 不做真实 multipart 文件上传。
- 不接入 MinerU 真实 PDF 解析，只保留现有 PDF adapter 占位。
- 不实现批量上传接口。
- 不新增文档删除、重试或状态轮询接口。

## 验证方式

- 运行 AI 服务 pytest，确认 ingest + query 链路未回退。
- 运行 Java 后端测试或编译，确认 DTO、客户端和 Controller 链路可构建。
- 如本地服务和数据库可用，再做 `POST /api/documents/upload` HTTP smoke。

## 实际验证结果

- Java 后端：`mvn.cmd test` 通过，构建结果为 `BUILD SUCCESS`。
- 前端：`npm.cmd run build` 通过，类型检查和生产构建成功。
- AI 服务：`python -m compileall app tests` 通过。
- AI 服务 pytest：当前 Python 环境未安装 pytest，未执行成功，已记录到失败复盘 / 观察记录。
- HTTP smoke：本轮未启动 PostgreSQL、Spring Boot 和 FastAPI，未执行真实 HTTP smoke。

## 当前风险

- 本地 PostgreSQL 未运行时只能做编译和单元级验证。
- 当前 embedding 仍是 stub，入库 Demo 可以形成闭环，但不是生产级向量质量。
- 前端本轮只做 Demo 文本提交，后续仍需替换为真实文件选择器与 FormData。
