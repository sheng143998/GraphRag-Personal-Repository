# Review: 2026-06-05 前端接口补齐

## Review 目标

请重点 review 本轮补齐的前端代码是否与 `docs/architecture/api-design.md` 契约对齐，以及是否遵守 PROJECT_CONTEXT.md 中的前端规范。

## 重点文件

### 基础层
- `frontend/src/types/index.ts` — 新增 11 个类型、扩展 4 个现有类型
- `frontend/src/api/client.ts` — extractErrorMessage 修复

### API 模块
- `frontend/src/api/chat.ts` — 新增 4 个会话/消息函数 + 修复 sendChatMessage
- `frontend/src/api/experiments.ts` — 完整 CRUD（5 函数）
- `frontend/src/api/feedback.ts` — 新建
- `frontend/src/api/rag.ts` — 新建
- `frontend/src/api/knowledgeBases.ts` — 新增 createKnowledgeBase
- `frontend/src/api/index.ts` — re-export 补齐

### Store
- `frontend/src/stores/workbench.ts` — hydrate 容错修复 + 14 个新增 actions

### 页面
- `frontend/src/pages/chat/ChatPage.vue` — 会话管理面板
- `frontend/src/pages/experiments/ExperimentsPage.vue` — CRUD 表单
- `frontend/src/pages/feedback/FeedbackPage.vue` — 新建
- `frontend/src/pages/settings/SettingsPage.vue` — 可编辑

### 路由
- `frontend/src/router/index.ts` — /feedback 路由
- `frontend/src/layouts/WorkbenchLayout.vue` — 导航入口

## Review 检查点

- 新增类型字段是否与 `docs/architecture/api-design.md` 中定义的请求/响应结构对齐。
- API 模块函数路径前缀是否均使用 Spring Boot `/api/*`，无直调 FastAPI 的情况。
- Store actions 是否正确组装请求参数并更新本地状态。
- 页面表单是否有 loading / error / empty 三态处理。
- SettingsPage localStorage 持久化是否正确。
- ChatPage 会话管理：选择会话后是否加载后端消息、发送问题时是否附带 sessionId。
- 是否符合 Vue 3 Composition API + TypeScript + Pinia 模式。

## 对照代码

后端参考（验证字段对齐用）：

- `backend-java/src/main/java/com/example/agentknowledge/controller/ChatController.java`
- `backend-java/src/main/java/com/example/agentknowledge/controller/FeedbackController.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/chat/*.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/feedback/*.java`
- `backend-java/src/main/java/com/example/agentknowledge/common/api/ApiResponse.java`

## 验证命令

```bash
cd frontend && npm run build
```

## 当前未验证项

- 全链路 HTTP smoke（需要后端服务运行）
- 浏览器端页面 UI 交互验证
