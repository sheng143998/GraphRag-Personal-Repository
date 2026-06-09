# 自然化 LLM 问题重写测试记录

## 观察点

- 旧 prompt 鼓励在 `rewritten_query` 中添加同义词、相关词、上位概念词和领域术语，真实 trace 中出现了不通顺的关键词串。
- 用户选择方案 1：主重写问题自然可读，multi-query 承担扩展。

## 处理

- `rewrite` prompt 明确要求一个自然完整问题，并禁止 standalone keyword list。
- `expand` prompt 保留语义扩展目标，但要求每个变体仍然是可读查询。
- AI 单元测试新增 prompt 约束断言。

## 风险

- 如果真实 LLM 不遵守格式，仍会回退到原始问题。
- 如果真实 LLM 虽然返回 `REWRITTEN_QUERY` 但仍输出关键词串，目前主要依靠 prompt 约束，后续可增加结构化 JSON 或启发式质量检查。
