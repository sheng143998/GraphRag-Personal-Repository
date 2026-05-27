# 2026-05-27 RAG 实验创建接口 review 提示

## 本次 review 目标

请 review `POST /api/rag/experiments` 是否能按统一 API 结构创建实验记录，并确认请求 DTO、Service 业务规则和 Controller 路径是否与上一轮 `GET /api/rag/experiments` 保持一致。

## 本次接口范围

- `POST /api/rag/experiments`
  - 入口：`backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
  - 作用：创建 RAG 实验配置或手动录入实验结果，返回创建后的实验记录。

## 重点 review 顺序

1. 请求 DTO
   - `backend-java/src/main/java/com/example/agentknowledge/dto/rag/CreateRagExperimentRequest.java`
   - 检查必填字段、长度限制、指标范围和可选知识库 ID 是否合理。

2. Service 业务逻辑
   - `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
   - 检查是否复用 `KnowledgeBaseService` 校验知识库是否存在，默认状态是否稳定，响应映射是否和列表接口一致。

3. Controller 路径
   - `backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
   - 检查 `POST /api/rag/experiments` 是否和 `GET /api/rag/experiments` 放在同一资源路径下，并返回统一 `ApiResponse`。

## 当前占位实现

- 本轮只创建实验记录，不触发自动评估。
- precision、recall 当前可以手动传入，也可以为空；为空时响应展示 `待评估`。
- 本轮不实现前端创建表单。

## 已执行验证

- 在 `backend-java/` 下运行 `mvn test`，结果为 `BUILD SUCCESS`。
- 当前没有 Java 测试源码，因此本轮验证重点是编译、Controller 注入链路、请求 DTO 注解和 Service 依赖注入。
- 本轮未启动 PostgreSQL，尚未执行真实 HTTP 创建 smoke。

## Review 时特别注意

- 不要让 Controller 直接写数据库，业务逻辑应在 Service。
- 如果 `knowledgeBaseId` 传入，必须校验知识库存在。
- 指标范围应限制在 0 到 1，避免后续评估对比图出现异常数据。
