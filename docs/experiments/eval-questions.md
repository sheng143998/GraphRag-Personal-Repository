# RAG 评估问题集

本文件用于记录固定评估问题，帮助对比 Basic RAG 与 Advanced RAG 策略效果。当前 Phase 4 重点覆盖 Hybrid Search、Rerank、Query Rewrite、Multi-query Retrieval、Parent-Child Retrieval 与 Metadata Filter。

## 使用方式

建议每次调整 RAG 策略后，至少选择同一知识库、同一批文档，分别运行：

- `basic-rag`
- `hybrid-rerank`
- `metadata-filter`
- `parent-child`
- `advanced-rag`

观察指标：

- 召回 chunk 是否相关。
- 引用来源是否准确。
- `vector_score`、`keyword_score`、`rerank_score` 是否有可解释变化。
- `trace.steps` 是否包含对应策略阶段。
- `rag_runs.rewritten_query` 是否记录 query rewrite 结果。
- 回答是否基于引用上下文，是否出现无依据扩展。

## Phase 4 Advanced RAG 评估问题

### 1. Hybrid Search + Rerank

问题：

```text
Spring 事务传播里 REQUIRES_NEW 和 REQUIRED 的区别是什么？
```

验证点：

- `hybrid-rerank` 是否能同时召回包含英文术语和中文解释的 chunk。
- retrieval metadata 是否包含 `vector_score`、`keyword_score`。
- rerank 后 `rerank_score` 是否写入 Java 的 `rag_retrieval_results`。

### 2. Query Rewrite

问题：

```text
我之前学过那个检索增强生成，怎么避免回答没有来源？
```

验证点：

- `advanced-rag` 是否生成 rewritten query。
- Java `rag_runs.rewritten_query` 是否保存改写结果。
- trace 中是否出现 `query_rewrite` step。

### 3. Multi-query Retrieval

问题：

```text
RAG 召回效果差时可以从哪些方向优化？
```

验证点：

- `advanced-rag` 是否生成多个 query variants。
- trace 中 `multi_query_expand` 是否记录 queries。
- fusion metadata 是否记录 `matched_queries` 与 `fusion_method`。

### 4. Metadata Filter

问题：

```text
只在开发经验类型文档里查，之前遇到过哪些数据库连接问题？
```

建议 metadata filter：

```json
{
  "document_type": "development_experience"
}
```

验证点：

- 前端/Java 能否透传 `metadataFilters`。
- Python repository 是否应用等值过滤。
- 返回结果是否收敛到指定 metadata 范围。

### 5. Parent-Child / 邻近上下文增强

问题：

```text
文档上传后 chunks 为空的问题是怎么排查和修复的？
```

验证点：

- `parent-child` 是否执行 `parent_child_context` step。
- 没有真实 parent chunk 时，是否使用 `neighbor-window` fallback。
- citation metadata 是否包含 `parent_child_mode` 与 `context_source_chunk_ids`。

### 6. Advanced RAG 综合策略

问题：

```text
如果我要给这个项目接入真实 embedding 和 reranker，需要改哪些模块？
```

验证点：

- `advanced-rag` 是否串联 query rewrite、multi-query、fusion、parent-child、rerank。
- 回答是否引用 adapter、retriever、reranker、repository、config 相关文档 chunk。
- Basic RAG 与 Advanced RAG 的召回结果是否存在差异。

## 当前限制

- 当前 embedding、LLM、reranker 仍可能是 stub adapter，评估重点是工程链路和 trace 完整性，不代表真实语义效果。
- metadata filter 当前先按等值过滤验证，不覆盖范围过滤、数组包含和复杂布尔条件。
- parent-child 当前优先使用邻近 chunk fallback，后续如引入 parent chunk 切分策略，需要补充新的评估问题。