# 2026-06-04 API 设计文档补全计划

## 背景

项目已形成前端 -> Spring Boot -> FastAPI AI Service 的多服务链路，但接口契约分散在 Controller、DTO、FastAPI schema 和前端 API 封装中。后续具体接口开发将交给其他 Agent，因此需要先补齐一份可交接的接口设计文档。

## 范围

- 梳理 Spring Boot 对外 `/api/*` 接口。
- 梳理 FastAPI 内部 `/ai/*` 接口。
- 标明前端调用映射和服务职责边界。
- 记录当前限制：PDF 解析长耗时、MinerU pending、AI 实现仍有 stub、metadata 类型尚未完全统一。

## 输出

- `docs/architecture/api-design.md`
- `docs/reviews/2026-06-04-api-design-docs-review-prompt.md`
- `PROJECT_CONTEXT.md` 阶段摘要和关键文档索引

## 非范围

- 不新增业务接口。
- 不修改 Controller / DTO / schema。
- 不启动服务做 HTTP smoke。
- 不修复 PDF 解析链路遗留问题。

## 交接建议

后续 Agent 开发接口时，以 `docs/architecture/api-design.md` 为契约入口，并在完成接口后同步更新该文档、计划文档、review prompt 和必要的失败记录。
