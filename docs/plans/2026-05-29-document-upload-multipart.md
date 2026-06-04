# 2026-05-29 文档上传 Multipart 接口

## 背景

当前 `POST /api/documents/upload` 已支持单篇 JSON Demo 文档内容，但前端仍需要粘贴正文文本，不是真实文件选择器。Phase 2 的文档入库目标需要逐步靠近真实上传流程，因此本轮在不改变接口路径的前提下，为同一接口补充 `multipart/form-data` 支持。

## 当前目标

本轮只增强一个接口：`POST /api/documents/upload` 增加 multipart 文件上传能力。

状态：已完成，等待用户 review。

## 接口边界

- Spring Boot 对外路径仍为 `POST /api/documents/upload`。
- 保留上一轮 JSON 请求能力。
- 新增 multipart 请求能力，支持字段：`knowledgeBaseId`、`title`、`documentType`、`file`、可选 `sourceType`、`sourcePath`、`summary`、`metadata`。
- multipart 文件内容先按 UTF-8 文本读取，适合 Markdown / TXT / CSV / HTML Demo。
- Spring Boot 仍统一调用 FastAPI `/ai/ingest/document`，前端不直接调用 AI 服务。

## 涉及模块

- Spring Boot 文档 Controller / Service / DTO
- 前端上传组件、上传类型和 API client
- 模块 README 与项目过程文档

## 预计修改文件

- `backend-java/src/main/java/com/example/agentknowledge/controller/DocumentController.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentService.java`
- `frontend/src/components/UploadEntry.vue`
- `frontend/src/api/documents.ts`
- `frontend/src/types/index.ts`
- `backend-java/README.md`
- `frontend/README.md`
- `docs/reviews/2026-05-29-document-upload-multipart-review-prompt.md`
- `docs/testing/failures/2026-05-29-document-upload-multipart-notes.md`
- `docs/handoff/CURRENT_STATE.md`
- `PROJECT_CONTEXT.md`

## 非范围

- 不实现二进制 PDF / DOCX 的真实解析。
- 不做批量上传。
- 不做上传进度条。
- 不新增后台任务或解析状态轮询。

## 验证方式

- 运行 Java 后端构建，确认 multipart Controller 与 Service 可编译。
- 运行前端构建，确认 file input、FormData 和类型定义可编译。
- 运行 AI 服务语法验证，确认 Python 侧未受影响。

## 实际验证结果

- Java 后端：`mvn.cmd test` 通过，结果为 `BUILD SUCCESS`。
- 前端：`npm.cmd run build` 通过，类型检查和生产构建成功。
- AI 服务：`python -m compileall app tests` 通过。
- HTTP smoke：本轮未启动 PostgreSQL、Spring Boot 和 FastAPI，未执行真实 HTTP smoke。

## 当前风险

- 当前 multipart 文件读取按 UTF-8 文本处理，二进制文件只适合后续解析器接入前的占位验证。
- metadata multipart 字段仍以字符串透传，后续需要统一结构化校验。
