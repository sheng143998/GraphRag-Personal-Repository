# React + TypeScript 前端重构计划：基于 Stitch RAG Knowledge Studio

日期：2026-06-16  
状态：计划待确认，暂不实施代码改造  
目标目录：先并行建设 React 版前端，验收后再替换当前 Vue 前端入口

## 1. 背景与目标

当前项目的前端位于 `frontend/`，技术栈是 Vue 3 + TypeScript + Vite + Pinia + Vue Router，已经覆盖对话、文档、知识库、实验评估、图谱、反馈和设置等页面。用户提供的 Stitch 页面位于：

```text
C:/Users/admin/Downloads/stitch_rag_knowledge_studio/stitch_rag_knowledge_studio
```

本轮目标是按照 Stitch 生成的 RAG Knowledge Studio 页面，重构为 React + TypeScript 前端。重构不是只换样式，而是把现有 Vue 工作台迁移为 React 组件体系，同时保持现有业务能力不倒退：

- 前端仍只调用 Spring Boot `/api/*`，不直接调用 FastAPI `/ai/*`。
- 保留已有文档上传能力，包括单篇、多篇和文件夹上传。
- 保留实验页面导入测评集后自动跑 RAG 全链路的能力。
- 保留聊天会话、RAG 引用、GraphRAG 图谱事实、反馈和设置入口。
- 视觉上以 Stitch 的 `Lumina Nexus` 工作台设计系统为准。

## 2. 输入材料

### 2.1 Stitch 页面

| Stitch 页面 | 建议落地路由 | 用途 |
| --- | --- | --- |
| `rag_chat_rag_qa` | `/chat` | 三栏 RAG 对话工作台：会话列表、问答区、引用 / trace 侧栏 |
| `document_management` | `/documents` | 文档上传、批量上传、文件夹上传、解析状态和文档列表 |
| `knowledge_base_management` | `/knowledge-base` | 知识库列表、统计卡片、创建 / 更新 / 删除入口 |
| `experiment_evaluation` | `/experiments`、`/experiments/comparison` | 评测集导入、自动运行、批量评估、指标看板 |
| `knowledge_graph_explorer` | `/graph` | 全屏图谱画布、实体详情右侧栏、缩放 / 布局工具 |
| `kb_graph` | `/knowledge-base` 或 `/graph` 的增强参考 | 知识库与图谱混合视图，可作为后续二阶段增强 |
| `lumina_nexus/DESIGN.md` | 全局设计系统 | 颜色、字体、间距、组件规则 |

### 2.2 当前 Vue 前端能力

现有路由：

- `/chat`
- `/documents`
- `/knowledge-base`
- `/experiments`
- `/experiments/comparison`
- `/feedback`
- `/graph`
- `/settings`

现有 API client 文件：

- `frontend/src/api/chat.ts`
- `frontend/src/api/documents.ts`
- `frontend/src/api/experiments.ts`
- `frontend/src/api/feedback.ts`
- `frontend/src/api/graph.ts`
- `frontend/src/api/knowledgeBases.ts`
- `frontend/src/api/rag.ts`
- `frontend/src/api/settings.ts`
- `frontend/src/api/client.ts`

迁移时优先复用这些 API 契约和 TypeScript 类型，降低重写风险。

## 3. 总体方案

推荐采用“并行 React 版 + 验收后替换”的保守路线。

第一阶段不直接删除 Vue 代码，而是在仓库中新增 React 版前端工作区，例如：

```text
frontend-react/
├── package.json
├── vite.config.ts
├── index.html
└── src/
    ├── app/
    ├── api/
    ├── components/
    ├── features/
    ├── layouts/
    ├── pages/
    ├── styles/
    ├── types/
    └── utils/
```

这样做的好处：

- Vue 版仍可作为功能对照和回退方案。
- React 页面可以逐页对齐 Stitch，不影响当前可用前端。
- 实验页和上传页这种复杂交互可以独立验收，避免一次性替换导致功能断裂。
- 通过验收后，再决定把 `frontend-react/` 重命名为 `frontend/`，或直接替换 `frontend/` 的 Vue 依赖和入口。

