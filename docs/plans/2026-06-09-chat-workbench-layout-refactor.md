# 2026-06-09 Coze 工作台风格前端重构

## 目标

在不改变后端接口契约的前提下，参考 Coze Studio 的浅色 IDE / 工作台信息架构，重构本项目前端整体视觉与布局。重点是把全局 shell、导航、页面容器、列表、表单、指标和 `/chat` 三栏工作台统一成更接近 Coze 的紧凑产品界面：窄全局导航、子导航、56px 顶栏、白色面板、细边框、浅背景、稳定滚动区。

## 边界

- 前端继续只调用 Spring Boot `/api/*`，不直接访问 FastAPI。
- 不抓取、复用或还原 Coze 前端源码、接口、私有素材、品牌资产或登录态数据。
- Figma 插件当前状态仅做诊断：插件包与配置存在，但本线程没有暴露实际 MCP 工具，因此本轮不写入 Figma 文件。
- 本轮聚焦 `frontend/src/layouts/WorkbenchLayout.vue`、`frontend/src/styles.css`、公共组件和现有页面模板，暂不拆分 Pinia store，避免把 UI 重构和状态重构混在一起。

## 设计方向

- 全局 shell 改为 Coze 式全屏 IDE 布局：
  - 64px 左侧全局导航，承载产品标识、一级模块入口和辅助入口。
  - 236px 子导航，承载当前工作区、页面列表、运行摘要与接口边界提示。
  - 56px 顶栏，展示当前页面标题、trace、策略和运行状态。
  - 主内容区使用浅灰背景与白色工作台面板，不再使用暗色玻璃侧栏和大面积渐变。
- 将聊天页重排为 `coze-workbench` 三栏布局：
  - 左栏：新建会话、会话列表、知识库 / 文档 / 策略概览。
  - 中栏：消息流、追问建议、固定底部输入 composer。
  - 右栏：来源引用、策略、学习计划、复习卡片、薄弱点练习。
- 视觉系统从玻璃态大卡片转向更克制的白色工作台：浅背景、细边框、紧凑间距、8px 圆角、明确状态色。
- 普通管理页保持现有功能流，但统一为 Coze 风格的表单面板、列表卡片、指标条、筛选条和表格。
- 保留现有 store action 和 API mapper，降低行为回归风险。
- 移除聊天页中的大块概览卡片对主链路的打断，让“发问 -> 回答 -> 引用 / 复习”更顺。

## 验证

- 已通过：`npm.cmd --prefix frontend run typecheck`
- 已通过：`npm.cmd --prefix frontend run build`
- 已启动 dist preview：`npm.cmd --prefix frontend run preview -- --host 127.0.0.1 --port 4173`
- 已用 Edge headless 截图检查：
  - `http://127.0.0.1:4173/chat` 桌面三栏工作台
  - `http://127.0.0.1:4173/chat` 移动端单栏堆叠
  - `http://127.0.0.1:4173/documents` 文档工作台
  - `http://127.0.0.1:4173/experiments` 实验工作台
  - `http://127.0.0.1:4173/graph` 图谱三栏工作台
  - `http://127.0.0.1:4173/settings` 设置两栏工作台
- 已检查前端边界：`frontend/src` 未发现页面直接调用 `/ai/*`；浏览器请求仍通过统一 API client 进入 `/api/*`。

## 风险

- `ChatPage.vue` 当前承担多个 workflow，模板重排可能遗漏条件渲染状态。
- 右侧薄弱点练习包含较多表单和动作按钮，需要确保移动端不会溢出。
- 全局样式复用较广，新增样式尽量使用新 class 前缀，避免影响其他页面。

## 实施摘要

- `frontend/src/layouts/WorkbenchLayout.vue` 改为 Coze 式窄主导航、二级导航、56px 顶栏和工作台内容区。
- `frontend/src/styles.css` 重建浅色 token、面板、表单、列表、状态、聊天三栏、移动端单栏和滚动条样式。
- `frontend/src/pages/chat/ChatPage.vue` 使用三栏 Coze 工作台布局，保留现有 Pinia action 与 API 契约。
- `frontend/src/pages/documents/KnowledgeBase/Graph/Feedback/Settings` 等页面复用两栏 / 三栏工作台布局和浅色资源列表样式。
- `frontend/src/pages/settings/SettingsPage.vue` 将 AI 服务地址文案收口为 Spring Boot 桥接诊断语义，避免前端直连 FastAPI 的误导。
