# 2026-05-27 RAG 实验列表接口

## 背景

当前 `GET /api/rag/experiments` 已有 Controller 入口，但返回的是硬编码占位数据。前端实验页已经调用该接口，项目规划中也要求沉淀 `rag_experiments` 表，用于后续对比不同 chunk、embedding、retriever 和 reranker 策略。

## 当前目标

本轮只完成一个接口：`GET /api/rag/experiments` 从数据库读取实验记录并返回给前端。

## 涉及模块

- Spring Boot 后端
- PostgreSQL / Flyway 迁移
- RAG 实验相关 DTO、Domain、Repository、Service
- 项目过程文档

## 预计修改文件

- `backend-java/src/main/resources/db/migration/V202605270930__create_rag_experiments.sql`
- `backend-java/src/main/java/com/example/agentknowledge/domain/RagExperiment.java`
- `backend-java/src/main/java/com/example/agentknowledge/repository/RagExperimentRepository.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/rag/RagExperimentResponse.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
- `docs/reviews/2026-05-27-rag-experiments-list-review-prompt.md`
- `docs/testing/failures/2026-05-27-rag-experiments-list-notes.md`
- `docs/handoff/CURRENT_STATE.md`

## 非范围

- 本轮不实现 `POST /api/rag/experiments`。
- 本轮不实现评估任务调度、自动运行评估集或图表展示。
- 本轮不改前端实验页结构，只保证已有列表接口可从真实表读取。

## 验证方式

- 运行 Java 后端测试或至少编译测试。
- 检查 Flyway 迁移文件可被识别。
- 人工检查接口响应字段与前端 `ExperimentRecord` 类型一致。

## 当前风险

- 项目当前没有 Java 自动化测试目录，本轮可能主要依赖 `mvn test` 编译验证。
- 如果本地 PostgreSQL 未启动，只能验证编译，不能执行真实数据库迁移。
- 当前实验指标字段仍是第一版业务抽象，后续评估体系完善后可能需要扩展。
