# Advanced RAG Phase 4 实现计划

## 背景与要解决的问题

当前项目已经具备 RAG 基础链路，但 Advanced RAG 相关能力在前端、Java 后端、Python AI 服务之间还没有完全打通，存在前端可选策略多于实际 Python 实现、部分 schema 已预留但未使用、检索增强链路未完成等问题。

本阶段需要解决以下问题：

- 前端已经提供多种 RAG 策略选项，但 Python 实际只有 `BasicRagStrategy`，策略选择无法真实落到不同后端行为。
- `metadata filter` 端到端不通，前端、Java 后端、Python AI 服务与 repository 查询之间缺少完整透传与应用。
- `query rewrite`、`multi-query`、`parent-child` 能力缺失，无法验证 Advanced RAG 的核心工程链路。
- `rerank` 当前仍是 stub，但已有可调用链路，需要纳入策略编排，先完成工程链路验证。

## 调研发现

当前代码和 schema 中已经预留了不少 Advanced RAG 的基础能力，可以在 Phase 4 中复用并补齐链路：

- PostgreSQL `search_chunks` 已经具备 `vector_score + keyword_score` 的 hybrid 检索雏形，权重为 `0.7 / 0.3`。
- Python AI 服务中已有 `AdapterReranker`，可用于 `hybrid-rerank`、`advanced-rag` 等策略的 rerank 阶段。
- `rag_runs.rewritten_query` schema 已预留，可用于保存 query rewrite 后的查询文本。
- `document_chunks.parent_chunk_id` schema 已预留，可作为 parent-child 检索增强的结构基础。
- 前端策略列表中已经出现 `hybrid-rerank`、`parent-child`、`metadata-filter`，但后端能力尚未完全对应。

## 当前目标范围

本阶段目标是完成 Phase 4 Advanced RAG 的工程闭环，让策略选择、查询改写、多查询扩展、metadata filter、parent-child fallback、rerank 链路可以端到端运行和验证。

暂不纳入本阶段范围：

- LangGraph。
- GraphRAG。
- 复习辅助。
- 面试辅助。

## 涉及模块

本计划涉及以下模块：

- `ai-service`：Python RAG 策略、query transformer、repository 检索增强、rerank 编排。
- `backend-java`：请求 DTO、AI 服务请求透传、retrieval result rank 修复。
- `frontend`：RAG 策略类型、策略列表、`metadataFilters` 请求透传。
- `docs/experiments`：补充 Advanced RAG 评估问题，方便交付后验证。

## 实现策略

### 1. Python 增加 query_transformers

在 `ai-service` 中新增 query transformer 能力，至少包含：

- `QueryRewriter`：将用户原始问题改写为更适合检索的查询文本。
- `MultiQueryExpander`：基于原始问题或改写问题生成多个检索查询。

实现建议：

- 先提供可运行的工程实现，不依赖真实外部 LLM 能力。
- 在当前 LLM 仍为 stub 或 adapter 不稳定时，允许使用确定性 fallback，例如返回原 query、添加有限模板化变体。
- 保留清晰接口，后续可替换为真实 LLM query rewrite 和 multi-query expansion。
- 将 rewritten query 写入已有 `rag_runs.rewritten_query` 字段，便于追踪和评估。

### 2. Python 增加 AdvancedRagStrategy

在 Python RAG 策略层新增 `AdvancedRagStrategy`，并由 `RagService` 统一分发以下策略名：

- `basic-rag`（继续由 `BasicRagStrategy` 承接）
- `hybrid-rerank`
- `metadata-filter`
- `parent-child`
- `advanced-rag`

策略行为建议：

- `basic-rag`：保持现有基础检索与生成链路，作为兼容基线。
- `hybrid-rerank`：使用现有 PostgreSQL hybrid 检索结果，再调用 `AdapterReranker` 进行重排。
- `metadata-filter`：在检索时应用 metadata 等值过滤，确保端到端透传可验证。
- `parent-child`：在基础检索结果之上追加 parent-child 或邻近 chunk 上下文增强。
- `advanced-rag`：组合 query rewrite、multi-query、metadata filter、hybrid retrieval、rerank、parent-child fallback 的完整链路。

实现重点：

- 保留 `BasicRagStrategy` 的稳定行为，避免破坏现有基础问答。
- 策略分发应明确，不要让前端传入的策略名静默退化为 Basic 行为而无法观测。
- 日志或 run 记录中应尽量体现启用的策略、rewritten query、multi-query 数量、rerank 是否执行、metadata filter 是否应用。

