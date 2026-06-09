# 自然化 LLM 问题重写计划

## 背景

用户选择方案 1：`rewritten_query` 保持自然、通顺、可读，`multi_query_expand` 负责不同角度扩展和同义词 / 相关词 / 上位概念词覆盖。当前 LLM 重写容易输出关键词串，trace 可读性不好。

## 实施范围

- 调整 FastAPI `AdapterBackedQueryTransformer.rewrite` prompt，要求输出一个自然完整问题。
- 明确禁止在 `rewritten_query` 中堆砌 standalone keywords、synonym lists 和无关扩展词。
- 保持 `AdapterBackedQueryTransformer.expand` 负责 query variants 和语义覆盖扩展。
- 更新 AI 单元测试，使用自然 rewritten query 示例，并检查 prompt 约束。

## 验证计划

- `uv run --isolated --with pytest --with fastapi==0.95.2 --with pydantic==1.10.26 pytest tests/test_advanced_rag_strategy.py tests/test_agent_workflow.py -q`
- `python -m compileall app`
