# 前端模块

## 模块职责

`frontend/` 是本地知识库 Agent 的前端工作台，负责知识库管理、文档上传、聊天问答、引用来源展示、RAG 策略配置、评测集管理、实验对比、图谱事实查看、反馈和系统设置。

前端浏览器请求只进入 Spring Boot `/api/*`，不直接访问 FastAPI `/ai/*`。

## 当前状态

- 已完成 Vue 3 + TypeScript + Pinia + Vue Router + Vite 基础工程。
- 已完成 Coze Studio 风格浅色工作台：窄主导航、二级侧栏、紧凑面板、移动端单栏适配。
- 已覆盖 `/chat`、`/documents`、`/knowledge-base`、`/experiments`、`/experiments/comparison`、`/graph`、`/feedback`、`/settings`。
- 实验页已升级为评测集管理工具，支持样本创建、编辑、归档、删除、单样本评估和按 preset 批量评测。
- 对比页展示结构化指标：`Recall@K`、`Precision@K`、`MRR`、`Citation`、Tokens、Cost 和分阶段耗时。

## 技术栈

- Vue 3
- TypeScript
- Vite
- Pinia
- Vue Router

## 目录结构

```text
frontend/
├── src/
│   ├── api/              # 统一 API client
│   ├── components/       # 通用和业务组件
│   ├── layouts/          # 工作台布局壳
│   ├── pages/            # 页面级组件
│   ├── router/           # 路由
│   ├── stores/           # Pinia 状态
│   ├── types/            # TypeScript 类型
│   └── utils/            # 工具函数
├── scripts/
│   ├── dev.mjs
│   └── build.mjs
├── index.html
└── package.json
```

## 本地启动

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

## 常用命令

```powershell
npm.cmd run dev
npm.cmd run typecheck
npm.cmd run build
npm.cmd run preview
```

## 运行时配置

- `VITE_BACKEND_PROXY_TARGET`：开发代理目标，默认 `http://localhost:8080`。
- runtime settings 可配置 API base URL、默认知识库、请求超时和 trace header。
- `aiServiceBaseUrl` 只作为后端桥接诊断口径保留，页面组件不得绕过 Spring Boot 直连 FastAPI。

## 关键入口

- `src/main.ts`：应用入口。
- `src/layouts/WorkbenchLayout.vue`：全局工作台布局。
- `src/styles.css`：全局视觉 token、布局和通用样式。
- `src/api/`：所有后端接口调用入口。
- `src/stores/workbench.ts`：当前聚合状态入口。
- `src/pages/chat/ChatPage.vue`：聊天工作台。
- `src/pages/experiments/ExperimentsPage.vue`：评测集管理工具。
- `src/pages/experiments/ExperimentComparisonPage.vue`：实验指标对比页。

## 与其他模块关系

```text
Vue 页面
-> frontend/src/api/*
-> Spring Boot /api/*
-> FastAPI /ai/*
```

## 后续优化

- 拆分 `ChatPage.vue` 为会话列表、消息流、composer、source inspector 等组件。
- 拆分 `workbench` store，降低跨页面状态耦合。
- 为评测集导入导出、批次任务状态和失败重试补充更完整交互。
- 增加 Playwright 或截图级回归检查。
