# 2026-05-29 文档详情与 chunk 摘要

## 背景

本次任务是增强 `GET /api/documents/{id}`，为文档入库 Demo 提供可 review 的 chunk 摘要。

## 当前状态

本轮接口已完成代码实现，并完成 Java 后端构建、前端构建和 AI 服务语法验证。

## 已知风险

- 当前不会启动本地数据库和服务，HTTP smoke 可能仍无法执行。
- Java 编译阶段历史 Maven jar 访问拒绝日志可能继续出现，但此前未阻塞构建。

## 问题记录

### 问题 1：Java 编译结束阶段仍打印本地 Maven jar 访问拒绝

- 现象：`mvn.cmd test` 最终 `BUILD SUCCESS`，但 javac 关闭 jar 时打印 `AccessDeniedException`。
- 触发场景：Java 后端编译阶段。
- 报错摘要：路径为 `backend-java/maven-repo/jakarta/transaction/jakarta.transaction-api/2.0.1/jakarta.transaction-api-2.0.1.jar`。
- 根因分析：这是历史已出现的本地 Maven 依赖 jar 占用或权限问题。
- 解决方案：本轮不做破坏性清理，因为构建已成功。
- 后续避免方式：如需彻底处理，只清理该单个依赖目录并重新拉取。
- 是否补充自动化测试：不涉及业务逻辑。

## 已执行验证

- `mvn.cmd test`：通过。
- `npm.cmd run build`：通过。
- `python -m compileall app tests`：通过。
- HTTP smoke：未执行，未启动本地依赖服务。
