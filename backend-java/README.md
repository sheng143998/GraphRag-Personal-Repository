# Java 业务后端模块

## 模块职责

Java 业务后端负责对外提供统一业务接口，管理知识库、文档、会话、运行记录和反馈等业务数据，并负责调用 Python 人工智能服务。

前端不直接调用人工智能服务，所有检索增强生成请求都应先进入 Java 后端。

## 技术栈

- Java 21。
- Spring Boot。
- Spring Data JPA。
- Flyway。
- PostgreSQL。
- pgvector。

## 目录结构说明

```text
backend-java/
├─ src/main/java/com/example/agentknowledge/
│  ├─ client/          # 调用人工智能服务
│  ├─ common/          # 通用响应和异常结构
│  ├─ config/          # 配置类
│  ├─ controller/      # 对外接口入口
│  ├─ domain/          # 数据库实体
│  ├─ dto/             # 请求和响应对象
│  ├─ repository/      # 数据访问
│  └─ service/         # 业务逻辑
├─ src/main/resources/
│  ├─ application.yml
│  └─ db/migration/   # Flyway 迁移脚本
└─ pom.xml
```

## 本地启动方式

启动前需要确保 PostgreSQL 可连接，且数据库迁移可以正常执行。

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

## 环境变量说明

- `SPRING_DATASOURCE_URL`：数据库连接地址。
- `SPRING_DATASOURCE_USERNAME`：数据库用户名。
- `SPRING_DATASOURCE_PASSWORD`：数据库密码。
- `AI_SERVICE_BASE_URL`：Python 人工智能服务基础地址。
- `AI_SERVICE_MOCK_ENABLED`：是否启用人工智能服务模拟返回。真实联调时应为 `false`。

真实密码只放在本地环境，不写入代码、测试或文档。

## 关键代码入口

- `controller/RagController.java`：检索增强生成对外接口。
- `service/RagService.java`：检索增强生成业务流程。
- `client/AiServiceClient.java`：调用 Python 人工智能服务。
- `domain/RagRun.java`：运行记录实体。
- `domain/RagRetrievalResult.java`：检索结果实体。
- `repository/`：数据库访问入口。
- `src/main/resources/db/migration/`：数据库迁移脚本。

## 主要接口

- `GET /api/health`
- `GET /actuator/health`
- `GET /api/knowledge-bases`
- `POST /api/rag/query`
- `GET /api/rag/runs/{id}`
- `GET /api/rag/experiments`
- `GET /api/rag/experiments/{id}`
- `POST /api/rag/experiments`
- `PUT /api/rag/experiments/{id}`
- `DELETE /api/rag/experiments/{id}`

## 重点审查文件

- `src/main/java/com/example/agentknowledge/controller/RagController.java`
- `src/main/java/com/example/agentknowledge/service/RagService.java`
- `src/main/java/com/example/agentknowledge/client/AiServiceClient.java`
- `src/main/java/com/example/agentknowledge/client/dto/`
- `src/main/java/com/example/agentknowledge/domain/RagRun.java`
- `src/main/java/com/example/agentknowledge/domain/RagRetrievalResult.java`
- `src/main/resources/db/migration/`

## 与其他模块的调用关系

```text
前端
-> Java Controller
-> Java Service
-> AiServiceClient
-> Python FastAPI
-> PostgreSQL 与 pgvector
```

## 当前已实现能力

- 基础健康检查。
- 知识库基础查询。
- 数据库迁移。
- `POST /api/rag/query` 调用 Python `/ai/rag/query`。
- 保存 `rag_runs` 和 `rag_retrieval_results`。
- 使用结构化元数据写入 JSONB 字段。
- 查询、创建、按 ID 查看、更新和删除 RAG 实验记录。

## 当前占位实现

- 部分业务接口仍是基础能力或待扩展状态。
- Java 自动化测试仍需补充更细的服务层和客户端契约测试。

## 后续待补能力

- 文档上传接口和解析状态回写。
- 会话消息完整保存。
- RAG 反馈接口。
- RAG 实验自动评估接口。
- 更完整的异常码和前端可读错误信息。

## 常见问题

- 如果启动失败，先检查数据库是否可连接。
- 如果迁移失败，检查 `db/migration/` 中脚本顺序和 pgvector 扩展。
- 如果检索增强生成接口返回模拟数据，检查 `AI_SERVICE_MOCK_ENABLED` 是否为 `false`。
- 如果调用人工智能服务失败，确认 Python 服务已启动并检查 `AI_SERVICE_BASE_URL`。