最终交付目标仍是项目只有一个正式前端入口，避免长期维护两套前端。

## 4. 技术栈选择

推荐 React 版使用：

| 类型 | 推荐 |
| --- | --- |
| 构建工具 | Vite |
| UI 框架 | React 18 + TypeScript |
| 路由 | React Router |
| 状态管理 | Zustand，按功能域拆分 store |
| 数据请求 | 先复用现有 `fetch` API client，不额外引入重型请求层 |
| 图标 | `lucide-react` 或 Material Symbols 字体二选一，优先保持 Stitch 图标语义 |
| 样式 | 全局 CSS tokens + CSS Modules 或普通 CSS 文件 |
| 图谱 | 第一版用 SVG / DOM 实现现有能力，后续再评估 React Flow / D3 |
| 测试 | TypeScript typecheck、Vite build、浏览器 smoke、关键 workflow 手测 |

暂不建议第一版引入复杂 UI 组件库。Stitch 的设计系统已经明确，直接建立轻量组件库更容易保持一致性。

## 5. 设计系统落地

从 `lumina_nexus/DESIGN.md` 抽取全局 token，写入 React 版 `src/styles/tokens.css`：

### 5.1 颜色

核心色：

- 背景：`#f7f9fb`
- 主内容面：`#ffffff`
- 低层容器：`#f2f4f6`
- 主文本：`#191c1e`
- 次文本：`#464555`
- 主色：`#3525cd`
- 主色容器：`#4f46e5`
- 边框：`#c7c4d8`
- 错误色：`#ba1a1a`

要求：

- 保持浅色 IDE / workbench 风格。
- 不做营销页式大 hero。
- 不使用大面积渐变、装饰性光斑或过度阴影。
- 所有页面优先通过边框、背景层级和紧凑间距建立结构。

### 5.2 字体

- 标题：Hanken Grotesk
- 正文：Inter
- 代码、ID、文件路径、chunkId、traceId：JetBrains Mono

第一版可以通过 Google Fonts 引入；如本地网络不稳定，保留系统 fallback。

### 5.3 组件形态

基础规范：

- 左侧主导航宽度：`240px`
- 顶栏高度：`48px`
- 页面最大内容宽度：管理页 `1200px`，图谱页可放宽到 `1400px` 或全屏
- 卡片 / 面板圆角：6px 到 8px
- 表格行高：不超过 48px
- 状态标识：8px 小圆点 + 文案，`PROCESSING` 可轻量 pulse
- 弹窗 / popover 才使用弱阴影，普通面板只用 1px border

## 6. React 目录与模块规划

建议目录：

```text
frontend-react/src/
├── app/
│   ├── App.tsx
│   ├── router.tsx
│   └── providers.tsx
├── api/
│   ├── client.ts
│   ├── chat.ts
│   ├── documents.ts
│   ├── experiments.ts
│   ├── feedback.ts
│   ├── graph.ts
│   ├── knowledgeBases.ts
│   ├── rag.ts
│   └── settings.ts
├── components/
│   ├── primitives/
│   ├── layout/
│   ├── data-display/
│   ├── forms/
│   └── feedback/
├── features/
│   ├── chat/
│   ├── documents/
│   ├── experiments/
│   ├── graph/
│   ├── knowledge-base/
│   ├── feedback/
│   └── settings/
├── layouts/
│   └── WorkbenchLayout.tsx
├── pages/
│   ├── ChatPage.tsx
│   ├── DocumentsPage.tsx
│   ├── KnowledgeBasePage.tsx
│   ├── ExperimentsPage.tsx
│   ├── ExperimentComparisonPage.tsx
│   ├── GraphPage.tsx
│   ├── FeedbackPage.tsx
│   └── SettingsPage.tsx
├── stores/
├── styles/
├── types/
└── utils/
```

## 7. 组件拆分计划

### 7.1 全局组件

