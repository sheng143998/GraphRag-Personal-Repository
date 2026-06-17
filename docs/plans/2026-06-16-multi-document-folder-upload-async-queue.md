# 多文档与文件夹上传异步队列方案

## 目标

- 文档上传入口支持多篇文档上传。
- 前端支持选择本地文件夹，并把浏览器提供的相对路径传给后端。
- 保留现有单篇上传接口兼容性。
- 第一阶段继续支持 Spring Boot 本地线程池异步解析。
- 第三阶段新增 RabbitMQ 队列模式，为后续多 worker、重试和削峰预留入口。

## 架构边界

- 前端只调用 Spring Boot `/api/*`。
- Spring Boot 负责上传接收、文档元数据保存、任务提交和状态更新。
- FastAPI 继续只负责单文档解析、切分、embedding 和 RAG 派生数据写入。
- 当前不把 RAG 解析逻辑放进 Java，也不让前端直接调用 FastAPI。

## 实现方案

### 第一阶段：本地线程池异步

默认模式为 `local`：

```text
前端批量上传
-> Spring Boot /api/documents/upload/batch
-> 每个文件创建 document，状态 PROCESSING
-> DocumentIngestDispatcher 提交给 DocumentIngestProcessor
-> @Async 线程池调用 FastAPI /ai/ingest/document
-> 成功 INDEXED，失败 FAILED
```

优点是本地开发简单，不依赖 RabbitMQ。

### 第三阶段：RabbitMQ 队列异步

可通过配置切换为 `rabbitmq`：

```text
前端批量上传
-> Spring Boot 创建 document，状态 PROCESSING
-> 发布 DocumentIngestMessage 到 RabbitMQ
-> Spring Boot RabbitMQ listener 消费消息
-> 调用 FastAPI 单文档 ingest
-> 更新 document 状态
```

本轮实现 Java 侧 RabbitMQ 发布/消费，不引入 Celery worker。原因是当前 FastAPI 已经暴露单文档 ingest HTTP 接口，最小闭环是在 Spring Boot 中消费队列后调用现有 FastAPI。后续如果需要 Python worker，可把消息体保持不变，改为 Python Celery/RQ 消费 `documentId + filePayload`。

## 主要改动文件

- `backend-java/pom.xml`
- `backend-java/src/main/resources/application.yml`
- `backend-java/src/main/java/com/example/agentknowledge/config/DocumentIngestQueueProperties.java`
- `backend-java/src/main/java/com/example/agentknowledge/config/RabbitMqConfig.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentIngestDispatcher.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentIngestMessage.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentIngestRabbitListener.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/controller/DocumentController.java`
- `frontend/src/api/documents.ts`
- `frontend/src/components/UploadEntry.vue`
- `frontend/src/stores/workbench.ts`
- `frontend/src/types/index.ts`

## 验证方式

- `mvn.cmd -f backend-java/pom.xml -q -DskipTests compile`
- `npm.cmd --prefix frontend run typecheck`

RabbitMQ 模式需要本地提供 RabbitMQ 后再用：

```text
DOCUMENT_INGEST_MODE=rabbitmq
SPRING_RABBITMQ_HOST=localhost
SPRING_RABBITMQ_PORT=5672
```

