# 2026-06-09 知识库对话 AI 调用超时失败记录

## 现象

知识库对话提问后，后端抛出 `SocketTimeoutException: Read timed out`。外层日志显示 `content type [application/octet-stream]`，但这不是主要问题；主要问题是 Java 侧等 FastAPI 响应超过读取超时。

## 原因

Spring Boot `app.ai-service.read-timeout` 默认只有 30 秒，低于 Python AI 服务一次模型调用和重试可能需要的时间。

## 修复

- Spring Boot AI 服务读取超时默认调整为 180 秒
- 前端聊天类请求超时调整为 180 秒
- Java AI Client 增加 Agent 调用开始 / 成功日志

## 验证

- `mvn.cmd -q -DskipTests compile`
- `npm.cmd --prefix frontend run typecheck`
