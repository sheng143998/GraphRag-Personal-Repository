# Support Supervisor 多 Agent 工作流 Review Prompt

## 背景

本次变更按 `docs/plans/2026-06-18-support-supervisor-multi-agent-workflow.md` 实现售后技术支持 Agent 的受控 Supervisor，并继续引入兼容 `FastAPI 0.95.2 + Pydantic 1.10.26` 的 `langgraph==0.1.5` 与 `langchain-core==0.2.8`。默认 `AI_AGENT_SUPPORT_WORKFLOW_RUNTIME=auto`，依赖可用时走真实 LangGraph `StateGraph.compile().ainvoke(...)`，依赖不可用时可观测回落到本地 runtime。

## 重点审查范围

- `ai-service/app/agents/states/support_state.py`
- `ai-service/app/agents/graphs/support_supervisor.py`
- `ai-service/app/agents/nodes/clarification_agent.py`
- `ai-service/app/agents/nodes/retrieval_agent.py`
- `ai-service/app/agents/nodes/code_log_tool_agent.py`
- `ai-service/app/agents/nodes/diagnosis_agent.py`
- `ai-service/app/agents/nodes/risk_review_agent.py`
- `ai-service/app/agents/nodes/escalation_agent.py`
- `ai-service/app/agents/nodes/evaluation_review_agent.py`
- `ai-service/app/agents/tools/log_pattern_tools.py`
- `ai-service/app/agents/tools/support_langchain_tools.py`
- `ai-service/app/agents/runnables/support_nodes.py`
- `ai-service/app/services/agent_service.py`
- `ai-service/tests/test_agent_workflow.py`
- `ai-service/tests/test_support_supervisor_graph.py`

## 审查问题

1. 售后请求是否稳定路由到 `SupportSupervisorWorkflow`，普通学习 Agent 是否仍走旧 `StudyAgentWorkflow`。
2. 澄清信息不足时是否会提前返回，不执行检索和诊断。
3. 检索、代码/日志分析、诊断、风险审查、工单升级、评估审查节点是否都能写入 `workflowSteps` 和 trace。
4. 风险审查和评估审查是否是强制闸门，是否存在被跳过的路径。
5. `supportPlan` 是否保持现有 Java / React 兼容字段。
6. 是否有生产变更、数据安全、证据不足场景下给出确定性结论的风险。
7. `langgraph==0.1.5` / `langchain-core==0.2.8` 是否与当前 Pydantic v1 兼容，是否避免升级 FastAPI/Pydantic 主基座。
8. `AI_AGENT_SUPPORT_WORKFLOW_RUNTIME=langgraph` 显式模式是否在依赖缺失或执行失败时直接失败，而不是静默伪装成功。
9. LangGraph runtime 与 local runtime 是否共享同一批 `_node_*` 方法，避免逻辑漂移。
10. `auto` 模式是否只在依赖缺失或图构建前失败时回落；图执行期失败不得复用已变更 state 重跑 local。
11. 是否引入了不必要的数据库迁移或 Spring Boot 诊断逻辑。

## 已执行验证

- `ai-service\.venv\bin\python.exe -m compileall -q ai-service\app\agents ai-service\app\services\agent_service.py`
- `ai-service\.venv\bin\python.exe -m pytest ai-service\tests\test_agent_workflow.py ai-service\tests\test_strategy_comparison_evaluator.py -q --basetemp .tmp\pytest-agent-wide -o cache_dir=.tmp\pytest-cache-agent-wide`
- `mvn.cmd -f backend-java\pom.xml test "-Dtest=AgentServiceTest,AssistantTurnServiceTest"`

## 已知说明

- 当前默认热路径为 `AI_AGENT_SUPPORT_WORKFLOW_RUNTIME=auto`：标准环境安装依赖后会走真实 LangGraph；依赖不可用时可观测回落到本地 runtime。
- 当前项目旧 `.venv` 是 Mingw/MSYS Python，直接安装 LangChain Core 依赖链可能在 `orjson` 构建处失败；本轮使用 uv managed Python 3.12 完成锁文件刷新和测试。
- 工单升级 Agent 当前只生成草稿字段，不调用外部工单系统。
- 代码/日志分析工具 Agent 当前基于用户输入中的日志、错误码和 trace id 做规则识别，不连接真实日志平台。
## 2026-06-18 追加审查重点

