# 2026-06-15 RAG 评测 token / 成本 / 耗时可观测性 Review Prompt

## Review 目标

请重点 review 本轮对 RAG 评测平台的完善：Advanced RAG 调用链路是否能真实记录模型 `usage`、分阶段耗时和评测历史成本维度；前端对比页是否能清晰展示新增指标；Java 侧是否仍只做业务编排和持久化，不实现 RAG / evaluator 算法。

## 重点 Review 文件

- `ai-service/app/services/adapters/base.py`
- `ai-service/app/services/adapters/openai_compatible.py`
- `ai-service/app/core/tracing.py`
- `ai-service/app/services/rag_service.py`
- `ai-service/app/rag/strategies/base.py`
- `ai-service/app/rag/strategies/advanced.py`
- `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
- `frontend/src/pages/experiments/ExperimentComparisonPage.vue`
- `frontend/src/styles.css`

## Review 关注点

- OpenAI-compatible adapter 是否只记录 provider 真实返回的 `usage`，没有编造 token / cost。
- `TraceBuilder.record_adapter_metadata()` 对多次 embedding、query rewrite、multi-query、rerank、generate 的 token 和 latency 聚合是否合理。
- trace attributes 中的 `token_usage`、`latency_breakdown`、`adapter_calls` 是否能被 Java 现有 `extractCostSnapshot()` 正确提取。
- `runBatch()` 在实验未绑定知识库时是否能提前给出清晰错误，避免无效 AI 调用。
- 对比页展示 `Recall@K`、`Precision@K`、`MRR`、`Citation`、`Tokens`、`Cost`、阶段耗时后，布局是否仍保持紧凑可读。
- 前端仍然只调用 Spring Boot `/api/*`，没有绕过 Java 直接调用 FastAPI。

## 已执行验证

- `mvn.cmd -f backend-java\pom.xml test`
- `.\ai-service\.venv\bin\pytest.exe ai-service\tests\test_strategy_comparison_evaluator.py ai-service\tests\test_advanced_rag_strategy.py`
- `npm.cmd --prefix frontend run typecheck`
- `npm.cmd --prefix frontend run build`

## 已知限制

- 只有 provider 响应包含 `usage` 时，评测历史才会保存 token / cost；部分 DashScope 或 rerank 接口可能不返回成本字段，此时保持 `null`。
- 当前 batch runner 仍是同步逐条执行，适合本地实验和小批量评测；生产级大量评测后续应改为异步任务队列。
