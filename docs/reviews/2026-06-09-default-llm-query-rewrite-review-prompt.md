# Review Prompt: 默认 LLM 查询改写

请审查默认 LLM 查询改写相关改动，重点关注：

- `advanced-rag` 是否默认走 LLM query rewrite 与 multi-query expansion。
- 规则型 query rewrite / multi-query 是否已从查询转换器中移除。
- LLM 输出异常时是否只回退到原始问题或已成功得到的 LLM 重写问题。
- 前端是否已删除 `enableLlmQueryTransform` 控件和状态。
- Spring Boot 是否仍保持业务桥接 / trace 持久化职责，没有实现 RAG 查询转换逻辑。
- 测试和 smoke 脚本是否不再依赖旧开关。
