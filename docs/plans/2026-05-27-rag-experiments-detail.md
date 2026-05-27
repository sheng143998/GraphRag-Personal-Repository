# 2026-05-27 RAG 实验详情接口

## 背景

当前已经完成 `GET /api/rag/experiments` 和 `POST /api/rag/experiments`。为了让前端后续能够进入某个实验详情页、查看实验配置和指标，需要补齐按 ID 查询实验记录的接口。

## 当前目标

本轮只完成一个接口：`GET /api/rag/experiments/{id}` 查询单个 RAG 实验详情。

## 涉及模块

- Spring Boot 后端
- RAG 实验 Service 与 Controller
- 项目过程文档

## 预计修改文件

- `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
- `backend-java/README.md`
- `docs/reviews/2026-05-27-rag-experiments-detail-review-prompt.md`
- `docs/testing/failures/2026-05-27-rag-experiments-detail-notes.md`
- `docs/handoff/CURRENT_STATE.md`
- `PROJECT_CONTEXT.md`

## 非范围

- 本轮不实现实验更新、删除或运行详情聚合。
- 本轮不新增前端详情页。
- 本轮不触发真实 RAG 评估任务。

## 验证方式

- 运行 Java 后端 `mvn test`。
- 人工检查不存在记录时是否抛出统一 `ResourceNotFoundException`。
- 人工检查响应 DTO 与列表和创建接口保持一致。

## 当前风险

- 本地 PostgreSQL 未启动时，只能做编译级验证，不能做真实 HTTP 查询 smoke。
