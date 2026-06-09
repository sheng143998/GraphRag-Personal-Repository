# 2026-06-09 统一数据库环境变量计划

## 背景

用户要求项目数据库配置统一使用：

```env
DB_URL=jdbc:postgresql://localhost:5432/agent_knowledge
DB_USERNAME=postgres
DB_PASSWORD=123456
```

之前 AI 服务还会读取 `AI_DATABASE_URL` / `DATABASE_URL`，`.env.example` 和部分文档也保留了旧变量，容易导致 Java 后端和 AI 服务连接不同数据库，或 AI 服务回退到内存仓库。

## 目标

- Java 后端、AI 服务和本地模板统一使用 `DB_URL` / `DB_USERNAME` / `DB_PASSWORD`
- AI 服务从 JDBC URL 自动推导 Python PostgreSQL URL
- 移除本地模板和说明中的 `AI_DATABASE_URL` / `DATABASE_URL` 主要配置入口

## 验证

- AI 服务配置检查：输出 `PostgresDocumentRepository`
- `ai-service/.venv/bin/python.exe -m py_compile app/core/config.py`
- `mvn.cmd -q -DskipTests compile`
