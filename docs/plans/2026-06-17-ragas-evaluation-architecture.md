# 2026-06-17 RAGAS 评估接入架构

## 目标

为当前 RAG / Advanced RAG / GraphRAG 实验评估体系增加 RAGAS 兼容层，支持：

- 从现有 RAG run / evaluator payload 导出 RAGAS `SingleTurnSample` 风格数据。
- 在独立 RAGAS 环境中运行 ID-based 与 LLM-based 指标。
- 将 RAGAS 结果回填到现有实验历史或报告文件。
- 后续把测评集自动生成、人工审核和批量评估接成闭环。

## 官方用法核对

核对日期：2026-06-17。

主源：

- PyPI `ragas` 当前版本为 `0.4.3`，项目链接指向 `https://github.com/vibrantlabsai/ragas`，官方文档为 `https://docs.ragas.io`。
- RAGAS 0.4.3 的 PyPI metadata 声明依赖 `pydantic>=2.0.0`，而本项目 `ai-service` 当前固定 `fastapi==0.95.2` 与 `pydantic==1.10.26`。
- PyPI 当前还标记了 `0.4.3` 的一个 vulnerability：`LLM Prompt Injection Vulnerability in Ragas MultiModalFaithfulness`.
- 官方 schema 文档中的 `SingleTurnSample` 支持 `user_input`、`response`、`retrieved_contexts`、`reference`、`reference_contexts`、`retrieved_context_ids`、`reference_context_ids` 等字段。
- 官方 evaluate reference 仍保留 `evaluate(dataset, metrics=...)`，但在 v0.4 后标注为 deprecated，推荐长期转向 `@experiment` decorator；本项目短期只在离线脚本中懒加载使用 `evaluate`，不放入主服务热路径。

因此本次不把 `ragas` 加入 `ai-service` 主依赖，避免破坏 Pydantic v1 服务；先落地兼容数据层和可选离线执行脚本。

## 当前项目现状

### 已具备

- RAG 查询链路：Spring Boot `/api/rag/query` -> FastAPI `/ai/rag/query` -> retriever / strategy / generator -> Spring Boot 持久化 `rag_runs` 和 `rag_retrieval_results`。
- Advanced RAG preset：`hybrid-rerank`、`metadata-filter`、`parent-child`、`advanced-rag`、`graph-rag` 已统一到 AI 服务 preset 配置。
- 评测集管理：Spring Boot 已有 `rag_evaluation_cases`，支持 question、expected answer、required/supporting/acceptable/citation chunk ids、document ids 和 `topK`。
- 评估执行：`POST /api/rag/evaluation-cases/run-batch` 可按样本批量生成 RAG run 并调用 FastAPI `/ai/rag/evaluate`。
- 现有 evaluator：FastAPI 计算确定性指标 `chunk_recall_at_k`、`document_recall_at_k`、`evidence_recall_at_k`、`precision_at_k`、`mrr`、`citation_hit`，并有 GraphRAG metadata 指标。
- 落库：Spring Boot 负责 `rag_experiment_evaluations` 评估历史、结构化指标、token/cost/latency 维度。

### 主要缺口

- 没有 RAGAS 评测集生成器接入。
- 没有把现有 case/run 转为 RAGAS 数据集的正式工具。
- 没有 RAGAS LLM-as-judge 指标结果的结构化落库字段。
- RAGAS 0.4.x 与当前 Pydantic v1 运行时冲突，需要隔离环境或升级 FastAPI/Pydantic。

## 本次落地

新增：

- `ai-service/app/rag/evaluators/testset_generation.py`
  - 从已上传文档生成的 `document_chunks` 或离线 chunk JSON 中抽取高质量候选证据。
  - 自动生成 `DRAFT` 状态的评测样本草稿，字段对齐现有 `rag_evaluation_cases` 导入 schema。
  - 同步输出人工审核 CSV，保留 `humanDecision` / `humanNotes` 列，方便半自动审核修改。
- `ai-service/app/rag/evaluators/ragas_bridge.py`
  - 将 `RagEvaluateRequest` 映射为 RAGAS `SingleTurnSample` 兼容 dict。
  - 将 `citations[*].metadata.content_preview/snippet/context/text/content` 映射为 `retrieved_contexts`。
  - 将 `citations[*].chunk_id` 映射为 `retrieved_context_ids`。
  - 将评测集分层 gold chunk ids 映射为 `reference_context_ids`。
  - 懒加载 RAGAS metrics 与 `EvaluationDataset.from_list(...)` / `evaluate(...)`。
- `ai-service/scripts/export_ragas_dataset.py`
  - 输入现有 `RagEvaluateRequest` JSON，输出 RAGAS JSONL。
- `ai-service/scripts/generate_ragas_testset_draft.py`
  - 支持 `--knowledge-base-id` 从已上传文档 chunk 读取，也支持 `--chunks-json` 离线生成。
  - 输出 Java/Spring Boot 导入接口可用的草稿 JSON 和人工审核 CSV。
- `ai-service/scripts/run_ragas_evaluation.py`
  - 在独立 RAGAS 环境中读取 JSONL 并运行指标，默认 ID-based metrics。
- `scripts/generate-ragas-testset-draft.ps1`
  - Windows 包装入口，便于从知识库或 chunk JSON 一键生成草稿与审核表。
- `scripts/run-ragas-evaluation.ps1`
  - Windows 包装入口，便于指定 RAGAS 独立 Python。
- `ai-service/tests/test_ragas_bridge.py`
  - 覆盖字段映射、gold ids 去重顺序、JSONL 输出和缺依赖保护。
- `ai-service/tests/test_ragas_testset_generation.py`
  - 覆盖自动草稿生成、低质量/父块过滤、导入 JSON、审核 CSV 与 camelCase chunk JSON 读取。

