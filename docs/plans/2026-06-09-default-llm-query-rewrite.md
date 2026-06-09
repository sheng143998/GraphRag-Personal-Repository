# 默认 LLM 查询改写计划

## 背景

用户要求删除前端 `enableLlmQueryTransform` 开关，并将 Advanced RAG 的问题重写策略调整为默认使用 LLM。旧的规则型同义词表扩展过于固定，容易把查询改写成不自然的中英混合短语。

## 实施范围

- Frontend：删除聊天页 LLM 查询转换开关及 Pinia 状态。
- FastAPI：`advanced-rag` 默认调用 LLM 做 query rewrite 与 multi-query expansion。
- FastAPI：移除规则型 query rewrite / multi-query 类；LLM 失败时仅回退到原始问题或已成功得到的 LLM 重写问题。
- Java：保持 Spring Boot 只透传业务请求和持久化 trace 的职责边界。
- 测试：更新 AI、Java、frontend 和 smoke 相关断言，删除旧开关依赖。

## 验证计划

- `uv run --isolated --with pytest --with fastapi==0.95.2 --with pydantic==1.10.26 pytest tests/test_advanced_rag_strategy.py tests/test_agent_workflow.py -q`
- `npm.cmd --prefix frontend run typecheck`
- `mvn.cmd -q "-Dtest=AgentServiceTest,AssistantTurnServiceTest" test`
- `python -m py_compile smoke_test.py`
