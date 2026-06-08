# 审查提示：RAG 检索选项 UI

请审查 `rag-retrieval-options-ui` 相关改动，重点确认实现是否符合项目架构边界、数据流和验证要求。

## 重点关注

- 前端不得直接调用 FastAPI，浏览器请求必须经过 Spring Boot `/api/*`。
- Spring Boot 只做桥接、业务持久化、DTO 映射和事务边界，不实现 RAG、GraphRAG 或 evaluator 评分逻辑。
- FastAPI 负责 RAG、Agent、GraphRAG、检索策略、生成和评估逻辑。
- 新增字段、trace payload、metadata 和 API 响应必须向后兼容。
- assistant-turn 请求中的 `retrievalOptions` 必须到达 FastAPI Agent workflow，并且不影响未传该字段的旧请求。
- 测试应覆盖主要成功路径、回退路径和跨服务透传路径。

## 建议验证命令

- `.\.venv\bin\python.exe -m pytest tests/test_agent_workflow.py tests/test_advanced_rag_strategy.py -q`
- `mvn.cmd test "-Dtest=AgentServiceTest,AssistantTurnServiceTest"`
- `npm.cmd --prefix frontend run typecheck`
- `npm.cmd --prefix frontend run build`
- `python -m py_compile smoke_test.py`
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`

## 审查结论记录

- 若发现问题，应标注文件、行为风险和建议修复方式。
- 若无问题，应说明仍存在的测试缺口或后续观察点。

本轮验证结果：以上命令均已通过；全链路 smoke 共 147 项通过、0 项失败。
