# 2026-06-09 AI Agent 报错但 Python 侧无日志记录

## 现象

Spring Boot 日志显示 `/api/chat/{sessionId}/assistant-turn` 调用 AI Agent 时超时：

```text
RestClientException: Error while extracting response for type AiAgentInvokeResponse
Caused by: java.net.SocketTimeoutException: Read timed out
```

同时 FastAPI 控制台没有明显请求日志。

## 判断

FastAPI 当前只有 Uvicorn access log 和少量业务日志，Agent 路由本身没有入口日志；因此“Python 没日志”不能直接证明请求没到 Python。

## 修复

- FastAPI 新增请求 middleware 日志
- Agent 路由和 AgentService 新增入口、完成、失败日志
- 日志使用 ASCII 文案，避免 Windows 控制台编码问题

## 后续定位规则

- 如果下次出现 Java 超时，但 FastAPI 有 `AI request start`，说明请求到了 Python，继续看是否卡在 Agent workflow / embedding / rerank / LLM。
- 如果 FastAPI 连 `AI request start` 都没有，说明 Java 请求没有打到当前 Python 服务，优先检查 `AI_SERVICE_BASE_URL`、端口和是否重启到最新进程。
