# React 前端工作台

`frontend-react/` 是当前项目的正式前端主入口，已替代旧 Vue `frontend/`。它面向企业售后技术支持知识库 Agent，提供文档入库、支持问答、RAG 评测、知识库管理、图谱事实、反馈和设置等工作台页面。

## 模块职责

- 浏览器端只调用 Spring Boot `/api/*`，不直接访问 FastAPI `/ai/*`。
- 提供售后支持问答工作台：会话、知识库选择、Agent supervisor 编排、证据引用、风险审查和工单升级建议。
- 提供文档入库中心：单文件、多文件、文件夹上传，展示已上传、解析中、切分中、向量化、可检索和失败复查。
- 提供评测实验工作台：测评集导入、页面内人工审核、批量运行、RAGAS / 检索指标回看、样本和实验删除。
- 提供知识库、GraphRAG 图谱事实、反馈和运行设置页面。

## 技术栈

- React 18
- TypeScript
- Vite
- React Router
- Zustand
- lucide-react
- Material Symbols 图标字体

## 常用命令

从仓库根目录执行：

```powershell
npm.cmd --prefix frontend-react run dev
npm.cmd --prefix frontend-react run typecheck
npm.cmd --prefix frontend-react run build
```

开发服务器默认监听 `127.0.0.1:3000`，并将 `/api` 代理到 `http://localhost:8080`。如果本机端口冲突，可覆盖：

```powershell
$env:VITE_DEV_HOST='127.0.0.1'
$env:VITE_DEV_PORT='3001'
npm.cmd --prefix frontend-react run dev
```

## 关键目录

```text
frontend-react/
├── scripts/                   # dev/build 包装脚本，显式设置 Vite root
├── src/api/                    # Spring Boot /api/* client
├── src/app/router.tsx          # React Router 配置
├── src/layouts/WorkbenchLayout.tsx
├── src/pages/                  # 页面入口
├── src/features/documents/     # 文档入库流水线
├── src/features/experiments/   # 测评集审核、批量评测和对比
├── src/components/             # primitives 和数据展示组件
└── src/styles/                 # token、工作台样式、实验页样式
```

## 主要页面

- `/chat`：售后支持问答工作台，展示 Agent supervisor 编排、诊断方案、证据引用、风险和升级建议。
- `/documents`：文档入库中心，支持上传、轮询状态、失败复查和 chunk 预览。
- `/experiments`：测评集导入、人工审核、批量运行和评估历史。
- `/experiments/comparison`：按策略聚合对比 Recall、Precision、MRR、Citation、Tokens、Cost 和 latency。
- `/knowledge-base`：知识库列表、统计、创建和删除。
- `/graph`：GraphRAG 图谱事实查询和可视化。
- `/feedback`、`/settings`：反馈提交和运行时设置。

## 验证记录

当前主前端已通过：

```powershell
npm.cmd --prefix frontend-react run typecheck
npm.cmd --prefix frontend-react run build
```

最近一次 Playwright + Edge 渲染检查覆盖 `/chat`、`/documents`、`/experiments`，页面非空、无 Vite overlay；本地控制台中的 API 500/404 属于后端数据或接口状态，不是前端构建错误。

## 开发约定

- 新页面和新 API client 均放在 `frontend-react/src/`。
- 组件不得绕过 `src/api/` 直接拼接后端 URL。
- 中文内容按 UTF-8 读取和保存；Windows PowerShell 查看中文文件必须显式 `-Encoding UTF8`。
- 前端视觉以“工业级售后支持中枢”为方向：中文优先、密度适中、冷灰 / 深青 / 告警色，避免营销页和装饰性渐变。
