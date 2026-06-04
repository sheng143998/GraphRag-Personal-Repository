# 2026-05-29 文档删除 + documentType 修复 + 全链路 smoke 失败复盘

## 问题 1：AI 服务端口不匹配
- 现象：文档上传 500，Java 无法连接 AI
- 根因：`application.yml` 默认 `AI_SERVICE_BASE_URL=http://localhost:8001`，实际 AI 在 8000
- 处理：启动时通过环境变量 `AI_SERVICE_BASE_URL=http://localhost:8000` 覆盖

## 问题 2：documentType 枚举值大小写
- 现象：AI 服务返回 422 `value is not a valid enumeration member`
- 根因：AI 服务 Pydantic 枚举期望小写（如 `tech_note`），Java 端传入大写（`TECH_NOTE`）
- 处理：`DocumentService.create()` 中对 `documentType` 调用 `.toLowerCase()`

## 问题 3：Java 启动缺少 DB 凭据
- 现象：Flyway 认证失败 `user "agent" password authentication failed`
- 根因：`application.yml` 默认用户 `agent`，实际是 `postgres`
- 处理：batch 脚本注入 `DB_URL`/`DB_USERNAME`/`DB_PASSWORD` 环境变量

## 问题 4：PowerShell 环境变量尾随空格
- 现象：认证失败 `user "postgres "`（注意尾随空格）
- 根因：`.env` 文件解析时未 trim
- 处理：改用正则 `[regex]::Match()` + `.Trim()`
