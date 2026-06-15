# 当前交接状态

更新时间：2026-06-15

## 当前正在做什么

已完成 RAG 评测平台本轮增强：统一 Advanced RAG preset runner、评测集批量运行、结构化指标持久化，并补齐 token / 成本 / 分阶段耗时的可观测链路。

## 已完成什么

- AI 服务 OpenAI-compatible adapter 会记录真实 provider 响应中的 `usage`、HTTP 状态、尝试次数和调用耗时。
- AI trace attributes 新增 `token_usage`、`latency_breakdown`、`adapter_calls`，覆盖 query rewrite、multi-query expansion、embedding、retrieval、rerank、generate 等阶段。
- Java 评测历史已能从 RAG run trace 中提取 prompt / completion / total / embedding / rerank tokens、estimated cost、embedding / retrieval / rerank / LLM latency，并写入 `rag_experiment_evaluations`。
- `runBatch()` 对实验未绑定知识库的情况增加提前校验，避免无效批量评测。
- 前端对比页展示策略聚合的 `Recall@K`、`Precision@K`、`MRR`、`Citation`、平均 Tokens、Cost 和最近评估的阶段耗时。
- 新增 review 文档：`docs/reviews/2026-06-15-rag-evaluation-token-cost-observability-review-prompt.md`。

## 最近验证

- `mvn.cmd -f backend-java\pom.xml test`：通过，22 tests。
- `.\ai-service\.venv\bin\pytest.exe ai-service\tests\test_strategy_comparison_evaluator.py ai-service\tests\test_advanced_rag_strategy.py`：通过，17 tests；仅有 pytest cache 权限警告。
- `npm.cmd --prefix frontend run typecheck`：通过。
- `npm.cmd --prefix frontend run build`：通过。

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

## 下一步建议

- 把 batch runner 改成异步任务模型：保存批次任务、逐条 case 状态、失败原因、可重试能力。
- 增加 CSV / JSON 导入导出评测集，支持从标注文件批量创建 cases。
- 做 chunk 策略实验：记录 chunk_size、overlap、chunk_strategy_version，并支持同一批评测问题对比不同 chunk 配置。
- 进一步补齐真实成本估算：当 provider 不返回 `estimated_cost` 时，可基于模型单价配置计算，但必须在 trace 中标记为 `estimated`。