- `WorkbenchLayout`：左侧导航、顶栏、主内容区域。
- `SideNav`：路由导航，保持 Stitch 的 active state。
- `TopBar`：标题、上下文、搜索、帮助 / 通知按钮。
- `Button`：primary、secondary、ghost、danger、icon variants。
- `Input` / `Select` / `Textarea`：统一 focus、错误态和 disabled 态。
- `Panel`：普通工作台面板，不允许无意义嵌套卡片。
- `StatusBadge`：文档状态、实验状态、RAG run 状态。
- `MetricCard`：评估指标和知识库统计。
- `DataTable`：紧凑表格头、行、空状态。
- `EmptyState`：仅在列表为空时使用，文案简短。

### 7.2 业务组件

聊天：

- `SessionList`
- `ChatTranscript`
- `ChatComposer`
- `CitationList`
- `TracePanel`
- `WeakPointPanel`
- `StrategySelector`

文档：

- `UploadDropzone`
- `BatchUploadPanel`
- `FolderUploadInput`
- `DocumentStatusList`
- `DocumentDetailDrawer`
- `ChunkPreviewList`

实验：

- `ExperimentList`
- `EvaluationCaseImportDialog`
- `EvaluationCaseTable`
- `AutoRunToolbar`
- `BatchEvaluationProgress`
- `MetricLeaderboard`
- `EvaluationHistoryTable`
- `RunDetailPanel`

知识库：

- `KnowledgeBaseGrid`
- `KnowledgeBaseCard`
- `KnowledgeBaseFormDialog`
- `KnowledgeBaseStatsBar`

图谱：

- `GraphCanvas`
- `GraphToolbar`
- `GraphLegend`
- `EntityDetailPanel`
- `RelationshipList`

## 8. 状态管理迁移

当前 Pinia `workbench.ts` 聚合了太多职责。React 迁移时拆成多个 store / hooks：

| Vue Pinia 状态 | React 建议 |
| --- | --- |
| knowledgeBases | `useKnowledgeBaseStore` |
| documents、uploadPending、pollDocumentStatus | `useDocumentStore` |
| chatSessions、messages、askQuestion | `useChatStore` |
| experiments、ragRuns、evaluationSummary | `useExperimentStore` |
| graph facts | `useGraphStore` |
| settings | `useSettingsStore` |
| lastError、toast | `useUiStore` |

关键要求：

- 文档解析轮询必须在组件卸载时清理 timer。
- 上传、自动评估、批量评估都要有明确 pending / progress / failed 状态。
- 不把临时输入框状态都塞进全局 store，表单状态优先留在组件内。
- 评测集导入后自动跑 RAG 的状态流必须保留：选择文件 -> 解析 JSON -> 按当前实验导入 -> 调用批量运行接口 -> 刷新评估结果。

## 9. API 迁移策略

第一优先级是直接迁移并复用现有 API 契约：

- `ApiEnvelope<T>` 结构保持不变。
- `X-Trace-Id` 继续由 client 层统一透传。
- 错误提取继续兼容 Spring Boot `{ error: { code, message } }`。
- 所有浏览器请求仍以 Spring Boot `/api/*` 为边界。
- 不在 React 页面中散落 `fetch`，页面只调用 `src/api/` 和功能 store。

重点保留接口能力：

- `POST /api/documents/upload`
- `POST /api/documents/upload/batch`
- `GET /api/documents`
- `GET /api/documents/{id}`
- `POST /api/chat/sessions`
- `GET /api/chat/sessions`
- `POST /api/chat/sessions/{sessionId}/assistant-turn`
- `GET /api/rag/evaluation-cases`
- `POST /api/rag/evaluation-cases/import`
- `POST /api/rag/evaluation-cases/run-batch`
- `GET /api/rag/runs`
- `GET /api/graph/facts`

具体接口路径以当前 `frontend/src/api/*.ts` 为准，React 迁移时先复制类型和 client，再逐步整理命名。

## 10. 页面实施阶段

### 阶段 0：计划确认与基线锁定

输出：

