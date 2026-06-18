# Support Supervisor 多 Agent 工作流 Review Prompt

## 背景

本次变更按 `docs/plans/2026-06-18-support-supervisor-multi-agent-workflow.md` 实现售后技术支持 Agent 的受控 Supervisor 第一版。主服务不引入 LangGraph 新依赖，先以本地显式状态图拆分 7 个专业节点，保持 FastAPI / Pydantic v1 兼容。

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
- `ai-service/app/services/agent_service.py`
- `ai-service/tests/test_agent_workflow.py`

## 审查问题

1. 售后请求是否稳定路由到 `SupportSupervisorWorkflow`，普通学习 Agent 是否仍走旧 `StudyAgentWorkflow`。
2. 澄清信息不足时是否会提前返回，不执行检索和诊断。
3. 检索、代码/日志分析、诊断、风险审查、工单升级、评估审查节点是否都能写入 `workflowSteps` 和 trace。
4. 风险审查和评估审查是否是强制闸门，是否存在被跳过的路径。
5. `supportPlan` 是否保持现有 Java / React 兼容字段。
6. 是否有生产变更、数据安全、证据不足场景下给出确定性结论的风险。
7. 是否引入了不必要的新依赖、数据库迁移或 Spring Boot 诊断逻辑。

## 已执行验证

- `ai-service\.venv\bin\python.exe -m compileall -q ai-service\app\agents ai-service\app\services\agent_service.py`
- `ai-service\.venv\bin\python.exe -m pytest ai-service\tests\test_agent_workflow.py ai-service\tests\test_strategy_comparison_evaluator.py -q --basetemp .tmp\pytest-agent-wide -o cache_dir=.tmp\pytest-cache-agent-wide`
- `mvn.cmd -f backend-java\pom.xml test "-Dtest=AgentServiceTest,AssistantTurnServiceTest"`

## 已知说明

- 本次没有引入真实 LangGraph runtime，按计划先完成本地状态图和节点拆分。
- 工单升级 Agent 当前只生成草稿字段，不调用外部工单系统。
- 代码/日志分析工具 Agent 当前基于用户输入中的日志、错误码和 trace id 做规则识别，不连接真实日志平台。
## 2026-06-18 追加审查重点

- 真实 UTF-8 中文输入必须命中售后路由、严重度、影响范围、日志信号和危险动作识别，例如“客户 P1 大面积不可用，无法登录控制台，生产环境，日志显示 HTTP 504”。
- 风险审查必须同时扫描用户输入、RAG 原始回答、诊断步骤和最终草稿，防止知识库答案绕过风险门禁给出“直接重启 / 删除 / 回滚 / 配置”类建议。
- 评估审查必须审查已经生成的草稿回答；无 citation 即使已经生成升级工单，也应进入待人工复核，而不是直接 passed。
- 澄清提前返回路径也必须写入一致的 support trace 属性，包括 `support_evaluation_passed=None` 和 `support_evaluation_skipped_reason=needs_clarification`。

追加验证：

- `ai-service\.venv\bin\python.exe -m pytest ai-service\tests\test_agent_workflow.py ai-service\tests\test_support_agent_nodes.py ai-service\tests\test_strategy_comparison_evaluator.py -q --basetemp .tmp\pytest-support-agent -o cache_dir=.tmp\pytest-cache-support-agent`
