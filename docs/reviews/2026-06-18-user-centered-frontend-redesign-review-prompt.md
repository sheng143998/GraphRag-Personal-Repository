# 用户路径导向前端重设计 Review Prompt

## 背景

本次改造聚焦 `frontend-react/`，按真实用户完成售后支持工作的路径重新设计主界面：

- `/chat`：售后支持问答工作台，突出问题处理、Agent supervisor 编排、证据核查、风险与升级建议。
- `/documents`：文档入库中心，突出上传后的入库流水线和失败复查。
- `/experiments`：测评实验工作台，突出测评集导入、人工审核、运行评测和指标回看。

## 审查重点

1. 前端浏览器请求是否仍只通过 Spring Boot `/api/*`，不能直接调用 FastAPI `/ai/*`。
2. `/chat` 是否保留已有会话、知识库选择、发送 assistant-turn、supportPlan 展示和 citations 展示能力。
3. `/documents` 是否保留单文件、多文件、文件夹上传、轮询、文档删除和详情抽屉能力。
4. `/experiments` 是否保留导入样本、页面内审核、单条/批量删除样本、删除实验、运行已通过样本能力。
5. 新增流程条、状态文案和空状态是否中文优先、无乱码、无英文主文案。
6. 响应式布局是否无明显遮挡、文本溢出、按钮挤压或卡片嵌套过度。
7. 类型安全：`AgentTraceMetadata`、`workflowSteps`、`traceAttributes` 映射是否兼容后端缺省字段。

## 已运行验证

- `npm.cmd --prefix frontend-react run typecheck`
- `npm.cmd --prefix frontend-react run build`
- Playwright + Edge 渲染 `/chat`、`/documents`、`/experiments`
- Playwright 点击 `/chat` 示例问题，确认输入框状态更新
- 架构扫描：`rg -n "localhost:8000|/ai/|ai-service|VITE_AI|http://127\\.0\\.0\\.1:8000" frontend-react/src`

## 已知观察

本地渲染时控制台存在 Spring Boot API `500` 和一个静态资源 / API `404`，页面未空白、无 Vite overlay。该问题属于当前本地后端数据或接口状态，非本次前端渲染改造新增的运行时崩溃。
