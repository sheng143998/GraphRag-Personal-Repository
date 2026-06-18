# React 评测实验删除能力 Review Prompt

## 背景

本次变更补齐 `frontend-react` 评测实验页面中的删除入口，覆盖单条样本删除、当前筛选样本批量删除、最近导入样本删除和当前实验删除。前端仍只调用 Spring Boot `/api/*`，不直接访问 FastAPI。

## 重点审查范围

- `frontend-react/src/api/experiments.ts`
- `frontend-react/src/features/experiments/ExperimentsWorkspace.tsx`
- `frontend-react/src/styles/experiments.css`

## 审查问题

1. 删除实验、删除样本是否全部通过统一 API client 进入 Spring Boot `/api/rag/*`。
2. 批量删除当前筛选样本是否只删除当前 UI 筛选集合，且成功后能同步本地列表、选中项和最近导入缓存。
3. 最近导入样本删除是否避免删除已经不存在的样本，删除后是否清空缓存。
4. 单条样本删除和实验删除是否有 `window.confirm` 防误删提示。
5. 删除按钮禁用态、危险按钮样式和移动端布局是否符合当前页面设计密度。

## 已执行验证

- `npm.cmd --prefix frontend-react run typecheck`
- `npm.cmd --prefix frontend-react run build`
- Playwright + Edge 渲染验证 `/experiments`，使用浏览器侧 mock `/api/*`：
  - 页面非空渲染，无框架错误覆盖层。
  - 四个删除入口均可见：删除当前实验、删除最近导入、删除当前筛选样本、删除样本。
  - 点击单条删除样本并确认后，触发 `DELETE /api/rag/evaluation-cases/{id}`，页面显示删除成功提示并保留下一条样本。

## 已知说明

Playwright 控制台仅出现 React Router v7 future flag warning，属于依赖升级提示，不影响本次功能。
