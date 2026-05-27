# 2026-05-26 模块 README 中文化计划

## 要解决的问题

当前项目自有 README 不完整，且已有 README 中存在英文标题、英文段落和英文说明，不符合 `PROJECT_CONTEXT.md` 中“各模块 README 默认使用中文”的要求。

同时，`PROJECT_CONTEXT.md` 要求以下一级模块必须有中文 README：

- 根目录 `README.md`
- `frontend/README.md`
- `backend-java/README.md`
- `ai-service/README.md`
- `infra/README.md`
- `scripts/README.md`

当前实际存在的自有 README 只有：

- `README.md`
- `ai-service/README.md`
- `docs/plans/README.md`

## 调研过程中发现的重要信息

- `frontend/node_modules/` 中存在大量第三方 README，这些属于依赖包文档，不属于项目自有文档，本次不修改。
- `frontend/`、`backend-java/`、`infra/`、`scripts/` 缺少模块 README，需要补齐。
- 必要的技术名词、命令、目录名、接口路径、配置项和文件名需要保留原文或代码格式，例如 `FastAPI`、`Spring Boot`、`npm.cmd run dev`、`POST /api/rag/query`。

## 涉及模块

- 根目录项目说明
- 前端模块
- Java 后端模块
- Python AI 服务模块
- 基础设施模块
- 脚本模块
- 计划文档目录说明
- 交接文档与 review 文档

## 预计修改文件

- `README.md`
- `frontend/README.md`
- `backend-java/README.md`
- `ai-service/README.md`
- `infra/README.md`
- `scripts/README.md`
- `docs/plans/README.md`
- `docs/reviews/2026-05-26-readme-localization-review-prompt.md`
- `docs/testing/failures/2026-05-26-readme-localization-notes.md`
- `docs/handoff/CURRENT_STATE.md`
- `PROJECT_CONTEXT.md`

## 实现策略

- 将已有 README 的英文标题和英文说明改为中文。
- 补齐缺失模块 README，并按 `PROJECT_CONTEXT.md` 要求包含模块职责、技术栈、目录结构、本地启动方式、常用命令、环境变量、关键入口、重点 review 文件、跨模块调用关系、已实现能力、占位实现、后续待补能力和常见问题。
- 不修改第三方依赖目录中的 README。
- 对技术名词、命令、路径、接口、配置项保留代码格式，避免把可执行内容翻译坏。

## 验证方式

- 使用文件搜索确认自有 README 列表完整。
- 检查 README 内容是否以中文说明为主。
- 检查是否误改 `node_modules` 中的第三方 README。
- 本次只改文档，不运行后端、前端或 AI 服务测试。

## 当前风险

- “英文全部替换为中文”和“命令、路径、接口、技术名词必须保留可执行/可识别形式”存在天然冲突，本次按项目规范处理：说明性文字中文化，命令、路径、接口、类名、配置项保留原文。
