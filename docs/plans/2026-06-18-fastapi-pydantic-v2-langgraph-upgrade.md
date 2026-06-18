# FastAPI / Pydantic v2 / LangGraph 版本升级计划

## 背景

升级前 AI 服务已经引入 LangGraph / LangChain Core 的兼容版本，但仍固定在 FastAPI `0.95.2`、Pydantic `1.10.26`、LangGraph `0.1.5` 和 LangChain Core `0.2.8`。这一组合可以保护当时的 FastAPI 主服务，但会限制后续使用新版 LangGraph supervisor、checkpoint、human-in-the-loop 和 LangChain 工具生态。

## 升级目标

- FastAPI 升级到 `0.137.2`。
- Pydantic 升级到 `2.13.4`。
- LangGraph 升级到 `1.2.5`。
- LangChain Core 升级到 `1.4.7`。
- 引入 LangChain `1.3.9`，为后续 agent / tool / runnable 体系改造预留完整依赖。
- Uvicorn 升级到 `0.49.0`。
- 保持服务边界不变：AI 服务负责 Agent / RAG / evaluator，Spring Boot 只做桥接、业务和持久化。

## 迁移策略

1. 先更新 `ai-service/pyproject.toml` 与 `uv.lock`，在隔离 uv 环境中验证依赖可解析。
2. 将业务代码中 Pydantic v1 风格 `.dict()` 输出收敛到兼容工具，优先消除运行时 deprecation warning 和未来破坏点。
3. 运行 AI 服务 Agent / RAGAS / RAG evaluator 相关测试，确认新版 FastAPI / Pydantic 与 LangGraph API 可用。
4. 运行 Java 桥接测试，确认 Spring Boot DTO 与 AI 服务返回结构未被破坏。
5. 由审查子 Agent 检查升级风险，按 findings 修复。

## 重点风险

- Pydantic v2 中 `.dict()` / `.json()` 仍可用但已废弃，后续应逐步切换为 `model_dump()` / `model_dump_json()`。
- 如果后续引入 `BaseSettings`，必须从 `pydantic-settings` 导入，而不是从 `pydantic` 导入。
- LangGraph 1.x API 仍保留 `StateGraph`、`START`、`END`，但运行时类型和 reducer 语义更严格，需要用真实运行测试覆盖。
- 当前 Agent workflow 在图节点中原地修改 `SupportAgentState`，必须确认新版 LangGraph 不会丢失状态对象。

## 验证命令

```powershell
$env:UV_PROJECT_ENVIRONMENT='..\.tmp\uv-test-ai-service-pydantic-v2-langgraph-latest'
uv run --python 3.12 --managed-python --extra dev python -m pytest tests\test_agent_workflow.py tests\test_support_agent_nodes.py tests\test_support_supervisor_graph.py tests\test_strategy_comparison_evaluator.py tests\test_ragas_bridge.py tests\test_ragas_testset_generation.py -q
```

```powershell
mvn.cmd -f backend-java\pom.xml test "-Dtest=AgentServiceTest,AssistantTurnServiceTest"
```

## 完成结果

- `ai-service/pyproject.toml` 和 `ai-service/uv.lock` 已升级到目标版本组合。
- 新增 `app/core/pydantic_compat.py`，统一 `model_to_dict()` 与 `model_copy_update()`，热路径不再直接依赖 Pydantic v1 `.dict()` / `.copy(update=...)`。
- 新增 `tests/test_api_pydantic_v2_serialization.py`，使用 `httpx.ASGITransport` 覆盖 FastAPI + Pydantic v2 的 HTTP JSON 序列化边界。
- RAGAS bridge 文案已从“规避 Pydantic v1/v2 冲突”调整为“RAGAS 可选懒加载，避免热路径 import”。
- 根据审查修复 `SupportSupervisorWorkflow`：`auto` runtime 只在 LangGraph 依赖不可用时回落本地，图构建或执行失败会直接抛错并记录 `support_workflow_runtime_error`。
- `langgraph.graph` 与 `langchain_core.tools` 测试已从 `pytest.importorskip` 改为硬导入，防止 mandatory dependency 缺失被跳过。

## 实际验证

```powershell
$env:UV_PROJECT_ENVIRONMENT='..\.tmp\uv-test-ai-service-pydantic-v2-langgraph-latest'
uv lock --python 3.12 --managed-python
uv run --python 3.12 --managed-python --extra dev python -m pytest tests\test_api_pydantic_v2_serialization.py tests\test_agent_workflow.py tests\test_support_agent_nodes.py tests\test_support_supervisor_graph.py tests\test_strategy_comparison_evaluator.py tests\test_ragas_bridge.py tests\test_ragas_testset_generation.py -q --basetemp ..\.tmp\pytest-pydantic-v2-langgraph-latest
```

结果：`50 passed`。

```powershell
mvn.cmd -f backend-java\pom.xml test "-Dtest=AgentServiceTest,AssistantTurnServiceTest"
```

结果：`2 tests, BUILD SUCCESS`。

说明：首次 pytest 使用系统临时目录时遇到 `C:\Users\admin\AppData\Local\Temp\pytest-of-admin` 权限错误，改用项目内 `--basetemp` 后通过。
