# React + TypeScript Stitch 前端重构 Review 提示

日期：2026-06-16

请重点 review `frontend-react/`：

1. 浏览器请求是否全部经由 Spring Boot `/api/*`，不得直接调用 FastAPI `/ai/*`。
2. `/documents` 是否保留单文件、多文件、文件夹上传能力，文件夹上传是否保留 `relativePath`。
3. `/experiments` 是否在导入测评集后自动触发 batch RAG run，且不会因为 React state 旧闭包跳过运行。
4. Workbench shell、tokens、文档页和实验页是否贴近 Stitch 的高密度浅色工作台风格。
5. `npm.cmd --prefix frontend-react run typecheck` 和 `npm.cmd --prefix frontend-react run build` 是否通过。

本轮已知已修复问题：

- `ExperimentsWorkspace.handleImport()` 原先在 `loadAll()` 后读取旧 `cases` state，可能导致 `successfulCaseIds` 为空。已改为导入后直接 `fetchEvaluationCases(experimentId)`，再用最新 rows 计算 batch case ids。
- `api/client.ts` 已恢复读取 `localStorage` 中的运行时 API 设置、timeout 和 trace header 开关。
