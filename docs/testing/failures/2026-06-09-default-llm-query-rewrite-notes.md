# 默认 LLM 查询改写测试记录

## 观察点

- 旧策略通过 `enableLlmQueryTransform` 控制 LLM 查询转换，未开启时使用规则型同义词表。
- 新策略要求 `advanced-rag` 默认调用 LLM，并删除规则型查询改写。

## 风险

- 如果真实 LLM 未配置或输出格式不符合约定，查询改写会回退到原始问题，召回覆盖可能低于真实 LLM 可用时的效果。
- Stub LLM 在测试环境不会产生真实语义扩展，因此单元测试需要注入 Fake LLM 验证默认 LLM 路径。

## 处理

- 使用 Fake LLM 覆盖默认 LLM query rewrite / multi-query 成功路径。
- 覆盖 LLM 输出无效时回退到原始问题的路径。
- 前端和 smoke 脚本删除旧开关依赖。
