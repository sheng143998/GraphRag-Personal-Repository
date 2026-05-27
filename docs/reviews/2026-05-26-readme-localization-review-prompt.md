# 2026-05-26 README 中文化审查提示

## 本次审查目标

请审查本次 README 中文化是否符合 `PROJECT_CONTEXT.md` 的模块 README 规范：说明性文字使用中文，必要的命令、路径、接口、配置项和技术名词保持可执行或可识别。

## 本次文档范围

本次只处理项目自有 README，不处理第三方依赖目录。

已更新或新增：

- `README.md`
- `frontend/README.md`
- `backend-java/README.md`
- `ai-service/README.md`
- `infra/README.md`
- `scripts/README.md`
- `docs/plans/README.md`

未处理：

- `frontend/node_modules/**/README.md`
- 其他第三方依赖目录中的 README

## 重点审查顺序

1. 根目录 `README.md`
   - 是否能说明项目目标、当前状态、模块职责和快速启动方式。

2. `frontend/README.md`
   - 是否说明页面结构、接口调用位置、路由、状态管理和前端后续待补能力。

3. `backend-java/README.md`
   - 是否说明 Controller / Service / Repository 分层、人工智能服务调用方式、迁移目录、主要接口和 RAG 持久化能力。

4. `ai-service/README.md`
   - 是否说明 RAG 主链路、数据库 repository、retriever、strategy、占位模型和后续真实模型接入方向。

5. `infra/README.md`
   - 是否说明 PostgreSQL、pgvector、Docker Compose、初始化脚本和后续基础设施待补能力。

6. `scripts/README.md`
   - 是否说明每个脚本用途、前置条件、是否会修改本地数据和风险点。

7. `docs/plans/README.md`
   - 是否说明计划文档格式、命名方式和编写约定。

## 验证方式

- 搜索项目自有 README，确认需要存在的模块 README 已补齐。
- 检查 `frontend/node_modules` 中的第三方 README 没有被修改。
- 检查说明性英文已改为中文。
- 检查命令、路径、接口、环境变量没有被翻译坏。

## 当前保留的英文或代码形式

以下内容保留原样是为了可执行、可搜索或与代码一致：

- 命令：`mvn test`、`npm.cmd run dev`、`python -m venv .venv`
- 路径：`src/api/`、`backend-java/src/main/resources/db/migration/`
- 接口：`POST /api/rag/query`、`POST /ai/rag/query`
- 配置项：`AI_SERVICE_MOCK_ENABLED`、`AI_DATABASE_URL`
- 技术名词：`Vue`、`TypeScript`、`Spring Boot`、`FastAPI`、`PostgreSQL`、`pgvector`

## 给用户的审查提示

请优先确认 README 的“中文说明是否易懂”和“命令/路径是否仍可直接使用”。本次没有改业务代码，也没有改第三方依赖 README。
