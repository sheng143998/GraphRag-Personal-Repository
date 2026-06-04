# 2026-05-29 修复 chunks=[] bug（AI 服务 InMemory 回退）

## 背景
上次 smoke 发现 POST /api/documents/upload 返回 chunkCount=1，但 GET /api/documents/{id} 返回 chunkCount=0, chunks=[]。

## 根因分析
.env 中 DATABASE_URL 和 AI_DATABASE_URL 均为空字符串，AI 服务 config.py 的 database_url 解析为 ""。
uild_repository() 中 settings.rag_use_database and settings.database_url → True and "" → falsy，回退到 InMemoryDocumentRepository。
chunks 只存内存，不写入 PostgreSQL document_chunks 表，Spring Boot 查询自然为空。

## 修复方案
修改 i-service/app/core/config.py，当 DATABASE_URL / AI_DATABASE_URL 为空时，从 DB_URL（JDBC 格式）+ DB_USERNAME + DB_PASSWORD 构造标准 PostgreSQL URL：
- jdbc:postgresql://host:port/dbname → postgresql://user:password@host:port/dbname

## 涉及文件
- i-service/app/core/config.py

## 验证方式
1. AI 服务语法编译 python -m compileall ai-service/app
2. 重启 AI 服务，确认仓库初始化为 PostgresDocumentRepository
3. 上传文档后查询 document_chunks 表确认 chunk 已写入
4. 调用 GET /api/documents/{id} 确认 chunks 非空
