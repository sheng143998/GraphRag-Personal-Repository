# Java 业务后端模块

## 模块职责

`backend-java/` 是项目的业务后端，对外统一暴露 Spring Boot `/api/*`。它负责知识库、文档、会话、消息、RAG run、实验、评测集、评测历史、反馈和图谱事实读取，并桥接 Python AI 服务。

Java 后端不实现 RAG 检索、生成或 evaluator 算法，只负责业务编排、持久化和跨服务契约。

## 当前状态

- 已完成 Spring Boot 基础工程、统一响应、异常处理、请求日志、`X-Trace-Id` 贯通和 health check。
- 已完成知识库、文档、聊天会话、assistant-turn、RAG run、实验、评测集、反馈、图谱事实相关接口。
- 已完成 Spring Boot -> FastAPI 的 ingest / RAG / Agent / evaluator 桥接。
- 已支持评测集管理和批量评测：同一批样本可按不同 RAG preset 自动生成 run 并评估。
- 已支持评测历史结构化持久化：检索指标、GraphRAG 指标、token、成本和分阶段耗时。

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
│   ├── common/          # 通用响应和异常
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
mvn test
mvn package -DskipTests
mvn spring-boot:run
```

## 环境变量

- `DB_URL`：PostgreSQL JDBC 地址，例如 `jdbc:postgresql://localhost:5432/agent_knowledge`。
- `DB_USERNAME`：数据库用户名。
- `DB_PASSWORD`：数据库密码。
- `DOCUMENT_UPLOAD_MAX_FILE_SIZE`：单文件上传大小上限，默认 `50MB`。
- `DOCUMENT_UPLOAD_MAX_REQUEST_SIZE`：单次 multipart 请求大小上限，默认 `50MB`。
- `AI_SERVICE_BASE_URL`：Python AI 服务地址，默认本地 FastAPI。
- `AI_SERVICE_MOCK_ENABLED`：是否启用 AI mock。
- `AI_SERVICE_READ_TIMEOUT`：调用 AI 服务读取超时。

真实密码只放在本地环境，不写入代码、测试或文档。

## 主要接口

- `GET /api/health`
- `GET|POST|PUT|DELETE /api/knowledge-bases`
- `POST /api/documents/upload`
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
- `GET /api/rag/experiments/evaluations/summary`
- `POST /api/feedback`
- `GET /api/graph/facts`

## 关键入口

- `controller/RagController.java`：RAG、实验、评测集和对比相关 API。
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
- 为评测集导入导出补充接口。
- 为 token / cost 估算增加模型单价配置，但必须标记为估算值。
- 增加更多 Controller 层契约测试。
