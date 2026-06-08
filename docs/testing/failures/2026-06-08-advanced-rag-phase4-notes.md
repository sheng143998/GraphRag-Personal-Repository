# 2026-06-08 Advanced RAG 第四阶段记录

## 现象

本记录用于复盘 `advanced-rag-phase4-notes` 相关验证或启动过程中出现的问题。历史记录中的命令、路径和错误关键字保留原样，便于再次检索。

## 观察

- Docker Desktop 未就绪时，Docker 相关命令可能无法启动 PostgreSQL / Redis。
- 本地非 Docker 路径可使用已有 PostgreSQL 配置启动 Spring Boot 与 FastAPI。
- 如果运行中的 jar 过旧，可能出现接口缺失、删除失败或 smoke 检查不一致。
- AI 内存模式返回的 citation id 可能不在 Java 数据库中，Spring Boot 持久化检索结果时需要容错处理。

## 已采取处理

- 使用 stub provider 和内存 RAG 存储稳定 AI 测试。
- 使用本地 PostgreSQL 凭据启动 Spring Boot，绕开 Docker daemon 不可用问题。
- 重新构建后端 jar，确保路由和服务实现同步。
- 对缺失本地 document/chunk 行的 citation 做安全关联，保留检索 metadata。

## 后续建议

- 保留非 Docker 全链路脚本作为默认本地验证路径。
- 增加 Java 集成测试覆盖知识库详情 / 更新 / 删除、文档删除和 RAG retrieval result 持久化。
- 若 Maven 本地仓库 jar 被沙箱拒绝访问，使用非沙箱方式重跑后端测试。
