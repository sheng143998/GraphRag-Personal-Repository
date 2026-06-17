# React 前端迁移工作区

`frontend-react/` 是基于 Stitch RAG Knowledge Studio 页面新建的 React + TypeScript 前端迁移工作区。当前用于并行验证 React 版工作台，暂不替换现有 Vue `frontend/`。

## 模块职责

- 按 Stitch `Lumina Nexus` 设计系统实现浅色高密度 RAG Workbench。
- 覆盖对话、文档中心、知识库、实验评估、评估对比、图谱事实、反馈和设置页面。
- 前端浏览器请求继续只进入 Spring Boot `/api/*`，不直接调用 FastAPI `/ai/*`。

## 技术栈

- React 18
- TypeScript
- Vite
- React Router
- Zustand
- lucide-react

## 常用命令

```powershell
npm.cmd --prefix frontend-react run dev
npm.cmd --prefix frontend-react run typecheck
npm.cmd --prefix frontend-react run build
```

开发服务器默认使用 `5174` 端口，并将 `/api` 代理到 `http://localhost:8080`。

## 关键目录

```text
frontend-react/
├── src/api/                    # Spring Boot /api/* client
├── src/app/router.tsx          # React Router 配置
├── src/layouts/WorkbenchLayout.tsx
├── src/pages/                  # 页面入口
├── src/features/documents/     # 文档中心：上传、状态轮询、详情预览
├── src/features/experiments/   # 实验评估：测评集导入、自动 batch run、对比
├── src/components/             # primitives 和数据展示组件
└── src/styles/                 # token、工作台样式、实验页样式
```

## 当前已实现能力

- `/documents`：单文件、多文件、文件夹上传，保留 `relativePath`，上传后轮询文档状态，展示文档表格和 chunk 预览抽屉。
- `/experiments`：读取本地 JSON / CSV 测评集，导入到当前实验，导入后自动触发 batch RAG run。
- `/experiments/comparison`：按最近评估记录聚合 Recall、Precision、MRR、Citation、Tokens、Cost 和 latency。
- `/chat`：会话列表、assistant-turn 调用、消息流和引用侧栏第一版。
- `/knowledge-base`：知识库列表、统计、创建和删除第一版。
- `/graph`：基于 graph facts 的确定性 SVG 图谱和实体详情第一版。
- `/feedback`、`/settings`：反馈提交和运行时设置第一版。

## 验证记录

本轮已通过：

```powershell
npm.cmd --prefix frontend-react run typecheck
npm.cmd --prefix frontend-react run build
```

审查 agent 发现的“导入评测集后自动运行可能读取旧 state 导致跳过 batch run”已修复：导入后现在直接拉取最新 evaluation cases，再计算本次导入成功的 case ids。

## 后续待办

- 做真实后端联调和浏览器视觉 smoke。
- 对齐 Stitch 截图逐页做视觉差异修正。
- 验收后决定是否将 `frontend-react/` 收敛为正式 `frontend/`。
