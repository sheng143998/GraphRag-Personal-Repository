# 2026-06-09 知识库对话 AI 调用超时 Review 提示

请重点检查：

- `backend-java/src/main/resources/application.yml`
- `backend-java/src/main/java/com/example/agentknowledge/client/AiServiceClient.java`
- `frontend/src/api/chat.ts`

关注点：

1. 180 秒默认读取超时是否覆盖本地模型 / OpenAI-compatible provider 的常见响应时间
2. 前端聊天接口是否和后端超时保持一致
3. 新增日志是否包含 traceId、agentName、strategyName 等定位信息
4. 是否仍然保留 `AI_SERVICE_READ_TIMEOUT` 环境变量覆盖能力