- 真实 UTF-8 中文输入必须命中售后路由、严重度、影响范围、日志信号和危险动作识别，例如“客户 P1 大面积不可用，无法登录控制台，生产环境，日志显示 HTTP 504”。
- 风险审查必须同时扫描用户输入、RAG 原始回答、诊断步骤和最终草稿，防止知识库答案绕过风险门禁给出“直接重启 / 删除 / 回滚 / 配置”类建议。
- 评估审查必须审查已经生成的草稿回答；无 citation 即使已经生成升级工单，也应进入待人工复核，而不是直接 passed。
- 澄清提前返回路径也必须写入一致的 support trace 属性，包括 `support_evaluation_passed=None` 和 `support_evaluation_skipped_reason=needs_clarification`。

追加验证：

- `ai-service\.venv\bin\python.exe -m pytest ai-service\tests\test_agent_workflow.py ai-service\tests\test_support_agent_nodes.py ai-service\tests\test_strategy_comparison_evaluator.py -q --basetemp .tmp\pytest-support-agent -o cache_dir=.tmp\pytest-cache-support-agent`

## 2026-06-18 二次开发追加审查重点

- `SupportSupervisorWorkflow` 是否只维护一套节点逻辑，本地 runtime 和可选 LangGraph runtime 是否共享同一批 `_node_*` 方法。
- `needs_clarification` 是否是唯一允许跳过后续 gates 的终态；其它终态是否都写入并完成 `risk_review_agent` 和 `evaluation_review_agent`。
- `workflow_runtime`、`workflow_status`、`required_gates`、`completed_gates`、`skipped_gates`、`final_status` 是否稳定写入 trace 顶层属性。
- `AgentService` 将 trace status 设置为 `needs_review` / `needs_clarification` 是否会影响 Java 桥接、前端展示或历史查询。
- `StudyAgentWorkflow` 直接收到 support 请求时抛错是否会破坏非售后学习 Agent，是否仍由 `AgentService` 正确路由售后请求。
- `EvaluationReviewAgent` 移除 mojibake 兜底后，真实 UTF-8 中文仍应通过章节检查，乱码不应通过。
- 当前已在主依赖中声明兼容 Pydantic v1 的 LangGraph / LangChain Core 版本；后续如升级到 LangGraph / LangChain 当前版本线，必须先迁移 FastAPI / Pydantic v2 并跑全量 schema/API 测试。

二次开发验证：

```powershell
ai-service\.venv\bin\python.exe -m compileall -q ai-service\app\agents ai-service\app\services\agent_service.py
ai-service\.venv\bin\python.exe -m pytest ai-service\tests\test_agent_workflow.py ai-service\tests\test_support_agent_nodes.py ai-service\tests\test_support_supervisor_graph.py ai-service\tests\test_strategy_comparison_evaluator.py -q --basetemp .tmp\pytest-support-agent-full -o cache_dir=.tmp\pytest-cache-support-agent-full
mvn.cmd -f backend-java\pom.xml test "-Dtest=AgentServiceTest,AssistantTurnServiceTest"
```

三次开发验证：

```powershell
$env:UV_PROJECT_ENVIRONMENT='..\.tmp\uv-test-ai-service-langgraph'; uv run --python 3.12 --managed-python --extra dev python -m pytest tests\test_agent_workflow.py tests\test_support_agent_nodes.py tests\test_support_supervisor_graph.py tests\test_strategy_comparison_evaluator.py -q --basetemp ..\.tmp\pytest-support-agent-langgraph -o cache_dir=..\.tmp\pytest-cache-support-agent-langgraph
mvn.cmd -f backend-java\pom.xml test "-Dtest=AgentServiceTest,AssistantTurnServiceTest"
```
