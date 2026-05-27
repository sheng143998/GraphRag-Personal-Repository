# 2026-05-27 RAG 实验删除接口与 HTTP smoke

## 背景

当前 RAG 实验接口已经支持列表、创建、详情和更新。用户明确要求继续完成 `DELETE /api/rag/experiments/{id}`，并启动数据库与后端做真实 HTTP smoke，把已完成的实验接口链路跑通。

## 当前目标

本轮完成一个接口和一次联调验证：

- `DELETE /api/rag/experiments/{id}` 删除 RAG 实验记录。
- 通过 PostgreSQL + Spring Boot HTTP smoke 验证实验接口链路。

## 涉及模块

- Spring Boot 后端
- PostgreSQL / Flyway 迁移验证
- RAG 实验 Controller、Service
- 项目过程文档

## 预计修改文件

- `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
- `backend-java/README.md`
- `docs/reviews/2026-05-27-rag-experiments-delete-and-smoke-review-prompt.md`
- `docs/testing/failures/2026-05-27-rag-experiments-delete-and-smoke-notes.md`
- `docs/handoff/CURRENT_STATE.md`
- `PROJECT_CONTEXT.md`

## 非范围

- 本轮不做前端页面联调。
- 本轮不做 RAG 自动评估任务。
- 本轮不删除数据库卷或重置本地数据。

## 验证方式

- 运行 Java 后端 `mvn test`。
- 启动 PostgreSQL。
- 启动 Spring Boot 后端。
- 通过 HTTP 调用：健康检查、实验列表、创建、详情、更新、删除、删除后再次详情查询 404。

## 当前风险

- Docker Desktop 可能未启动，导致 PostgreSQL 无法启动。
- 8080 端口可能被占用，需要记录原因并避免误杀不属于本项目的进程。
- 当前本地 Maven jar 访问拒绝提示已多次出现，但此前不阻塞构建。
