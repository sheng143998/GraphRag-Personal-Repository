# 2026-05-29 修复 chunks=[] bug review 提示

## 涉及文件
- i-service/app/core/config.py — 新增 _build_database_url() 从 DB_URL + DB_USERNAME + DB_PASSWORD 构造 PostgreSQL URL

## 变更要点
1. 当 AI_DATABASE_URL 和 DATABASE_URL 均为空时，解析 JDBC 格式 DB_URL 并拼接标准 PostgreSQL URL
2. 对用户名/密码做 quote_plus URL 编码，避免特殊字符问题
3. 无密码时省略 :password 段

## 验证结果
- Python compileall 通过
- 模拟环境变量测试：database_url 正确拼接，epo type: PostgresDocumentRepository
- 待重启 AI 服务后执行完整 smoke

## 重点 review
- _build_database_url() 正则是否正确匹配 JDBC URL 各段
- quote_plus 在密码包含 @ 等特殊字符时行为是否符合预期
