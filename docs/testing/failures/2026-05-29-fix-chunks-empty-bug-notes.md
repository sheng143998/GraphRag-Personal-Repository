# 2026-05-29 修复 chunks 为空问题

## 问题
smoke 时 POST /api/documents/upload 返回 chunkCount=1，但 GET /api/documents/{id} 返回 chunks=[]

## 根因
.env 中 DATABASE_URL 和 AI_DATABASE_URL 均为空，AI 服务 uild_repository() 因 database_url="" 回退到 InMemoryDocumentRepository，chunks 只存内存不写 PostgreSQL。

## 教训
- AI 服务与 Spring Boot 使用不同的环境变量命名约定，.env 模板应包含两套变量
- 启动脚本 / smoke 流程应显式检查 AI 服务仓库类型（Postgres vs InMemory）
- InMemoryDocumentRepository 在联调场景下是危险默认：静默成功但不持久化