### 3. Python repository 增加 parent-child 邻近 chunk 上下文增强 fallback

基于 `document_chunks.parent_chunk_id` 已预留字段，实现 parent-child 上下文增强。

由于当前数据中可能没有真实 parent chunk 结构，需要提供 fallback：

- 本阶段优先实现同文档内 chunk 顺序邻近窗口 fallback（命中 chunk 前后各 1 个）。
- `parent_chunk_id` 真实父块查询作为后续增强，不纳入本轮最小闭环。
- fallback 范围建议先保持保守，例如命中 chunk 前后各 1 个邻近 chunk，避免上下文膨胀。
- 对增强后的 chunk 做去重，避免同一 chunk 在多查询或邻近补充中重复进入 prompt。

### 4. Java RagQueryRequest 增加 metadataFilters 并透传到 AiRagQueryRequest

在 `backend-java` 请求模型中补充 `metadataFilters` 字段，并在调用 Python AI 服务时完整透传到 `AiRagQueryRequest`。

实现重点：

- 字段类型建议使用简单 map 结构，先支持 metadata 等值过滤。
- 保持 JSON 字段名与前端、Python 一致，例如 `metadataFilters`。
- 避免在 Java 层吞掉空 map 与非空 map 的区别，便于后端判断是否启用 metadata filter。

### 5. Java 修复 retrieval result rank 计算

修复 retrieval result rank 当前使用 `indexOf` 计算的问题，改为顺序计数。

原因：

- `indexOf` 对重复对象或 equals 行为敏感，可能导致 rank 错误。
- 顺序计数更符合 retrieval result 的展示和评估语义。

实现建议：

- 遍历 retrieval results 时维护递增计数器。
- rank 从 1 开始，保持用户可读和评估报表一致。

### 6. 前端类型和 sendChatMessage 透传 metadataFilters，策略列表补齐 basic-rag/advanced-rag

前端需要补齐请求类型、发送逻辑和策略列表：

- 请求类型增加 `metadataFilters`。
- `sendChatMessage` 透传 `metadataFilters` 到 Java 后端。
- 策略列表补齐 `basic-rag` 与 `advanced-rag`。
- 保留已有 `hybrid-rerank`、`parent-child`、`metadata-filter`。

实现重点：

- 前端策略值必须与 Python 策略分发使用的字符串完全一致。
- 如果 UI 暂无 metadata filter 编辑控件，也应先保证类型和 API 参数可传递，后续再扩展交互。
- 避免仅更新展示文案而没有更新实际请求 payload。

### 7. docs/experiments/eval-questions.md 补 Advanced RAG 评估问题

在实验文档中补充 Advanced RAG 评估问题，用于验证 Phase 4 能力。

建议覆盖：

- Basic RAG 与 Advanced RAG 对同一问题的回答差异。
- metadata filter 是否能限制检索范围。
- query rewrite 是否改善表达不完整或口语化问题的召回。
- multi-query 是否能覆盖同义表达或相关概念。
- parent-child fallback 是否能补足命中 chunk 周边上下文。
- rerank 链路是否能改变候选 chunk 排序。

## 预计修改文件清单

预计需要修改或新增以下文件，实际文件名以当前项目结构为准：

- `ai-service/app/rag/strategies.py` 或现有 RAG strategy 所在文件：新增 `AdvancedRagStrategy`，接入多策略分发。
- `ai-service/app/rag/query_transformers.py`：新增 `QueryRewriter`、`MultiQueryExpander`。
- `ai-service/app/repositories/*`：扩展 chunk 搜索接口，支持 metadata filter 与 parent-child 邻近 chunk fallback。
- `ai-service/app/schemas/*` 或请求模型所在文件：补充 `metadataFilters`、策略名、rewritten query 相关字段映射。
- `ai-service/app/services/*`：在 RAG run 创建、查询执行、结果记录中接入 rewritten query、multi-query、rerank 状态。
- `backend-java/src/main/java/**/RagQueryRequest.java`：增加 `metadataFilters`。
- `backend-java/src/main/java/**/AiRagQueryRequest.java`：增加 `metadataFilters`。
- `backend-java/src/main/java/**` 中调用 AI 服务的 client/service：透传 `metadataFilters`。
- `backend-java/src/main/java/**` 中 retrieval result 构建逻辑：修复 rank 计算。
- `frontend/src/**` 中聊天请求类型定义：增加 `metadataFilters`。
- `frontend/src/**` 中 `sendChatMessage` 实现：透传 `metadataFilters`。
- `frontend/src/**` 中 RAG 策略列表或配置：补齐 `basic-rag`、`advanced-rag`。
- `docs/experiments/eval-questions.md`：补充 Advanced RAG 评估问题。

