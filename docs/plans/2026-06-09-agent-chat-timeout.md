# 2026-06-09 知识库对话 AI 调用超时修复计划

## 背景

知识库对话提问后，Spring Boot 日志出现：

```text
RestClientException: Error while extracting response for type AiAgentInvokeResponse and content type application/octet-stream
Caused by: java.net.SocketTimeoutException: Read timed out
```

关键根因是 Java 后端调用 FastAPI `/ai/agent/invoke` 时读取超时。当前 Spring Boot 默认 `AI_SERVICE_READ_TIMEOUT` 为 30 秒，而 Python 模型调用默认可能等待 60 秒并带重试，因此 Java 侧过早断开。

## 目标

- 放宽 Spring Boot 调用 AI 服务的读取超时
- 放宽前端聊天请求等待时间，避免浏览器先中断
- 增加 AI Agent 调用日志，便于判断卡在 Java -> FastAPI 还是 FastAPI -> 模型服务

## 改动

- `backend-java/src/main/resources/application.yml` 默认 `AI_SERVICE_READ_TIMEOUT` 调整为 `180s`
- `frontend/src/api/chat.ts` 对知识库对话、旧 RAG query、薄弱点练习请求设置 `180000ms` 超时
- `AiServiceClient.invokeAgent(...)` 增加调用开始 / 成功返回日志

## 验证

- `mvn.cmd -q -DskipTests compile`
- `npm.cmd --prefix frontend run typecheck`
