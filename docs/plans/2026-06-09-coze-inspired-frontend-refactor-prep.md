# 2026-06-09 Coze 风格参考前端大重构准备

## 目标

为前端大重构做准备，参考 Coze 会话类产品的信息架构、工作台密度和交互节奏，重新规划本项目 Vue 3 前端体验。重构目标不是复刻 Coze 的代码、品牌资产或私有交互，而是吸收其会话工作台的产品模式，重新设计适合本地知识库 Agent / Advanced RAG 的界面。

## 当前结论

- Figma 插件包已安装，`figma-use` 等 skill 可读取；但当前 Codex 线程没有暴露 `use_figma`、`get_screenshot`、`get_metadata`、`create_new_file` 等实际 Figma MCP 工具，因此现在不能直接创建或更新 Figma 文件。
- 当前系统能看到 Edge 默认用户数据目录和正在运行的 Edge 进程，但没有打开 `--remote-debugging-port`，无法附着到现有 Edge 会话。
- Edge 可执行文件位于 `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`。
- 不建议使用真实 Edge 登录态对 Coze 登录会话页做 DOM / CSS / 网络层批量采集；只允许做最小化、脱敏、测试账号优先的视觉与布局观察。
- 已按用户要求启动多 agent：一个 agent 负责前端代码库现状梳理，一个 agent 负责参考站点采集合规与技术可行性评估，均使用 `gpt-5.5` 与 `xhigh` reasoning。

## 允许参考的内容

- 页面区域结构：侧边栏、会话列表、主对话区、输入区、工具栏、辅助面板。
- 响应式布局：桌面多栏、窄屏折叠、会话和设置入口的优先级。
- 设计 token 级信息：颜色层级、字号、间距、边框、圆角、阴影和状态反馈。
- 抽象交互流程：创建会话、切换会话、发送消息、查看来源、配置策略、继续追问。
- 自行重绘的线框图、组件清单、布局说明和脱敏截图。

## 禁止事项

- 不抓取、导出或复用 Coze 的前端源码、JS bundle 还原结果、接口协议、私有素材、品牌图标或专有文案。
- 不读取、保存或转储 cookie、token、localStorage、sessionStorage、IndexedDB、请求头、HAR 或接口响应体。
- 不绕过登录、验证码、风控、权限或反自动化限制。
- 不采集真实账号下的私有会话内容、文件、知识库、工作区数据或 AI 输出。
- 不让 Vue 前端绕过 Spring Boot 直接请求 FastAPI；浏览器请求继续统一进入 `/api/*`。

## 前端现状

- 技术栈：Vue 3、TypeScript、Vite、Vue Router、Pinia。
- 路由入口：`/chat`、`/documents`、`/knowledge-base`、`/experiments`、`/experiments/comparison`、`/feedback`、`/graph`、`/settings`。
- 当前全局 shell 在 `frontend/src/layouts/WorkbenchLayout.vue`，采用固定左侧导航 + 顶部标题栏 + 页面内容区。
- 当前样式集中在 `frontend/src/styles.css`，偏玻璃态、渐变和卡片式信息面板；后续需要向更清爽、更高密度、更会话中心的工作台风格收敛。
- 当前聊天页 `frontend/src/pages/chat/ChatPage.vue` 功能密集，包含会话管理、总览、上传入口、问答、学习计划、复习卡片、薄弱点、策略选择和来源列表，适合作为第一阶段重构重点。
- 当前 `frontend/src/stores/workbench.ts` 承载知识库、文档、聊天、实验、反馈、设置、trace 和薄弱点等多数状态，后续需要分域拆分，避免 UI 重构时误伤业务副作用。
- `frontend/src/pages/experiments/ExperimentsPage.vue` 也属于高复杂度页面，应排在聊天工作台之后分阶段处理。
- `frontend/src/pages/graph/GraphPage.vue` 存在直接 API 调用模式，后续需要和其他页面的 store 编排模式统一。
- `frontend/src/pages/settings/SettingsPage.vue` 暴露 `aiServiceBaseUrl`，需在重构中明确其只作后端配置展示或移除，避免前端直连 FastAPI。
- `frontend/src/api/chat.ts` 仍保留 legacy `sendChatMessage('/rag/query')`，主链路已走 assistant-turn；重构前需要明确保留、迁移或删除策略。
- 前端 README 仍提到 `vite.config.ts`，但实际 Vite 配置在 `frontend/scripts/dev.mjs` 与 `frontend/scripts/build.mjs` 内联维护，存在文档漂移。

## 建议重构方向

1. 信息架构重排
   - 将 `/chat` 作为主工作台，形成三栏结构：会话 / 知识库上下文、主对话流、检索与学习辅助侧栏。
   - 将上传、策略、来源、学习计划、薄弱点做成可收起的工具面板，避免主聊天路径被大量表单打断。

2. 视觉系统重建
   - 建立 `design-tokens.css` 或等价 token 分层：颜色、间距、字体、圆角、阴影、状态色。
   - 减少大面积渐变、玻璃态和装饰粒子，转为更克制、扫描效率更高的工作台 UI。
   - 保持卡片半径不超过 8px，强调清晰边界、紧凑列表和稳定工具栏。

3. 组件拆分
   - 从 `ChatPage.vue` 拆出会话列表、消息流、Composer、引用来源、策略面板、学习面板和弱点练习模块。
   - 保持 API 调用仍集中在 `frontend/src/api/*` 与 Pinia store，不在组件中散落请求逻辑。
   - 把 citation parsing、assistant-turn response mapping、trace 解析等 adapter 逻辑从大 store / 页面中逐步抽离，便于测试。

4. 交互补齐
   - 输入区支持明确发送状态、停止 / 重试入口、追问建议、策略标识和 trace id。
   - 来源、trace、GraphRAG 元数据和评估指标以侧栏 tabs 展示。
   - 空状态、错误态、加载态、长文本溢出、移动端折叠都要覆盖。

5. 验证与迭代
   - 每轮重构后运行 `npm.cmd --prefix frontend run typecheck` 与 `npm.cmd --prefix frontend run build`。
   - 启动 Vite 预览，用 Playwright 或浏览器截图检查桌面与移动端布局。
   - 如果 Figma MCP 工具恢复可用，先把 token 和主工作台线框同步到 Figma，再按 Figma 反馈迭代实现。
   - 首轮准备已验证当前基线：`npm.cmd --prefix frontend run typecheck` 与 `npm.cmd --prefix frontend run build` 均通过。

## 多 agent 分工建议

- 主 agent：维护整体架构、最终集成、验证和文档。
- 代码库 explorer：梳理现有前端页面、状态和样式依赖，给出重构风险。
- 参考采集 explorer：只输出脱敏视觉与布局观察，不抓源码和私有数据。
- 后续 worker A：负责全局 shell、导航、token 和基础组件。
- 后续 worker B：负责聊天主工作台、消息流和输入区。
- 后续 worker C：负责右侧 RAG / GraphRAG / 学习辅助面板。

## 下一步

1. 等待前端代码库 explorer 的结构报告。
2. 若需要 Figma 介入，先修复或重新连接 Figma MCP 工具；否则先用本地代码和脱敏截图完成第一版线框。
3. 创建第一阶段实施计划：`chat-workbench-layout-refactor`。
4. 在不改变接口契约的前提下，先重构 `ChatPage.vue` 及其依赖组件，再逐步扩展到其他页面。
