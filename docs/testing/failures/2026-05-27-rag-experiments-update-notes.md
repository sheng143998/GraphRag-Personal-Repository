# 2026-05-27 RAG 实验更新接口过程记录

## 背景

本次任务是新增 `PUT /api/rag/experiments/{id}`，用于更新单个 RAG 实验记录。

## 当前状态

本轮接口已完成代码实现，并完成 Java 后端最小验证。

## 已知风险

- 本地 PostgreSQL 未启动时，只能做 Java 编译级验证。
- 当前项目 Java 测试目录为空，本轮可能主要依赖 `mvn test` 做编译和上下文验证。

## 问题 1：`mvn test` 成功但 javac 关闭本地依赖 jar 时打印访问拒绝

- 现象：`mvn test` 最终返回 `BUILD SUCCESS`，但编译阶段继续输出 `java.nio.file.AccessDeniedException`。
- 触发场景：在 `backend-java/` 下运行 `mvn test`。
- 报错摘要：访问被拒绝路径为 `backend-java/maven-repo/jakarta/transaction/jakarta.transaction-api/2.0.1/jakarta.transaction-api-2.0.1.jar`。
- 根因分析：这是前几轮已持续出现的本地 Maven 依赖 jar 占用或权限问题。当前编译和测试生命周期最终成功，未阻塞业务代码验证。
- 解决方案：本轮不做破坏性清理，只继续记录该本地环境问题。
- 后续避免方式：如需处理，应只清理该单个依赖目录并重新下载，避免删除整个本地仓库。
- 是否补充自动化测试：不涉及业务逻辑，无需新增自动化测试。

## 已执行验证

- `mvn test`：通过，当前项目没有 Java 测试源码，因此主要验证编译、资源复制和 Spring Boot 构建链路。
- 未执行真实 HTTP 更新 smoke：本轮没有启动 PostgreSQL 和后端服务。
