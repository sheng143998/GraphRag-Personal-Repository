# 2026-05-29 文档上传 Multipart 接口 review 提示

## 本次 review 目标

请 review `POST /api/documents/upload` 的 multipart 支持是否和现有 JSON 上传能力兼容，并确认前端是否已经通过 Spring Boot 上传真实文件。

## 本次接口范围

- `POST /api/documents/upload`
  - JSON：保留上一轮单篇 Demo 文本上传。
  - multipart：新增单文件上传，Spring Boot 读取文本内容后调用 FastAPI `/ai/ingest/document`。

## 重点 review 顺序

1. Controller 入口
   - `backend-java/src/main/java/com/example/agentknowledge/controller/DocumentController.java`
   - 检查 JSON 和 multipart 两个 consumes 是否清楚，不互相冲突。

2. Service 复用
   - `backend-java/src/main/java/com/example/agentknowledge/service/DocumentService.java`
   - 检查 multipart 是否复用同一条 AI 入库链路，避免出现两套文档入库逻辑。

3. 前端上传
   - `frontend/src/components/UploadEntry.vue`
   - `frontend/src/api/documents.ts`
   - 检查是否通过 FormData 调用 Java 后端，而不是绕过到 FastAPI。

## 当前占位实现

- multipart 文件内容按 UTF-8 文本读取。
- PDF / DOCX / XLSX 等二进制真实解析仍未完成。
- 暂不支持批量上传和进度条。

## 已执行验证结果

- Java 构建：`mvn.cmd test` 通过，结果为 `BUILD SUCCESS`。编译结束阶段仍出现历史 Maven 本地 jar 访问拒绝日志，但未阻塞构建。
- 前端构建：`npm.cmd run build` 通过，类型检查和生产构建成功。
- AI 服务语法验证：`python -m compileall app tests` 通过。
- HTTP smoke：未执行，本轮没有启动 PostgreSQL、Spring Boot 和 FastAPI。

## Review 时特别注意

- 不要删除 JSON 上传能力。
- 前端不要手动设置 multipart 的 `Content-Type`，应让浏览器自动带 boundary。
- 当前二进制文件解析能力必须明确标为占位，避免误以为已经支持真实 PDF / Word。
