# 2026-05-27 RAG 实验详情接口 review 提示

## 本次 review 目标

请 review `GET /api/rag/experiments/{id}` 是否按统一资源路径查询单个实验，并确认不存在记录时是否通过统一异常结构返回 404。

## 本次接口范围

- `GET /api/rag/experiments/{id}`
  - 入口：`backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
  - 作用：按 ID 查询单个 RAG 实验记录，返回与列表和创建接口一致的 `RagExperimentResponse`。

## 重点 review 顺序

1. Service 查询逻辑
   - `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
   - 检查是否通过 Repository 查询真实记录，未找到时是否抛出 `ResourceNotFoundException`。

2. Controller 路径
   - `backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
   - 检查 `GET /api/rag/experiments/{id}` 是否和列表、创建接口在同一资源路径下。

3. 响应契约
   - `backend-java/src/main/java/com/example/agentknowledge/dto/rag/RagExperimentResponse.java`
   - 确认详情、列表、创建三类接口响应字段一致，避免前端重复适配。

## 当前占位实现

- 本轮只查询实验基础信息，不聚合该实验关联的 RAG run、评估问题或对比图数据。
- 本轮不实现前端详情页。

## 已执行验证

- 在 `backend-java/` 下运行 `mvn test`，结果为 `BUILD SUCCESS`。
- 当前没有 Java 测试源码，因此本轮验证重点是编译、Controller 路由、Service 查询逻辑和统一异常引用。
- 本轮未启动 PostgreSQL，尚未执行真实 HTTP 查询 smoke。

## Review 时特别注意

- 详情接口不要返回硬编码数据。
- 未找到实验时应走全局异常处理，而不是返回空对象。
- 当前响应的 precision/recall 同时保留数值字段和展示字段，方便后续前端图表和列表直接使用。
