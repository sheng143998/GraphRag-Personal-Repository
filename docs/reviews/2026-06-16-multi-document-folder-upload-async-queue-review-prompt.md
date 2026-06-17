# 多文档与文件夹上传异步队列 Review Prompt

## 本次 Review 目标

请重点 review 文档上传链路是否符合项目三服务边界，并确认批量/文件夹上传不会破坏原有单篇上传兼容性。

## 重点 Review 文件

- `backend-java/src/main/java/com/example/agentknowledge/controller/DocumentController.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentIngestDispatcher.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentIngestProcessor.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentIngestRabbitListener.java`
- `backend-java/src/main/java/com/example/agentknowledge/config/RabbitMqConfig.java`
- `frontend/src/components/UploadEntry.vue`
- `frontend/src/api/documents.ts`
- `frontend/src/stores/workbench.ts`

## 需要确认的问题

- `POST /api/documents/upload` 单篇 JSON / multipart 是否保持兼容。
- `POST /api/documents/upload/batch` 是否正确保存每个文件的 `sourcePath`，尤其是文件夹上传的相对路径。
- `DOCUMENT_INGEST_MODE=local` 是否仍然使用 Spring `@Async` 线程池。
- `DOCUMENT_INGEST_MODE=rabbitmq` 下发布/消费消息是否符合后续扩展到 Python worker 的消息结构。
- 前端选择文件夹时，`webkitRelativePath` 是否能按预期传到后端。

## 已验证

- `mvn.cmd -f backend-java/pom.xml test`
- `npm.cmd --prefix frontend run typecheck`

## 已知边界

- 本轮没有引入 Celery worker。当前第三阶段落点是 RabbitMQ 队列模式，消费者仍在 Spring Boot 内部，复用现有 FastAPI 单文档 ingest 接口。
- 还没有实现死信队列、延迟重试和数据库任务表；后续可在 RabbitMQ 模式上继续增强。
