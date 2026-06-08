# 2026-06-05 前端接口补齐计划

## 背景

2026-06-04 完成 `docs/architecture/api-design.md` 接口设计文档后，Java 后端 Controller 与 FastAPI 路由均已实现文档中定义的所有端点，但前端侧存在明显缺口：缺少 API 模块函数、TypeScript 类型定义、页面 CRUD UI 和部分路由。

## 范围

以 `docs/architecture/api-design.md` 为契约，补齐前端以下层级：

- API 模块层：新增 feedback.ts + rag.ts，扩充 chat.ts / experiments.ts / knowledgeBases.ts
- TypeScript 类型层：补齐缺失的 11 个类型，扩展 4 个现有类型
- 客户端层：修复 client.ts 错误消息提取路径
- Store 层：修复 hydrate 容错、新增 chat sessions / experiments / feedback 完整 actions
- 页面层：ExperimentsPage CRUD UI、SettingsPage 可编辑、FeedbackPage 新建、ChatPage 会话管理
- 路由与导航层：新增 /feedback 路由、WorkbenchLayout 导航入口

## 输出

- 前端 5 个 API 模块补齐（chat / experiments / knowledgeBases / feedback / rag）
- 11 个新增 TypeScript 类型 + 4 个修复
- 1 个 Store 重写 + 14 个新增 actions
- 4 个页面新建/重写 + 1 个路由新增 + 1 个导航新增
- `docs/reviews/2026-06-05-frontend-api-completion-review-prompt.md`
- `docs/handoff/CURRENT_STATE.md` 更新
- `PROJECT_CONTEXT.md` 更新

## 非范围

- 不修改 Java 后端 Controller / Service / DTO
- 不修改 FastAPI 路由 / Schema / Service
- 不启动服务做 HTTP smoke
- 不新增后端接口
