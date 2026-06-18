# 脚本模块

## 模块职责

`scripts/` 保存本地开发、依赖启动、依赖停止、数据库重置、全链路 smoke，以及 RAG/RAGAS 评测辅助脚本。部分脚本会修改本地环境或数据库，运行前请确认当前服务和数据状态。

## 常用命令

```powershell
.\scripts\dev-start.ps1
.\scripts\dev-stop.ps1
.\scripts\reset-local-db.ps1
```

重置数据库前，请确认没有需要保留的本地数据。

## RAGAS 测评集半自动流程

这个流程用于“先自动根据上传文档生成测评集，再由人工半自动审核修改，最后导入后端运行评估”。

### 1. 从已上传文档生成草稿

从知识库数据库读取 `document_chunks`：

```powershell
.\scripts\generate-ragas-testset-draft.ps1 `
  -KnowledgeBaseId "<knowledge-base-uuid>" `
  -OutputJson .\datasets\processed\ragas-draft-cases.json `
  -ReviewCsv .\datasets\processed\ragas-draft-review.csv `
  -Python .\ai-service\.venv\Scripts\python.exe
```

如果已经离线导出了 chunk JSON，也可以这样生成：

```powershell
.\scripts\generate-ragas-testset-draft.ps1 `
  -ChunksJson .\datasets\processed\chunks-for-review.json `
  -OutputJson .\datasets\processed\ragas-draft-cases.json `
  -ReviewCsv .\datasets\processed\ragas-draft-review.csv `
  -Python .\ai-service\.venv\Scripts\python.exe
```

`ragas-draft-review.csv` 是给人工审核的表。重点检查这些列：

- `humanDecision`：填写 `通过`、`拒绝`、`待审` 或 `跳过`。
- `question`：可以直接改成人类更自然的问题。
- `expectedAnswer`：必须完全由证据片段支持。
- `requiredChunkIds`、`supportingChunkIds`、`citationChunkIds`：确认 gold evidence 是否准确。
- 对 ID 列，删除单元格内容表示清空该字段；也可以填写 `[]` 或 `-` 表示清空。要保留自动生成的证据 ID，请不要清空对应单元格。
- `questionType`、`generatorMode`、`metadata`：用于识别规则式、LLM 或 RAGAS 生成来源，以及事实题、推理题、多证据题、故障排查题等复杂题型信息；不会直接导入后端。
- `evidencePreview`：辅助核对证据，不会导入后端。
- `humanNotes`：会合并进后端 `notes`。

默认 `-GeneratorMode rule` 保持规则式生成，不需要额外依赖。要尝试 LLM 复杂题型生成，可使用 ai-service 已配置的 OpenAI-compatible LLM adapter：

```powershell
.\scripts\generate-ragas-testset-draft.ps1 `
  -ChunksJson .\datasets\processed\chunks-for-review.json `
  -OutputJson .\datasets\processed\ragas-llm-draft-cases.json `
  -ReviewCsv .\datasets\processed\ragas-llm-draft-review.csv `
  -GeneratorMode llm `
  -QuestionTypes "fact,reasoning,multi_context,troubleshooting" `
  -Python .\ai-service\.venv\Scripts\python.exe
```

要尝试 RAGAS `TestsetGenerator`，请在隔离 venv 中安装 RAGAS / LangChain 相关依赖，避免把 `ragas` 和 Pydantic v2 带进主 `ai-service` 依赖：

```powershell
python -m venv .venv-ragas
.\.venv-ragas\Scripts\python.exe -m pip install "ragas==0.4.3" langchain-core langchain-openai
.\scripts\generate-ragas-testset-draft.ps1 `
  -ChunksJson .\datasets\processed\chunks-for-review.json `
  -OutputJson .\datasets\processed\ragas-generator-draft-cases.json `
  -ReviewCsv .\datasets\processed\ragas-generator-draft-review.csv `
  -GeneratorMode ragas `
  -RagasTestsetSize 20 `
  -Python .\.venv-ragas\Scripts\python.exe
```

`llm`、`ragas`、`auto` 模式默认在生成失败或缺少可选依赖时回退到规则式草稿，并在 stderr 打印 warning；增加 `-NoFallback` 可改为直接失败。

### 2. 审核后生成后端导入包

```powershell
.\scripts\finalize-ragas-testset-review.ps1 `
  -DraftJson .\datasets\processed\ragas-draft-cases.json `
  -ReviewCsv .\datasets\processed\ragas-draft-review.csv `
  -ExperimentId "<rag-experiment-uuid>" `
  -OutputJson .\datasets\processed\ragas-reviewed-import.json `
  -Python .\ai-service\.venv\Scripts\python.exe
