# FastAPI / Pydantic v2 / LangGraph 升级 Review Prompt

## 背景

本次变更按 `docs/plans/2026-06-18-fastapi-pydantic-v2-langgraph-upgrade.md` 完成 AI 服务版本升级。升级目标为：

- `fastapi==0.137.2`
- `pydantic==2.13.4`
- `pydantic-settings==2.14.1`
- `langchain==1.3.9`
- `langchain-core==1.4.7`
- `langgraph==1.2.5`
- `uvicorn==0.49.0`

## 重点审查范围

- `ai-service/pyproject.toml`
- `ai-service/uv.lock`
- `ai-service/app/core/pydantic_compat.py`
- `ai-service/app/agents/graphs/support_supervisor.py`
- `ai-service/app/agents/runnables/support_nodes.py`
- `ai-service/app/agents/tools/support_langchain_tools.py`
- `ai-service/app/rag/evaluators/ragas_bridge.py`
- `ai-service/app/rag/evaluators/testset_generation.py`
- `ai-service/tests/test_api_pydantic_v2_serialization.py`
- `ai-service/tests/test_support_supervisor_graph.py`
- `ai-service/tests/test_support_agent_nodes.py`
- `ai-service/tests/test_ragas_bridge.py`

## 审查问题

1. FastAPI / Pydantic v2 下 `/ai/health`、`/ai/rag/evaluate` 等响应是否能正确序列化 datetime、Enum、嵌套 trace 和 `dict[str, object]`。
2. Pydantic 模型输出是否统一通过 `model_to_dict()`，需要复制模型时是否通过 `model_copy_update()`，避免继续依赖 v1 `.dict()` / `.copy(update=...)` 热路径。
3. RAGAS 仍应保持可选懒加载，不应在 FastAPI 服务启动或普通评估路径中强制 import RAGAS。
4. Support Supervisor 在 LangGraph 1.x 下是否真实执行 `StateGraph.compile().ainvoke(...)`，且返回 `{"state": SupportAgentState}`。
5. `AI_AGENT_SUPPORT_WORKFLOW_RUNTIME=auto` 是否只在依赖不可用时回落本地 runtime；图构建失败和执行失败不得静默 fallback。
6. `langgraph.graph` 与 `langchain_core.tools` 作为 mandatory dependencies 是否有硬导入测试，避免 CI 中缺依赖却 skip。
7. Spring Boot 桥接 DTO 是否仍能透传 `supportPlan`、`workflowSteps`、trace status 和 RAG trace。

## 多 Agent 审查结论

- 依赖侦察 Agent 确认最新稳定版本组合，并建议同步升级 `uvicorn==0.49.0`。
- Pydantic 迁移扫描 Agent 指出 `.copy(update=...)`、HTTP response serialization 和 JSON-safe trace payload 是主要风险；本次已补兼容 helper 和 HTTP 序列化测试。
- 代码审查 Agent 指出 `auto` fallback 可能掩盖 LangGraph 构建失败，以及真实 LangGraph / StructuredTool 测试不应 `importorskip`；本次已修复为构建失败直接抛错、mandatory dependency 硬导入。

## 已执行验证

```powershell
$env:UV_PROJECT_ENVIRONMENT='..\.tmp\uv-test-ai-service-pydantic-v2-langgraph-latest'
uv lock --python 3.12 --managed-python
uv run --python 3.12 --managed-python --extra dev python -m pytest tests\test_api_pydantic_v2_serialization.py tests\test_agent_workflow.py tests\test_support_agent_nodes.py tests\test_support_supervisor_graph.py tests\test_strategy_comparison_evaluator.py tests\test_ragas_bridge.py tests\test_ragas_testset_generation.py -q --basetemp ..\.tmp\pytest-pydantic-v2-langgraph-latest
mvn.cmd -f backend-java\pom.xml test "-Dtest=AgentServiceTest,AssistantTurnServiceTest"
```

结果：

- AI 服务重点测试 `50 passed`。
- Java 桥接测试 `2 tests, BUILD SUCCESS`。

## 已知说明

- 首次 pytest 使用系统临时目录时遇到 `C:\Users\admin\AppData\Local\Temp\pytest-of-admin` 权限错误，改用项目内 `--basetemp ..\.tmp\pytest-pydantic-v2-langgraph-latest` 后通过。
- pytest cache 目录在本机存在权限 warning，不影响测试断言；不建议为了这个警告改业务代码。