## 重点 review 文件

交付前重点 review 以下文件和逻辑：

- Python RAG strategy 分发文件：确认 `basic-rag`、`hybrid-rerank`、`metadata-filter`、`parent-child`、`advanced-rag` 都有明确行为。
- Python repository 检索文件：确认 metadata filter 确实参与 SQL 或查询条件，且 parent-child fallback 去重正确。
- Python query transformer 文件：确认 rewrite 和 multi-query 有稳定 fallback，不会因 stub LLM 中断主链路。
- Python RAG run 记录逻辑：确认 `rag_runs.rewritten_query` 被正确写入。
- Java `RagQueryRequest` 和 `AiRagQueryRequest`：确认字段命名、JSON 序列化、透传一致。
- Java retrieval result 构建逻辑：确认 rank 使用顺序计数，不再使用 `indexOf`。
- 前端 API 类型与 `sendChatMessage`：确认 `metadataFilters` 在 payload 中真实发送。
- 前端策略列表：确认展示值与后端策略字符串一致。
- `docs/experiments/eval-questions.md`：确认评估问题能覆盖 Phase 4 关键链路。

## 测试计划

### Python

执行编译检查：

```bash
python -m compileall ai-service
```

执行 Python 测试：

```bash
pytest
```

重点验证：

- `basic-rag` 保持可用。
- `advanced-rag` 可完成 query rewrite、multi-query、检索、rerank、上下文增强、生成流程。
- `metadata-filter` 策略下过滤条件能进入 repository 查询。
- parent-child 无真实 parent 数据时能使用邻近 chunk fallback。

### Java

执行编译：

```bash
mvn compile
```

重点验证：

- `RagQueryRequest.metadataFilters` 能正确反序列化。
- `AiRagQueryRequest.metadataFilters` 能正确序列化到 Python AI 服务请求。
- retrieval result rank 从 1 开始递增，且不受重复对象影响。

### Frontend

执行构建：

```bash
npm run build
```

重点验证：

- 策略列表包含 `basic-rag`、`hybrid-rerank`、`metadata-filter`、`parent-child`、`advanced-rag`。
- `sendChatMessage` payload 中可携带 `metadataFilters`。
- 现有聊天页面和基础 RAG 查询不回归。

### 端到端验证

使用 `docs/experiments/eval-questions.md` 中补充的问题进行人工验证：

- 对比 `basic-rag` 与 `advanced-rag` 的检索结果和回答。
- 使用 metadata filter 验证检索范围是否收敛。
- 查看 RAG run 记录，确认 `advanced-rag` 的 rewritten query 被保存。
- 查看 retrieval results，确认 rerank 后 rank 顺序正确。
- 在无 parent chunk 数据时，确认邻近 chunk fallback 生效且没有重复 chunk。

## 已知风险

- embedding、rerank、LLM 当前可能仍是 stub 或 adapter 级实现，策略效果主要验证工程链路，不代表真实模型效果。
- `parent-child` 当前如果没有真实 parent 数据，只能通过同文档邻近 chunk fallback 提供上下文增强。
- metadata filter 第一阶段先支持等值过滤，不覆盖范围过滤、数组包含、复杂布尔条件等高级过滤语义。
- multi-query 可能增加检索次数，需要控制 query 数量、候选 chunk 数量和最终 prompt 长度。
- rerank 链路虽然可用，但如果底层模型是 stub，排序变化不一定具有真实相关性意义。
- query rewrite 如果使用 fallback 或模板化实现，可能无法显著改善召回，只能验证字段记录和流程编排。
- Advanced RAG 组合链路更长，需要确保任一增强步骤失败时不会中断基础 RAG 查询。

## 交接标准

Phase 4 完成后，应满足以下交接标准：

- 前端可选择的 RAG 策略与 Python AI 服务实际支持的策略一致。
- `metadataFilters` 能从前端透传到 Java，再进入 Python repository 检索逻辑。
- `advanced-rag` 策略能串联 query rewrite、multi-query、hybrid retrieval、rerank、parent-child fallback。
- `rag_runs.rewritten_query` 能记录改写后的查询。
- retrieval result rank 使用稳定的顺序计数。
- Advanced RAG 评估问题已补充到 `docs/experiments/eval-questions.md`。
- Python、Java、Frontend 三端基础编译或构建命令通过，或有明确记录说明失败原因与后续处理项。
