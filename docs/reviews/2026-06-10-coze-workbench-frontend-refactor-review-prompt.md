# 2026-06-10 Coze 工作台风格前端重构 Review Prompt

## Review 目标

请重点审查本轮前端重构是否在不改变后端接口契约的前提下，将 Vue 前端统一为 Coze Studio 风格的浅色工作台布局，并继续遵守“浏览器只调用 Spring Boot `/api/*`”的边界。

## 重点文件

- `frontend/src/layouts/WorkbenchLayout.vue`
  - 检查全局窄主导航、二级导航、顶栏和内容区是否结构清晰。
  - 检查导航分组、当前路由高亮和 trace / 策略状态是否可读。
- `frontend/src/styles.css`
  - 检查 Coze 风格 token、面板、表单、列表、状态、聊天、移动端响应式是否一致。
  - 检查是否仍存在暗色玻璃态、大面积渐变、过大圆角或文本溢出。
- `frontend/src/pages/chat/ChatPage.vue`
  - 检查三栏布局中会话、上传、消息流、composer、引用来源、策略和学习面板是否保留原功能。
  - 检查移动端单栏堆叠是否可用。
- `frontend/src/pages/documents/DocumentsPage.vue`
  - 检查文档上传、列表、详情和 metadata 显示是否仍可用，且已转为浅色工作台风格。
- `frontend/src/pages/knowledge-base/KnowledgeBasePage.vue`
  - 检查创建 / 编辑 / 详情 / 删除入口是否仍可用。
- `frontend/src/pages/graph/GraphPage.vue`
  - 检查图谱过滤、实体和关系三栏工作台排布。
- `frontend/src/pages/feedback/FeedbackPage.vue`
  - 检查反馈表单和右侧上下文摘要是否可用。
- `frontend/src/pages/settings/SettingsPage.vue`
  - 检查 AI 服务地址是否仅作为 Spring Boot 桥接诊断语义，不暗示前端直连 FastAPI。

## 验证命令

```powershell
npm.cmd --prefix frontend run typecheck
npm.cmd --prefix frontend run build
rg -n "fetch\\(|axios|/ai/|http://localhost:800|AI_SERVICE|aiServiceBaseUrl" frontend/src
npm.cmd --prefix frontend run preview -- --host 127.0.0.1 --port 4173
```

## 截图检查

建议检查以下页面：

- `http://127.0.0.1:4173/chat` 桌面和移动端
- `http://127.0.0.1:4173/documents`
- `http://127.0.0.1:4173/experiments`
- `http://127.0.0.1:4173/graph`
- `http://127.0.0.1:4173/settings`

## 重点风险

- `ChatPage.vue` 保留了较多业务 workflow，需确认 UI 重排没有遗漏弱点练习、追问、学习计划和引用来源状态。
- 本轮主要做 UI / layout 重构，未拆分 `workbench` store；后续如继续扩展，应再做状态分域。
- `aiServiceBaseUrl` 字段仍在 settings 类型中保留用于兼容本地设置，但不应被页面用于直接请求 FastAPI。
