# 2026-06-17 RAGAS 评估体系接入 Review Prompt

请从架构边界、评估口径和可维护性角度审查本次 RAGAS 接入：

- `ai-service/app/rag/evaluators/ragas_bridge.py` 是否只做 RAGAS 兼容数据映射与懒加载，避免把 RAGAS/Pydantic v2 依赖带入 FastAPI 主服务热路径。
- `ai-service/app/rag/evaluators/testset_generation.py` 是否能从已上传文档 chunk 生成可审核的 `DRAFT` 样本，并正确过滤 parent / image / toc / low-quality chunk。
- `ai-service/scripts/generate_ragas_testset_draft.py`、`export_ragas_dataset.py`、`run_ragas_evaluation.py` 与 `scripts/*.ps1` 是否适合本项目 Windows 本地工作流。
- 生成的 JSON 是否兼容现有 Spring Boot `rag_evaluation_cases` 导入 schema，审核 CSV 是否足以支撑人工半自动修改。
- 测试是否覆盖字段映射、gold chunk 去重、JSONL、草稿生成、审核 CSV 和 RAGAS 缺依赖提示。

验证命令：

```powershell
cd ai-service
.\.venv\bin\python.exe -m pytest tests\test_ragas_bridge.py tests\test_ragas_testset_generation.py tests\test_strategy_comparison_evaluator.py -q --basetemp ..\.tmp\pytest-ragas
```
