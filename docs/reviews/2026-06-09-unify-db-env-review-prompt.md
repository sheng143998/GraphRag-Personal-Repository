# 2026-06-09 统一数据库环境变量 Review 提示

请重点检查：

- `.env`
- `.env.example`
- `backend-java/src/main/resources/application.yml`
- `ai-service/app/core/config.py`
- `ai-service/README.md`
- `scripts/README.md`

关注点：

1. 是否所有运行配置都统一使用 `DB_URL` / `DB_USERNAME` / `DB_PASSWORD`
2. AI 服务是否优先且只从 `DB_URL` 推导 PostgreSQL URL
3. 默认值是否与用户本地 PostgreSQL 配置一致
4. 文档是否不再引导使用 `AI_DATABASE_URL` / `DATABASE_URL`
