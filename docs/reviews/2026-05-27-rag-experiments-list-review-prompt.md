# 2026-05-27 RAG 实验列表接口 review 提示

## 本次 review 目标

请 review `GET /api/rag/experiments` 是否已经从硬编码占位切换为数据库读取，并确认新增的 `rag_experiments` 表、Java 实体、仓储、服务和 DTO 契约是否适合作为后续 RAG 评估平台的基础。

## 本次接口范围

- `GET /api/rag/experiments`
  - 入口：`backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
  - 作用：查询 RAG 实验记录列表，按更新时间倒序返回给前端实验页。

## 重点 review 顺序

1. 数据库迁移
   - `backend-java/src/main/resources/db/migration/V202605270930__create_rag_experiments.sql`
   - 检查字段是否覆盖实验名称、策略、数据集、样本数、precision、recall、状态、备注和时间戳。

2. Java 持久化模型
   - `backend-java/src/main/java/com/example/agentknowledge/domain/RagExperiment.java`
   - `backend-java/src/main/java/com/example/agentknowledge/repository/RagExperimentRepository.java`
   - 检查字段类型、表名、时间戳和排序方法是否与迁移一致。

3. 服务和响应契约
   - `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
   - `backend-java/src/main/java/com/example/agentknowledge/dto/rag/RagExperimentResponse.java`
   - 检查 `precision`、`recall` 是否以字符串兼容当前前端类型，同时保留原始数值字段供后续扩展。

4. Controller 接口
   - `backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
   - 确认已移除硬编码实验数据，接口仍保持 `ApiResponse<List<...>>` 结构和 trace 返回。

## 当前占位实现

- 本轮只实现列表查询，不新增创建实验接口。
- precision、recall 当前允许为空，返回前端时显示为 `待评估`。
- 本轮不接入真实评估任务，实验记录需要后续接口或迁移种子数据写入。

## 已执行验证

- 在 `backend-java/` 下运行 `mvn test`，结果为 `BUILD SUCCESS`。
- 当前没有 Java 测试源码，因此本轮验证重点是编译、资源复制、JPA 映射和 Controller 注入链路。
- 本轮未启动 PostgreSQL，尚未执行真实 Flyway 迁移验证。

## Review 时特别注意

- 不要把实验记录重新写成 Controller 内硬编码数据。
- 迁移文件必须追加新版本，不修改历史迁移。
- 如果后续新增 `POST /api/rag/experiments`，应复用本轮新增的实体和服务，不要另起一套实验模型。
