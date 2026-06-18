# RAGAS 测评集生成、报告回填与页面审核流 Review Prompt

请审查 2026-06-18 这轮围绕 RAGAS 测评闭环的改动，重点关注：

1. `ai-service` 的自动测评集生成是否保持主服务轻量：
   - `rule`、`llm`、`ragas`、`auto` 模式是否边界清晰。
   - RAGAS / LangChain 可选依赖是否只在离线脚本运行时懒加载。
   - LLM 生成 JSON 的映射、证据 chunk 回退和失败降级是否可解释。

2. RAGAS 离线报告回填是否可靠：
   - JSONL 导出是否保留 `evaluationId`、`runId`、`experimentId`、`evaluationCaseId` 定位字段。
   - `PUT /api/rag/experiment-evaluations/ragas-report` 是否只保存报告结果，不把 RAGAS 算法放进 Java。
   - `ragasScores`、`ragasMetricNames`、版本、裁判模型和报告 URI 是否能被 history / summary DTO 带出。

3. React 页面内人工审核流是否完整：
   - 前端是否只调用 Spring Boot `/api/*`。
   - 状态筛选、编辑表单、通过 / 拒绝 / 待审操作是否正确构造 `UpdateEvaluationCasePayload`。
   - required / supporting / acceptable / citation chunk ID 修改后，`relevantChunkIds` 和 `expectedCitationChunkIds` 是否同步合理。

4. 验证要求：
   - Python：`ai-service\.venv\bin\python.exe -m pytest ai-service\tests\test_ragas_bridge.py ai-service\tests\test_ragas_testset_generation.py -q`
   - Java：`mvn.cmd -f backend-java/pom.xml test`
   - React：`npm.cmd --prefix frontend-react run typecheck` 和 `npm.cmd --prefix frontend-react run build`

如果发现风险，请按 P0/P1/P2/P3 排序，并给出具体文件和行号。
