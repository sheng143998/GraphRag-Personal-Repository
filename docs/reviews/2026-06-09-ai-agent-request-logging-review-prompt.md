# 2026-06-09 AI Agent 请求入口日志 Review 提示

请重点检查：

- `ai-service/app/main.py`
- `ai-service/app/api/routes/agent.py`
- `ai-service/app/services/agent_service.py`

关注点：

1. FastAPI middleware 是否能覆盖所有 `/ai/*` 请求
2. 日志是否包含 Java 透传的 `X-Trace-Id`
3. Agent 路由日志是否避免打印完整问题和密钥等敏感内容
4. 失败日志是否会保留异常栈，便于定位卡在 retrieval / embedding / rerank / LLM 哪一步
