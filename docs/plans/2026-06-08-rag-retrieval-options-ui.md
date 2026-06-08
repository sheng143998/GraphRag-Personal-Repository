# 2026-06-08 RAG 检索选项 UI

## 目标

本计划记录 `rag-retrieval-options-ui` 相关工作的实现意图、边界和验证方式。该工作服务于本地知识库 Agent / Advanced RAG 项目，目标是让聊天页用户可以选择混合检索权重预设，并把 `retrievalOptions` 经 Spring Boot assistant-turn 链路透传到 FastAPI Agent。

## 范围

- 聊天页新增混合检索预设与 LLM 查询转换开关。
- Pinia 状态层把 UI 选择转换为 `retrievalOptions`。
- Spring Boot assistant-turn / Agent bridge 只做 DTO 透传，不实现 RAG 逻辑。
- FastAPI Agent 工作流在 `retrieve_and_generate` 步骤记录检索选项可观测字段。
- smoke 脚本覆盖 assistant-turn 请求携带 `retrievalOptions` 并到达 Agent workflow。
- 前端浏览器请求仅允许进入 Spring Boot `/api/*`。
- Spring Boot 只负责业务编排、桥接、DTO 映射和持久化，不实现 RAG、GraphRAG 或 evaluator 评分逻辑。
- FastAPI 继续负责 RAG、Agent、GraphRAG、检索、生成与评估逻辑。
- 命令、接口、字段、策略名和模型名保持原样，便于与代码和测试对应。

## 实施要点

- 前端复用 `frontend/src/stores/workbench.ts` 生成 `retrievalOptions`，`ChatPage.vue` 只负责控件展示和状态切换。
- `frontend/src/api/chat.ts` 与共享类型补充可选 `retrievalOptions` 字段。
- Spring DTO 和 service 保持字段透传，避免把检索策略逻辑放入 Java。
- FastAPI Agent trace 暴露 `retrieval_options_enabled` 与 `retrieval_option_keys`，便于 smoke 断言。
- `smoke_test.py` 增加 assistant-turn 透传断言。

## 验证方式

- `.\.venv\bin\python.exe -m pytest tests/test_agent_workflow.py tests/test_advanced_rag_strategy.py -q`，15 个测试通过。
- `mvn.cmd test "-Dtest=AgentServiceTest,AssistantTurnServiceTest"`，2 个测试通过。
- `npm.cmd --prefix frontend run typecheck`，通过。
- `npm.cmd --prefix frontend run build`，通过。
- `python -m py_compile smoke_test.py`，通过。
- `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1`，147 项通过、0 项失败。

## 备注

Docker 仍不纳入本轮验证；全链路使用本地非 Docker 脚本。
