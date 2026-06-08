# Review: 2026-06-04 API 设计文档补全

## Review 目标

请重点 review 新增的接口文档是否准确反映当前代码契约，并确认后续 Agent 能否基于该文档继续开发接口。

## 重点文件

- `docs/architecture/api-design.md`
- `docs/plans/2026-06-04-api-design-docs.md`
- `PROJECT_CONTEXT.md`

## 对照代码

Spring Boot 对外接口：

- `backend-java/src/main/java/com/example/agentknowledge/controller/*Controller.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/**/*.java`
- `backend-java/src/main/java/com/example/agentknowledge/common/api/ApiResponse.java`

FastAPI 内部接口：

- `ai-service/app/api/router.py`
- `ai-service/app/api/routes/*.py`
- `ai-service/app/schemas/*.py`

前端调用映射：

- `frontend/src/api/*.ts`
- `frontend/src/types/index.ts`

## Review 检查点

- Spring Boot `/api/*` 和 FastAPI `/ai/*` 边界是否清晰。
- 请求 / 响应字段是否与 DTO、Pydantic schema 对齐。
- 文档是否明确前端只能调用 Spring Boot，不能直接调用 AI Service。
- 文档是否正确标注当前限制：PDF 解析长耗时、MinerU pending、stub 模型、metadata 类型不完全统一。
- 是否存在让后续 Agent 误以为已完成异步文档任务、真实 LLM 或真实 embedding 的表述。

## 当前未验证项

本次只做接口文档补全，没有运行 HTTP smoke 或启动服务验证。
