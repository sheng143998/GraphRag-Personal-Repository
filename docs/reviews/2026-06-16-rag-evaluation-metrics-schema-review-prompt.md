# RAG 评估指标与评测集 Schema 升级 Review Prompt

## 本次改动

- 评测集样例新增分层证据字段：`requiredChunkIds`、`supportingChunkIds`、`acceptableChunkIds`、`citationChunkIds`。
- 保留旧字段 `relevantChunkIds`、`relevantDocumentIds`、`expectedCitationChunkIds`，并在导入 / 创建时用旧字段兜底新字段，兼容已有 JSON 评测集。
- evaluator 将 `Recall@K` 拆为 `chunkRecall@K`、`documentRecall@K`、`evidenceRecall@K`，其中旧 `recallAtK` 继续作为 `evidenceRecall@K` 的兼容别名。
- `Precision@K` 分母改为实际参与评估的返回结果数量，而不是固定 `topK`，避免 `topK=8` 但实际只返回 5 条时被硬性压低。
- Spring Boot 新增 Flyway 迁移，保存分层证据字段与三类 recall 指标。
- React 导入解析和类型定义支持新字段。

## 重点 Review 文件

- `ai-service/app/rag/evaluators/strategy_comparison.py`
- `ai-service/app/rag/evaluators/base.py`
- `ai-service/app/schemas/rag.py`
- `backend-java/src/main/resources/db/migration/V202606162230__split_rag_evaluation_recall_metrics.sql`
- `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/domain/RagEvaluationCase.java`
- `backend-java/src/main/java/com/example/agentknowledge/domain/RagExperimentEvaluation.java`
- `frontend-react/src/features/experiments/importParser.ts`
- `frontend-react/src/types/index.ts`

## 建议 Review 点

1. 新字段是否满足“核心证据 / 辅助证据 / 可接受证据 / 期望引用”的标注语义。
2. `evidenceRecall@K` 是否应该继续采用“不重复计算同一条召回结果”的口径。
3. `Precision@K` 分母改为实际返回结果数后，是否还需要额外新增 `precisionAtRequestedK` 用于严格候选池评估。
4. 旧字段回填到 `required_chunk_ids` / `citation_chunk_ids` 是否符合已有评测集迁移预期。
5. 前端是否需要进一步把三类 recall 展示到表格，而不是只在类型层支持。

## 已验证

- `mvn.cmd -f backend-java/pom.xml test`
- `npm.cmd --prefix frontend-react run typecheck`
- `npm.cmd --prefix frontend-react run build`
- `ai-service/.venv/bin/python.exe -m pytest tests/test_strategy_comparison_evaluator.py`

## 已知事项

- Python 测试通过，但 pytest cache 目录存在权限 warning，不影响测试结果。
- React 页面当前只完成类型和导入解析兼容，列表展示仍以旧 `recallAtK` / `precisionAtK` 为主。
