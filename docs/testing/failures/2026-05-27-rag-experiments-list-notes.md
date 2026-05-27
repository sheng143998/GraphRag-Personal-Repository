# 2026-05-27 RAG 实验列表接口过程记录

## 背景

本次任务是把 `GET /api/rag/experiments` 从硬编码占位改为数据库读取，为后续 RAG 实验评估平台打基础。

## 当前状态

本轮接口已完成代码实现，并完成 Java 后端最小验证。

## 已知风险

- 当前项目没有 Java 测试目录，本轮可能只能通过 `mvn test` 做编译和上下文验证。
- 如果本地 PostgreSQL 未启动，本轮不会强行启动数据库，只记录无法做真实迁移验证的原因。

## 问题 1：`mvn test` 成功但 javac 关闭本地依赖 jar 时打印访问拒绝

- 现象：`mvn test` 最终返回 `BUILD SUCCESS`，但编译阶段输出 `java.nio.file.AccessDeniedException`。
- 触发场景：在 `backend-java/` 下运行 `mvn test`。
- 报错摘要：访问被拒绝路径为 `backend-java/maven-repo/jakarta/transaction/jakarta.transaction-api/2.0.1/jakarta.transaction-api-2.0.1.jar`。
- 根因分析：本地 Maven 仓库中的 jar 可能被杀毒软件、索引器或另一个 Java 进程短暂占用；当前 Maven 任务最终成功，未阻塞编译产物生成。
- 解决方案：本轮未做破坏性清理。若后续持续出现，可关闭占用进程后重跑，或在确认路径后清理该单个依赖目录让 Maven 重新下载。
- 后续避免方式：遇到类似问题时先看 Maven 最终退出码和 `BUILD SUCCESS/FAILURE`，不要直接删除整个本地仓库。
- 是否补充自动化测试：不涉及业务逻辑，无需新增自动化测试。

## 已执行验证

- `mvn test`：通过，当前项目没有 Java 测试源码，因此主要验证编译、资源复制和 Spring Boot 构建链路。
- 未执行真实数据库迁移：本轮没有启动 PostgreSQL，本次只完成接口编译级验证。
