# 2026-06-08 LLM 查询转换回退

## 目标

为 Advanced RAG 增加按请求开启的 LLM 查询改写与多查询扩展路径，同时保留确定性的规则回退能力。

## 范围

- 在 FastAPI AI 服务中新增基于 adapter 的查询转换器。
- 通过 `retrievalOptions.enableLlmQueryTransform` 按请求启用该能力。
- 解析受约束的 LLM 输出，生成改写查询与多查询变体。
- 当 LLM 输出为空、无效或格式异常时，回退到现有规则查询改写与扩展。
- 在 Advanced RAG trace 步骤中记录 provider 与 fallback 元数据。
- 扩展 AI 回归测试与全链路 smoke 覆盖。

## 不在本次范围

- Spring Boot RAG 逻辑。
- 前端开关控件。
- 基于 LLM 的图谱抽取。
- Docker 验证。
