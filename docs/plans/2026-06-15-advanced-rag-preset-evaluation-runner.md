# 2026-06-15 Advanced RAG Preset Evaluation Runner

## Goal

将当前分散的 RAG 策略改造成“统一 Advanced RAG 引擎 + preset 配置”的结构，并补齐评测集自动运行能力，使项目能够对 Query Rewrite、Multi-query、Hybrid Retrieval、Rerank、Parent-Child、GraphRAG 等能力做可量化消融实验。

最终目标不是让用户在普通聊天页看到一堆复杂策略，而是在工程内部统一实现，在实验页按 preset 批量跑同一批评测样本，得到可比较的 `recall@k`、`precision@k`、`MRR`、`citation_hit`、延迟等指标。

## Current State

- AI 服务已有 `AdvancedRagStrategy`，但能力开关主要通过 `strategy_name` 在代码里硬编码判断。
- 当前策略包括 `hybrid-rerank`、`metadata-filter`、`parent-child`、`advanced-rag`、`graph-rag`，它们本质上已经共用同一个 Advanced RAG 执行类。
- 评测集已经持久化到 Spring Boot，字段包括问题、标准答案、相关 chunk/document、期望引用 chunk 和 `topK`。
- 当前评估执行主要依赖“选择已有 RAG run 后评分”，不适合自动比较不同策略 / chunk 配置。
- `recall@k`、`precision@k`、`MRR`、`citation_hit` 已在 FastAPI 侧计算，但主要写入 evaluator notes，没有结构化落库。

## Architecture Boundaries

- 前端只调用 Spring Boot `/api/*`，不直接访问 FastAPI。
- Spring Boot 负责实验、评测集、评估历史、RAG run 持久化和 API 编排，不实现检索、生成或评分算法。
- FastAPI 负责 RAG preset 解析、检索、生成、评估指标计算和 trace 生成。
- PostgreSQL 继续作为业务数据、chunk、embedding、RAG run 和评估历史的统一存储。

## Target Design

### 1. Advanced RAG Preset Model

在 AI 服务中引入配置化 preset，避免在 `AdvancedRagStrategy.run()` 中散落硬编码判断。

建议新增：

```text
ai-service/app/rag/strategies/presets.py
```

核心配置字段：

```text
query_rewrite
multi_query
metadata_filter
parent_child
rerank
graph_expand
```

建议 preset：

```text
hybrid-rerank    = hybrid retrieval + rerank
metadata-filter  = hybrid retrieval + metadata filter + rerank
parent-child     = hybrid retrieval + parent-child context + rerank
advanced-rag     = query rewrite + multi-query + metadata filter + parent-child + rerank
graph-rag        = advanced-rag + graph expansion
```

`basic-rag` 继续保留为 baseline，不强行塞进 Advanced RAG 类，便于实验中保留最小基线。

### 2. Runtime UX vs Experiment UX

用户聊天页保留简化模式：

```text
basic-rag
advanced-rag
graph-rag
```

实验页保留细粒度 preset：

```text
basic-rag
hybrid-rerank
metadata-filter
parent-child
advanced-rag
graph-rag
```

这样既避免用户侧复杂，又能在实验侧做消融分析。

### 3. Evaluation Runner

新增“评测集自动运行”能力，不再只依赖手动选择历史 run。

建议新增 Spring Boot API：

```text
POST /api/rag/evaluation-cases/run-batch
```

请求体建议：

```json
{
  "experimentId": "...",
  "caseIds": ["..."],
  "strategyName": "advanced-rag",
  "topK": 5,
  "retrievalOptions": {
    "vectorWeight": 0.7,
    "keywordWeight": 0.3
  }
}
```

执行流程：

```text
for each evaluation case:
  1. Spring Boot 读取 case.question / expectedAnswer / gold labels
  2. Spring Boot 调用现有 RAG query 链路或内部复用 RagService，按 strategyName/topK/retrievalOptions 生成新的 rag_run
  3. Spring Boot 将 run 的 retrieval_results 转发给 FastAPI `/ai/rag/evaluate`
  4. FastAPI 返回 grounded_score、retrieval_score 和结构化指标
  5. Spring Boot 保存 evaluation history
```

注意：Java 不计算指标，只负责把 case gold labels 和 run retrieval results 发给 FastAPI。

### 4. Structured Metrics

建议扩展 `rag_experiment_evaluations`，将关键指标结构化存储。

建议新增 migration：

```sql
ALTER TABLE rag_experiment_evaluations
ADD COLUMN recall_at_k DOUBLE PRECISION,
ADD COLUMN precision_at_k DOUBLE PRECISION,
ADD COLUMN mrr DOUBLE PRECISION,
ADD COLUMN citation_hit DOUBLE PRECISION,
ADD COLUMN latency_ms INTEGER,
ADD COLUMN strategy_config JSONB NOT NULL DEFAULT '{}'::jsonb;
```

