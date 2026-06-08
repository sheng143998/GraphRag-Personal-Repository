# 2026-06-08 薄弱点优先级

## 目标

本计划记录 `weak-point-prioritization` 相关工作的实现意图、边界和验证方式。该工作服务于本地知识库 Agent / Advanced RAG 项目，要求保持前端、Spring Boot 与 FastAPI 的职责边界清晰。

## 范围

- 按当前主题补齐对应模块能力或验证入口。
- 前端浏览器请求仅允许进入 Spring Boot `/api/*`。
- Spring Boot 只负责业务编排、桥接、DTO 映射和持久化，不实现 RAG、GraphRAG 或 evaluator 评分逻辑。
- FastAPI 继续负责 RAG、Agent、GraphRAG、检索、生成与评估逻辑。
- 命令、接口、字段、策略名和模型名保持原样，便于与代码和测试对应。

## 实施要点

- 根据 `weak-point-prioritization` 的主题更新对应服务、测试或文档。
- 保持改动小步可验证，避免跨模块混入无关重构。
- 如果涉及 UI，优先复用现有 Pinia store、`frontend/src/api/*` 和页面样式。
- 如果涉及评估或检索，必须保留可观测 trace、metadata 或 smoke 断言。

## 验证方式

- `mvn.cmd test`
- `npm.cmd --prefix frontend run typecheck`
- `npm.cmd --prefix frontend run build`
- `python -m py_compile smoke_test.py`
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`

## 备注

本文件已从历史英文计划文档中文化；文件名保持不变以避免破坏既有索引和交叉引用。
