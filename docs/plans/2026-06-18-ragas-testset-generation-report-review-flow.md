# 2026-06-18 RAGAS 测评集生成、结果回填与页面审核流

## 目标

补齐三项能力：

- 自动生成测评集从规则式草稿升级为可选 LLM / RAGAS TestsetGenerator 风格复杂题型生成，同时保留无依赖 fallback。
- RAGAS 离线评估报告可回填到 Spring Boot 的 `rag_experiment_evaluations` 历史记录。
- 人工审核从 CSV-only 扩展到 `frontend-react` 页面内审核、编辑和状态流转。

## 架构边界

- FastAPI / AI-service：负责测评集生成、RAGAS JSONL 映射和离线评分脚本。
- Spring Boot：负责评测集、实验、评估历史、RAGAS 报告字段的业务持久化。
- 前端：只调用 Spring Boot `/api/*`，不直接访问 FastAPI 或 RAGAS sidecar。
- RAGAS 依赖继续保持可选，不加入主 `ai-service` 运行时依赖，避免 Pydantic v1 / v2 冲突。

## 实施切片

1. AI-service
   - `generate_ragas_testset_draft.py` 增加 `--generator-mode rule|llm|ragas`。
   - LLM 模式使用现有 OpenAI-compatible adapter 生成复杂题型 JSON，失败时明确报错或 fallback。
   - RAGAS 模式懒加载 `ragas.testset.TestsetGenerator`，仅在独立 RAGAS 环境中运行。
   - 输出保持 Spring Boot import item schema，并继续生成审核 CSV。

2. Spring Boot
   - 新增 Flyway migration，为 `rag_experiment_evaluations` 增加 RAGAS 报告字段。
   - 新增 DTO 和接口：按 evaluation id 回填报告。
   - Response/history/summary 透出报告字段。

3. frontend-react
   - 实验评估页面新增审核工作区：状态筛选、草稿/通过/拒绝计数、编辑问题/答案/id/备注、通过/拒绝/待审按钮。
   - 保留导入 JSON/CSV 能力，导入后可在页面内继续审核。
   - 全中文文案，避免乱码。

## 验证

- AI-service targeted pytest。
- Spring Boot service/controller 单测或 Maven targeted test。
- React typecheck/build，必要时用 Playwright 验证 `/experiments` 页面渲染与审核操作。
