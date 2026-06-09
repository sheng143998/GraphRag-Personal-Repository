# Review Prompt: 自然化 LLM 问题重写

请审查自然化 LLM 问题重写相关改动，重点确认：

- `rewritten_query` prompt 是否要求输出自然、通顺、完整的问题。
- 同义词、相关词、上位概念词和领域术语扩展是否留给 `multi_query_expand`。
- 测试是否覆盖 prompt 约束，避免之后退回关键词堆砌式重写。
- 变更是否仍保持 RAG 逻辑在 FastAPI，Spring Boot 只负责桥接和持久化。
