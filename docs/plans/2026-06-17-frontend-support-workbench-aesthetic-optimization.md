# 2026-06-17 frontend-react 售后支持工作台美学与中文化优化

## 背景

本阶段在 RAGAS 评估体系和企业售后技术支持 Agent 编排完成后，继续把 `frontend-react/` 从通用 RAG Studio 调整为企业售后技术支持知识库 Agent 工作台。目标是中文优先、业务高密度、专业耐看，并让前端承接后端已经透传的结构化 `supportPlan`。

## 设计方向

- 工作台定位：企业售后技术支持、知识库检索、证据核查、诊断建议和升级判断。
- 视觉方向：冷灰底、深青主色、告警橙/红只用于风险提示；减少旧紫色模板感。
- 信息架构：不做营销页，保留三栏工作台密度，让会话、回答、证据追踪同屏可见。
- 文案原则：主界面尽量中文化；保留 RAG、MRR、topK、JSON、文件扩展名等必要技术名词。

## 主要改动

- `ChatPage` 新增知识库选择、售后模式变量、示例问题和结构化售后诊断方案卡片。
- `api/chat.ts` 和 `types/index.ts` 增加 `agentName`、`variables` 与 `supportPlan` 类型/映射，避免后端返回的诊断结构在前端丢失。
- 全局导航、路由 subtitle、文档中心、评测页、图谱页、设置页继续中文化，减少可见英文标签。
- `tokens.css` 收敛字体与色彩 token，去掉重复 `--primary-fixed` 和旧紫色主色。
- `chat-page.css` 新增售后诊断卡片、风险/升级区、移动端适配和更稳的三栏布局。
- `scripts/dev.mjs` 与 `scripts/build.mjs` 显式设置 Vite root，避免从仓库根目录用 `npm --prefix frontend-react run dev` 启动时入口路径不稳定。

## 验证

- `npm.cmd --prefix frontend-react run typecheck`
- `npm.cmd --prefix frontend-react run build`
- Playwright via system Edge：
  - `/chat` 桌面首屏非空。
  - 点击“接口 502 排查”示例并发送后，渲染 `售后诊断方案`、澄清问题、诊断步骤、风险提示和证据侧栏。
  - `/documents` 桌面渲染资料入库、状态表和文档状态。
  - `/chat` 移动端首屏渲染。
  - 审查反馈后补测：1280px 宽度隐藏右侧证据栏避免中间区挤压；390px 移动端显示知识库选择和新建会话入口。
  - 控制台仅有 React Router v7 future flag warning，无业务错误。

## 已知限制

- 历史会话重新加载时，`supportPlan` 目前只在本轮 assistant-turn 响应内展示；若需要长期回看诊断结构，需要后端将 `supportPlan` 持久化到消息扩展字段或 trace 可回查字段。
- Playwright 使用 stub 后端验证渲染和交互，不依赖本地 Spring Boot / FastAPI 真实服务状态。