- 本计划文档。
- Stitch 页面与当前 Vue 路由/API 的映射确认。
- 明确是否采用 `frontend-react/` 并行目录。

验收：

- 用户确认可以进入 React 实施。

### 阶段 1：React 工程骨架

工作：

- 新建 React + TS + Vite 工程。
- 配置 `vite.config.ts` 的 `/api` 代理，保持 Spring Boot 边界。
- 添加 React Router。
- 建立全局 token、reset、字体和基础布局。
- 迁移现有 `types` 和 `api`。

验收：

- `/chat`、`/documents`、`/knowledge-base`、`/experiments`、`/graph`、`/feedback`、`/settings` 可路由访问。
- `npm run typecheck` 和 `npm run build` 通过。

### 阶段 2：Workbench Shell 与设计系统

工作：

- 实现 `WorkbenchLayout`、`SideNav`、`TopBar`。
- 实现按钮、输入框、面板、状态标识、表格、指标卡片等 primitives。
- 对齐 Stitch 的 240px 侧栏、48px 顶栏、浅色高密度布局。

验收：

- 所有页面共享同一套 shell。
- active navigation 和 hover / focus 状态可用。
- 桌面与窄屏下不出现主内容遮挡或文字溢出。

### 阶段 3：文档中心

优先实现，因为用户刚完成上传链路升级，风险最高。

工作：

- 按 `document_management` 重建 `/documents`。
- 支持单篇、多篇、文件夹上传。
- 文件夹上传继续保留 `relativePath` / `webkitRelativePath`。
- 上传后展示 `PROCESSING`，并轮询到 `INDEXED` / `FAILED`。
- 文档表格支持状态、文档类型、知识库、chunk 数、更新时间。
- 文档详情显示 chunks preview、metadata、sourcePath。

验收：

- 单文件上传可用。
- 多文件上传可用。
- 文件夹上传可用。
- 上传后状态自动刷新。
- 失败状态有明确提示。

### 阶段 4：实验评估

工作：

- 按 `experiment_evaluation` 重建 `/experiments`。
- 修复并保留“选择本地 JSON 后导入到当前实验”按钮可用逻辑。
- 支持上传评测集后自动跑一次 RAG 全链路。
- 展示 batch run 进度、成功 / 失败数量、每条 case 的 runId / evaluationId。
- `/experiments/comparison` 展示策略聚合指标、token、cost、latency。

验收：

- 选择测评集 JSON 后按钮可点击。
- 导入后自动触发批量 RAG run。
- 页面能刷新显示评估结果。
- 失败样例能展示错误信息，不阻断其他样例。

### 阶段 5：聊天工作台

工作：

- 按 `rag_chat_rag_qa` 重建 `/chat`。
- 左侧会话列表，中间消息流，右侧引用 / trace / 学习辅助面板。
- 支持策略选择、hybrid preset、提问 pending、引用来源显示。
- 保留 weak points、review cards、follow-up questions 展示。

验收：

- 新建会话可用。
- 发送问题后能保存 user / assistant message。
- 引用来源、traceId、策略名称展示正确。
- 会话切换后历史消息可恢复。

### 阶段 6：知识库管理

工作：

- 按 `knowledge_base_management` 重建 `/knowledge-base`。
- 展示知识库卡片、文档数、chunk 数、更新时间。
- 支持创建、更新、删除知识库。
- `kb_graph` 中“知识库 + 图谱联动”的视图先作为二阶段增强，不阻塞第一版迁移。

验收：

- 知识库 CRUD 可用。
- 默认知识库为空时有可理解提示。
- 删除默认知识库后设置能回退到可用知识库。

### 阶段 7：GraphRAG 图谱

工作：

- 按 `knowledge_graph_explorer` 重建 `/graph`。
- 第一版使用现有 graph facts 接口展示实体 / 关系。
- 实现画布缩放、适应屏幕、实体选择、详情右侧栏。
- 如果现有数据不足以生成稳定布局，先实现确定性 SVG / DOM layout，后续再接 D3 / React Flow。

