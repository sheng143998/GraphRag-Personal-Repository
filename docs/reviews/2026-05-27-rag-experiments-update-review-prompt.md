# 2026-05-27 RAG 实验更新接口 review 提示

## 本次 review 目标

请 review `PUT /api/rag/experiments/{id}` 是否能按统一资源路径更新实验记录，并确认字段校验、部分更新语义和 404 处理是否符合 RAG 实验平台后续使用方式。

## 本次接口范围

- `PUT /api/rag/experiments/{id}`
  - 入口：`backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
  - 作用：更新单个 RAG 实验记录，返回更新后的 `RagExperimentResponse`。

## 重点 review 顺序

1. 请求 DTO
   - `backend-java/src/main/java/com/example/agentknowledge/dto/rag/UpdateRagExperimentRequest.java`
   - 检查可选字段、长度限制和 precision/recall 的 0 到 1 范围约束。

2. Service 更新逻辑
   - `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
   - 检查是否先查询真实记录，未找到时是否抛出 `ResourceNotFoundException`，以及是否只更新请求中传入的字段。

3. Controller 路径
   - `backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
   - 检查 `PUT /api/rag/experiments/{id}` 是否和列表、创建、详情接口保持同一资源路径。

## 当前占位实现

- 本轮不实现字段清空语义，空字符串会被忽略。
- 本轮不触发真实 RAG 评估任务，只保存传入的实验字段。
- 本轮不实现前端编辑表单。

## 已执行验证

- 在 `backend-java/` 下运行 `mvn test`，结果为 `BUILD SUCCESS`。
- 当前没有 Java 测试源码，因此本轮验证重点是编译、Controller 路由、请求 DTO 注解和 Service 更新逻辑。
- 本轮未启动 PostgreSQL，尚未执行真实 HTTP 更新 smoke。

## Review 时特别注意

- 更新接口不要创建新实验；找不到记录时必须走 404。
- 指标字段必须限制在 0 到 1。
- 如果传入 `knowledgeBaseId`，必须校验知识库存在。
