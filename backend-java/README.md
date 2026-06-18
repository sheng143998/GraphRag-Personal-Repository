# Java 业务后端模块

`backend-java/` 是项目的业务后端，对外统一暴露 Spring Boot `/api/*`。React 前端只访问本模块，Python AI 服务只通过本模块被桥接调用。

Java 后端不实现 RAG 检索、生成、Agent 推理或 evaluator 算法，只负责业务编排、权限边界、持久化、数据库迁移和跨服务契约。

## 当前状态

- 已完成统一响应、异常处理、请求日志、`X-Trace-Id` 贯通和 health check。
- 已完成知识库、文档、聊天会话、assistant-turn、RAG run、实验、评测集、反馈、图谱事实相关接口。
- 已完成 Spring Boot -> FastAPI 的 ingest / RAG / Agent / evaluator 桥接。
- 支持文档上传和异步入库：单文件、多文件、文件夹上传，默认本地线程池，可切换 RabbitMQ。
- 支持售后技术支持 Agent：透传 `supportPlan`、`workflowSteps`、trace attributes 和引用证据给 React 前端。
- 支持评测集管理：页面内审核、状态流转、样本删除、批量删除最近导入或当前筛选样本、删除实验。
- 支持 RAGAS 离线报告回填：将 RAGAS 报告写回实验评估记录，保留指标名、版本、裁判模型和报告 URI。

## 技术栈

- Java 21
- Spring Boot
- Spring Data JPA
- Flyway
- PostgreSQL
- pgvector

## 目录结构

```text
backend-java/
├── src/main/java/com/example/agentknowledge/
│   ├── client/          # 调用 Python AI 服务
│   ├── common/          # 通用响应、trace 和异常
│   ├── config/          # 配置
│   ├── controller/      # /api/* Controller
│   ├── domain/          # JPA Entity
│   ├── dto/             # 请求 / 响应 DTO
│   ├── repository/      # Repository
│   └── service/         # 业务编排和持久化
├── src/main/resources/
│   ├── application.yml
│   └── db/migration/    # Flyway migration
└── pom.xml
```

## 本地启动

启动前请确保 PostgreSQL 可连接，根目录 `.env` 或系统环境变量中有统一数据库配置。

```powershell
cd backend-java
mvn spring-boot:run
```

## 常用命令

```powershell
mvn.cmd -f backend-java\pom.xml test
mvn.cmd -f backend-java\pom.xml package -DskipTests
mvn.cmd -f backend-java\pom.xml spring-boot:run
```

## 环境变量

- `DB_URL`：PostgreSQL JDBC 地址，例如 `jdbc:postgresql://localhost:5432/agent_knowledge`。
- `DB_USERNAME`：数据库用户名。
- `DB_PASSWORD`：数据库密码。
- `DOCUMENT_UPLOAD_MAX_FILE_SIZE`：单文件上传大小上限，默认 `50MB`。
- `DOCUMENT_UPLOAD_MAX_REQUEST_SIZE`：单次 multipart 请求大小上限，默认 `50MB`。
- `DOCUMENT_INGEST_MODE`：文档入库模式，默认 `local`，可切换 `rabbitmq`。
- `AI_SERVICE_BASE_URL`：Python AI 服务地址，默认本地 FastAPI。
- `AI_SERVICE_MOCK_ENABLED`：是否启用 AI mock。
- `AI_SERVICE_READ_TIMEOUT`：调用 AI 服务读取超时。

真实密码和 token 只放在本地环境，不写入代码、测试或文档。

## 主要接口

- `GET /api/health`
- `GET|POST|PUT|DELETE /api/knowledge-bases`
- `POST /api/documents/upload`
- `POST /api/documents/upload/batch`
- `GET /api/documents`
- `GET|DELETE /api/documents/{id}`
- `GET|POST /api/chat/sessions`
- `GET /api/chat/{sessionId}/messages`
- `POST /api/chat/{sessionId}/assistant-turn`
- `POST /api/agent/invoke`
- `POST /api/rag/query`
- `GET /api/rag/runs`
- `GET /api/rag/runs/{id}`
- `GET|POST|PUT|DELETE /api/rag/experiments`
- `GET|POST|PUT|DELETE /api/rag/evaluation-cases`
- `POST /api/rag/evaluation-cases/{id}/evaluate`
- `POST /api/rag/evaluation-cases/run-batch`
- `PUT /api/rag/experiment-evaluations/ragas-report`
- `GET /api/rag/experiments/evaluations/summary`
- `POST /api/feedback`
- `GET /api/graph/facts`

## 关键入口

- `controller/RagController.java`：RAG、实验、评测集、RAGAS 回填和对比相关 API。
- `service/RagExperimentService.java`：实验、评测集、批量评测和评测历史持久化。
- `service/RagService.java`：RAG query 桥接和 run 持久化。
- `service/AssistantTurnService.java`：聊天 assistant-turn 编排。
- `service/DocumentIngestProcessor.java`：文档异步入库。
- `client/AiServiceClient.java`：调用 FastAPI。
- `domain/RagExperimentEvaluation.java`：评测历史结构化指标实体。
- `src/main/resources/db/migration/`：数据库迁移脚本。

## 验证

```powershell
mvn.cmd -f backend-java\pom.xml test
```

## 后续优化

- 将同步批量评测升级为异步任务：批次记录、单 case 状态、失败重试和任务进度。
- 增加 Controller 契约测试，覆盖 RAGAS 回填、样本批量删除和 assistant-turn trace 透传。
- 为 token / cost 估算增加模型单价配置，但必须标记为估算值。
- 为文档入库失败原因提供更结构化的错误码，便于 React 前端展示复查建议。