验收：

- 能按知识库加载实体和关系。
- 点击实体能看到名称、类型、别名、metadata、关联关系。
- 空图谱有明确空状态。

### 阶段 8：反馈与设置

Stitch 未单独提供反馈和设置页面，需要沿用现有功能并套入设计系统。

工作：

- `/feedback`：提交回答质量反馈，选择 run / session / message、评分、类型和评论。
- `/settings`：API base URL、默认知识库、超时、trace header 开关。
- 设置继续写入 localStorage，避免影响后端配置。

验收：

- 反馈提交成功后有明确成功状态。
- 设置保存后刷新页面仍能恢复。
- 不展示或鼓励前端直连 FastAPI `/ai/*`。

### 阶段 9：替换 Vue 入口

只有在 React 版全部验收后执行。

可选路线：

1. 将 `frontend-react/` 替换为正式 `frontend/`。
2. 或把当前 `frontend/` 内 Vue 依赖和入口改为 React，保留目录名不变。

推荐最终保持 `frontend/` 作为唯一正式前端目录，避免后续文档、脚本和 Docker 配置分裂。

## 11. 验证计划

每个阶段至少执行：

```powershell
npm.cmd --prefix frontend-react run typecheck
npm.cmd --prefix frontend-react run build
```

如果最终替换到 `frontend/`：

```powershell
npm.cmd --prefix frontend run typecheck
npm.cmd --prefix frontend run build
```

浏览器 smoke 验证：

- `/chat`：加载会话、提问、查看引用。
- `/documents`：单篇上传、多篇上传、文件夹上传、状态轮询。
- `/experiments`：导入评测集、自动 batch run、查看评估结果。
- `/experiments/comparison`：查看策略指标对比。
- `/knowledge-base`：创建 / 编辑 / 删除知识库。
- `/graph`：加载实体关系、点击实体详情。
- `/feedback`：提交反馈。
- `/settings`：保存并刷新设置。

视觉验证：

- 对比 Stitch `screen.png` 与浏览器截图。
- 桌面宽屏、普通笔记本宽度和移动宽度各检查一次。
- 检查按钮文字、表格列、上传区域、聊天输入框、图谱右侧栏是否溢出。

## 12. 风险与处理

| 风险 | 影响 | 处理 |
| --- | --- | --- |
| 一次性 Vue -> React 重写范围大 | 容易丢功能 | 使用 `frontend-react/` 并行实现，逐页验收 |
| 实验页流程复杂 | 自动运行和导入按钮容易回归 | 优先迁移实验 API 和状态机，单独 smoke |
| 文档上传涉及文件夹路径 | 浏览器兼容和 FormData 字段容易出错 | 保留现有 `BatchUploadPayload` 语义，重点测试 `relativePath` |
| Stitch 是静态 HTML | 需要转成真实数据驱动组件 | 先抽组件和 token，再接真实 API |
| 图谱布局当前可能较弱 | 视觉与交互难完全一致 | 第一版确定性 SVG 布局，二阶段评估 D3 / React Flow |
| 两套前端短期共存 | 文档和启动命令可能混乱 | README 明确 React 版是迁移目标，验收后收敛为一个正式入口 |

## 13. 不在第一版范围内

- 不改 Spring Boot / FastAPI 接口职责边界。
- 不重写 RAG、GraphRAG、evaluator 后端逻辑。
- 不新增 Kafka / RabbitMQ / Celery 解析链路能力。
- 不做暗色主题，除非后续明确需要。
- 不做大型动画或营销型首页。
- 不引入复杂设计系统库替代 Stitch token。

## 14. 下一步建议

确认本计划后，建议从阶段 1 开始实施：

1. 新建 `frontend-react/` React + TS + Vite 工程。
2. 迁移 `types` 和 `api`，先跑通 `/api/*` client。
3. 实现 Workbench shell 和设计 token。
4. 优先落地 `/documents` 与 `/experiments`，因为它们最近刚改过，也是最容易出现回归的页面。