```

状态映射：

- `通过`、`approve`、`yes` -> `ACTIVE`
- `拒绝`、`reject`、`no` -> `REJECTED`
- `待审`、`draft`、`pending` -> `DRAFT`
- `跳过`、`skip`、`ignore` -> 不写入导入包

如果只想导入已通过样本，增加 `-ActiveOnly`。如果不想导入拒绝样本，增加 `-ExcludeRejected`。

`finalize` 会严格校验后端导入契约：`ExperimentId`、chunk id、document id 必须是 UUID，`caseId` 不能超过 120 个字符，`question` 不能为空，并且最终 `items` 不能为空。校验失败时不会写出可导入包。

### 3. 导入后端

`ragas-reviewed-import.json` 已经是 Spring Boot 接口需要的格式：

```json
{
  "experimentId": "...",
  "items": [
    {
      "caseId": "support-case-001",
      "question": "客户设备无法联网时应如何排查？",
      "expectedAnswer": "先确认物理链路，再检查 DHCP、DNS 和网关配置；仍无法恢复时收集日志并升级二线。",
      "requiredChunkIds": ["11111111-1111-1111-1111-111111111111"],
      "citationChunkIds": ["11111111-1111-1111-1111-111111111111"],
      "evaluationTopK": 5,
      "status": "ACTIVE"
    }
  ]
}
```

可直接提交到：

```text
POST /api/rag/evaluation-cases/import
```

注意：批量运行接口只会运行 `ACTIVE` 用例，`DRAFT` 和 `REJECTED` 不会被自动执行。

### 4. 运行 RAGAS 离线指标

项目主 `ai-service` 仍使用 Pydantic v1，`ragas 0.4.x` 需要 Pydantic v2，因此建议使用隔离环境：

```powershell
python -m venv .venv-ragas
.\.venv-ragas\Scripts\python.exe -m pip install "ragas==0.4.3"
.\scripts\run-ragas-evaluation.ps1 `
  -InputPath .\datasets\processed\ragas-eval.jsonl `
  -OutputPath .\docs\experiments\ragas-report.json `
  -Python .\.venv-ragas\Scripts\python.exe
```

## 本地全链路 smoke

当本地 PostgreSQL 已可用，并且 `.env` 包含 `DB_URL`、`DB_USERNAME`、`DB_PASSWORD` 时，可以运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1
```

如果后端 jar 已构建，可跳过构建：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1 -SkipBuild
```

## 注意事项

- PowerShell 脚本无法执行时，先检查执行策略：`Get-ExecutionPolicy`。
- Docker 命令不可用时，确认 Docker Desktop 已启动且在系统 `PATH` 中。
- 数据库重置失败时，检查是否仍有 Java / Python 服务占用连接。
- RAGAS 自动生成的样本必须经过人工审核后再作为正式基准集使用。

## 2026-06-18 RAGAS 增强用法

自动生成测评集现在支持三种生成模式：

```powershell
.\scripts\generate-ragas-testset-draft.ps1 `
  -ChunksJson .\datasets\processed\chunks-for-review.json `
  -OutputJson .\datasets\processed\ragas-draft-cases.json `
  -ReviewCsv .\datasets\processed\ragas-draft-review.csv `
  -GeneratorMode llm `
  -QuestionTypes "fact,reasoning,multi_context,troubleshooting" `
  -Python .\ai-service\.venv\Scripts\python.exe
```

- `rule`：确定性规则草稿，适合无模型环境保底。
- `llm`：调用 AI 服务现有 LLM adapter，生成事实题、推理题、多证据题和故障排查题。
- `ragas`：在隔离 RAGAS 环境中懒加载 `TestsetGenerator`，适合安装了 RAGAS / LangChain 依赖后使用。
- `auto`：优先尝试 `ragas`，失败后尝试 `llm`，再失败则降级到 `rule`。

人工审核有两条路径：

- CSV 路径：继续编辑 `ragas-draft-review.csv`，再运行 `finalize-ragas-testset-review.ps1`。
- 前端路径：将草稿 JSON 导入 React 实验评估页，在页面内筛选“待审 / 已通过 / 已拒绝”，编辑问题、标准答案、证据 chunk ID 和备注，然后点击“通过 / 拒绝 / 待审”保存到 Spring Boot。

RAGAS 离线评估报告可以自动回填后端数据库。导出的 JSONL 输入中如包含 `evaluationId`，或包含 `runId + experimentId/evaluationCaseId`，运行脚本时增加 `-BackfillBackendUrl`：

```powershell
.\scripts\run-ragas-evaluation.ps1 `
  -InputPath .\datasets\processed\ragas-eval.jsonl `
  -OutputPath .\docs\experiments\ragas-report.json `
  -BackfillBackendUrl "http://localhost:8080/api" `
  -RagasVersion "0.4.3" `
  -JudgeModel "qwen-plus" `
  -Python .\.venv-ragas\Scripts\python.exe
```

脚本会写出本地 JSON 报告，并调用：

```text
PUT /api/rag/experiment-evaluations/ragas-report
```

回填 `ragasScores`、`ragasMetricNames`、`ragasVersion`、`ragasJudgeModel` 和 `ragasReportUri`。Java 后端只保存报告结果，不执行 RAGAS 算法。
