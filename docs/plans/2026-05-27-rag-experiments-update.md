# 2026-05-27 RAG 实验更新接口

## 背景

当前 RAG 实验已经支持列表、创建和详情查询。后续实验运行后，需要能够回填 precision、recall、样本数、状态和备注，也需要修正实验名称、策略和数据集信息，因此需要补齐更新接口。

## 当前目标

本轮只完成一个接口：`PUT /api/rag/experiments/{id}` 更新 RAG 实验记录。

## 涉及模块

- Spring Boot 后端
- RAG 实验 DTO、Service 与 Controller
- 项目过程文档

## 预计修改文件

- `backend-java/src/main/java/com/example/agentknowledge/dto/rag/UpdateRagExperimentRequest.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
- `backend-java/README.md`
- `docs/reviews/2026-05-27-rag-experiments-update-review-prompt.md`
- `docs/testing/failures/2026-05-27-rag-experiments-update-notes.md`
- `docs/handoff/CURRENT_STATE.md`
- `PROJECT_CONTEXT.md`

## 非范围

- 本轮不实现删除接口。
- 本轮不实现自动评估任务回调。
- 本轮不新增前端编辑表单。

## 验证方式

- 运行 Java 后端 `mvn test`。
- 人工检查请求 DTO 的指标范围限制。
- 人工检查不存在记录时仍走统一 404。

## 当前风险

- 本轮更新接口采用“只更新请求中传入的字段”的方式，空字符串字段会被忽略，后续如果需要清空字段可再补专门语义。
- 本地 PostgreSQL 未启动时，只能做编译级验证，不能做真实 HTTP 更新 smoke。