## 推荐接入架构

### 1. 测评集自动生成

短期：

- 从 `document_chunks` 抽取候选 chunk，构造预生成输入文件。
- 在独立 RAGAS 环境运行 testset generation，生成候选 question / reference / reference_contexts。
- 将生成结果导出为项目现有 `rag_evaluation_cases` 导入 JSON，初始状态为 `DRAFT`。

中期：

- AI 服务新增内部脚本或 worker：按 knowledge base、document type、chunk strategy 抽样。
- 对每个样本保存稳定证据锚点：`document_id + chunk_id + section_title + text_span_hash`。
- 对生成样本打上来源 metadata：生成模型、RAGAS 版本、chunk strategy、prompt/template 版本。

### 2. 人工半自动审核

- 保留现有评测集管理页作为审核入口，前端仍只调用 Spring Boot。
- 审核字段建议至少包括：问题是否自然、标准答案是否可由证据支持、required/supporting/acceptable/citation chunk ids 是否准确、是否适合某类策略对比。
- 状态流转建议：`DRAFT -> REVIEWED -> ACTIVE -> ARCHIVED`。
- 审核时优先保留 `requiredChunkIds` 与 `citationChunkIds`，因为它们可同时服务项目确定性指标和 RAGAS ID-based metrics。

### 3. 运行 RAGAS 评估

短期离线路径：

```text
Spring Boot batch run
-> FastAPI /ai/rag/evaluate 计算确定性指标
-> 导出 RagEvaluateRequest JSON
-> ai-service/scripts/export_ragas_dataset.py 生成 JSONL
-> 独立 RAGAS venv 运行 ai-service/scripts/run_ragas_evaluation.py
-> 输出 JSON 报告
```

推荐指标分层：

- 无 LLM / 低成本：`IDBasedContextPrecision`、`IDBasedContextRecall`。
- LLM-as-judge：`Faithfulness`、`ResponseRelevancy`、`FactualCorrectness`。
- 当前项目自己的强约束指标仍保留为主评估口径：chunk/document/evidence recall、precision、MRR、citation hit。

### 4. 结果落库与报告

短期：

- 将 RAGAS JSON 报告存入 `docs/experiments/` 或外部 artifacts。
- 在 `rag_experiment_evaluations.notes` 中写入报告路径、RAGAS 版本、metric names、judge model。

中期建议新增 Flyway migration：

```sql
ALTER TABLE rag_experiment_evaluations
ADD COLUMN ragas_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
ADD COLUMN ragas_metric_names JSONB NOT NULL DEFAULT '[]'::jsonb,
ADD COLUMN ragas_version VARCHAR(32),
ADD COLUMN ragas_judge_model VARCHAR(120),
ADD COLUMN ragas_report_uri VARCHAR(500);
```

职责边界：

- FastAPI / RAGAS sidecar 负责评分与报告生成。
- Spring Boot 负责保存报告路径和结构化 JSONB，不实现 RAGAS 指标算法。
- 前端只读取 Spring Boot `/api/*` 聚合结果。

## 命令

导出 RAGAS JSONL：

```powershell
cd ai-service
.\.venv\bin\python.exe .\scripts\export_ragas_dataset.py --input ..\datasets\samples\rag-evaluate-payloads.json --output ..\datasets\processed\ragas-eval.jsonl
```

从已上传知识库生成 DRAFT 测评集草稿和人工审核表：

```powershell
.\scripts\generate-ragas-testset-draft.ps1 `
  -KnowledgeBaseId "<knowledge-base-uuid>" `
  -OutputJson .\datasets\processed\ragas-draft-cases.json `
  -ReviewCsv .\datasets\processed\ragas-draft-review.csv `
  -Python .\ai-service\.venv\Scripts\python.exe
```

离线从 chunk JSON 生成草稿：

```powershell
.\scripts\generate-ragas-testset-draft.ps1 `
  -ChunksJson .\datasets\processed\chunks-for-review.json `
  -OutputJson .\datasets\processed\ragas-draft-cases.json `
  -ReviewCsv .\datasets\processed\ragas-draft-review.csv `
  -Python .\ai-service\.venv\Scripts\python.exe
```

独立环境运行 RAGAS：

```powershell
python -m venv .venv-ragas
.\.venv-ragas\Scripts\python.exe -m pip install "ragas==0.4.3"
.\.venv-ragas\Scripts\python.exe .\ai-service\scripts\run_ragas_evaluation.py --input .\datasets\processed\ragas-eval.jsonl --output .\docs\experiments\ragas-report.json
```

Windows 包装脚本：

```powershell
.\scripts\run-ragas-evaluation.ps1 -InputPath .\datasets\processed\ragas-eval.jsonl -OutputPath .\docs\experiments\ragas-report.json -Python .\.venv-ragas\Scripts\python.exe
```

## 验证

本次代码验证命令：

```powershell
cd ai-service
.\.venv\Scripts\python.exe -m pytest tests\test_ragas_bridge.py tests\test_ragas_testset_generation.py tests\test_strategy_comparison_evaluator.py -q
```

## 剩余风险

- `ragas==0.4.3` 当前 PyPI 标记存在 multimodal faithfulness 相关 prompt injection 漏洞；本项目短期不启用 multimodal metrics，不把该依赖放入主服务。
- RAGAS 0.4.x 需要 Pydantic v2；若要在线化，需先评估 FastAPI/Pydantic 升级，或把 RAGAS 做成独立 worker/sidecar。
- LLM-as-judge 指标依赖评审模型质量和成本，需要记录 judge model、temperature、prompt/version 和 token usage。
- RAGAS 自动生成样本必须经过人工审核，否则容易把弱证据、目录、图片说明或 OCR 噪声标为 gold。