FastAPI `RagEvaluationResult` 建议补充：

```text
recall_at_k
precision_at_k
mrr
citation_hit
graph_entity_coverage
graph_relationship_hit
graph_expansion_term_hit
```

`retrieval_score` 可以继续保留为综合分，但前端对比和简历量化应优先使用结构化指标。

### 5. Chunk Optimization Experiments

当前 `SimpleChunker` 是固定 500 字符窗口，`ParentChildChunker` 也是固定窗口策略。后续可以在 preset runner 可用后增加 chunk 实验：

```text
fixed-500
fixed-500-overlap
paragraph-aware
title-aware
parent-child
```

为了避免重新切分后 UUID 失效，评测集后续应支持更稳定的 gold label：

```text
document_id + page_number + section_title + text_span_hash
```

短期可以先继续使用 chunk UUID，长期需要支持相关文本片段或稳定 chunk key。

## Implementation Steps

### Phase 1: Preset Refactor

- 新增 `RagStrategyPreset` / `resolve_rag_preset()`。
- 将 `AdvancedRagStrategy.run()` 中的策略判断改为读取 preset 配置。
- 保留现有策略名称，避免破坏前端和历史数据。
- 更新 AI 侧单元测试，确认各 preset 对应 trace step 状态正确。

### Phase 2: Structured Evaluation Metrics

- 扩展 FastAPI `RagEvaluationResult`。
- 让 evaluator 返回结构化 `recall_at_k`、`precision_at_k`、`mrr`、`citation_hit`。
- 新增 Java DTO 字段映射。
- 新增数据库 migration，扩展 `rag_experiment_evaluations`。
- 保存 evaluation history 时写入结构化指标。

### Phase 3: Evaluation Batch Runner

- 新增 Spring Boot 批量运行请求 DTO。
- 新增 `/api/rag/evaluation-cases/run-batch`。
- 复用现有 RAG query / run persistence 能力，为每个 case 自动生成新的 run。
- 对每个新 run 调用 evaluator。
- 返回每条 case 的 run id、evaluation id、指标和失败原因。

### Phase 4: Frontend Experiment UX

- 实验页新增 preset 选择器、topK、retrievalOptions 控制。
- 新增“按当前评测集批量运行”按钮。
- 对比页展示结构化指标，不再只展示 grounded/retrieval 综合分。
- 最近评估行展示 strategy、topK、latency、recall@k、MRR、citation_hit。

### Phase 5: Chunk Experiment Preparation

- 为 ingest metadata 明确记录 `chunk_strategy`、`chunk_size`、`chunk_overlap`。
- 增加 chunk 策略版本字段，便于同一文档不同切分方案对比。
- 后续再实现 paragraph-aware / title-aware chunker。

## Validation Plan

- AI service:
  - `pytest ai-service/tests/test_advanced_rag_strategy.py`
  - `pytest ai-service/tests/test_strategy_comparison_evaluator.py`
  - 新增 preset resolver 单元测试。
- Spring Boot:
  - `mvn -f backend-java/pom.xml test`
  - 覆盖 batch runner 请求映射、evaluation case 读取、AI gateway 调用和结构化指标持久化。
- Frontend:
  - `npm.cmd --prefix frontend run typecheck`
  - `npm.cmd --prefix frontend run build`
- Smoke:
  - 创建 2-3 条 evaluation cases。
  - 分别以 `basic-rag`、`hybrid-rerank`、`advanced-rag` 批量运行。
  - 验证每个 case 生成新 rag run、新 evaluation history，并且结构化指标可在对比页展示。

## Acceptance Criteria

- `AdvancedRagStrategy` 不再通过散落的 `strategy_name == ...` 判断控制核心能力，而是通过 preset 配置驱动。
- 实验页可以选择策略 preset，对一组评测样本自动生成 run 并完成评估。
- 评估历史中结构化保存 `recall@k`、`precision@k`、`MRR`、`citation_hit`。
- 对比页可以按 strategy 聚合展示平均指标。
- 保持服务边界：前端不直连 FastAPI，Java 不实现评分算法。

## Resume Value

完成后可在简历中描述为：

```text
将多种 RAG 能力统一抽象为配置化 Advanced RAG 引擎，并构建评测集自动运行器，对 Query Rewrite、Hybrid Retrieval、Rerank、Parent-Child Chunk 等能力进行消融实验；基于人工标注样本结构化统计 recall@k、MRR 与 citation_hit，形成可量化的 RAG 优化闭环。
```
