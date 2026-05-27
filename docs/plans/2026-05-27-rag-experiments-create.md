# 2026-05-27 RAG 实验创建接口

## 背景

上一轮已完成 `GET /api/rag/experiments`，实验页可以从 `rag_experiments` 表读取记录。当前还缺少创建实验配置的入口，后续无法通过 API 沉淀不同 RAG 策略、数据集和指标记录。

## 当前目标

本轮只完成一个接口：`POST /api/rag/experiments` 创建 RAG 实验记录。

## 涉及模块

- Spring Boot 后端
- RAG 实验 DTO、Service、Controller
- 项目过程文档

## 预计修改文件

- `backend-java/src/main/java/com/example/agentknowledge/dto/rag/CreateRagExperimentRequest.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
- `docs/reviews/2026-05-27-rag-experiments-create-review-prompt.md`
- `docs/testing/failures/2026-05-27-rag-experiments-create-notes.md`
- `docs/handoff/CURRENT_STATE.md`
- `PROJECT_CONTEXT.md`

## 非范围

- 本轮不实现更新、删除或详情查询实验接口。
- 本轮不触发真实评估任务，也不调用 FastAPI。
- 本轮不调整前端页面表单。

## 验证方式

- 运行 Java 后端 `mvn test`。
- 人工检查请求 DTO 校验约束与数据库字段长度一致。
- 人工检查创建后复用 `RagExperimentResponse`，与列表接口响应结构一致。

## 当前风险

- 本地 PostgreSQL 未保持运行时，无法做真实 HTTP 创建 smoke。
- 指标字段当前允许手动传入，后续接评估任务后可能需要改成由评估流程回填。
