# Review Prompt: frontend-react 售后支持工作台美学与中文化优化

请审查本次 `frontend-react/` 改动，重点关注：

1. `supportPlan` 类型、API 映射与 `ChatPage` 渲染是否和后端 `AssistantTurnResponse` 契约一致。
2. `agentName` / `variables` 是否能稳定触发 AI 服务售后技术支持 Agent 编排，且不影响普通 RAG 发送流程。
3. `ChatPage` 的知识库选择、新建会话、发送中、无知识库、无引用、移动端布局是否存在状态缺口。
4. 中文化改动是否误改了必须保留的 API 字段、schema 字段或评测指标含义。
5. 全局 token、样式收敛和 Vite root 显式配置是否会影响既有页面、构建和开发启动。
6. 是否需要把 `supportPlan` 持久化到消息记录或 trace 回查，以支持历史会话重新打开后的结构化展示。

已验证：

- `npm.cmd --prefix frontend-react run typecheck`
- `npm.cmd --prefix frontend-react run build`
- Playwright + system Edge stub 后端验证 `/chat`、`/documents` 和移动端 `/chat`。
