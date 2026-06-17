# 2026-06-17 企业售后技术支持知识库 Agent 编排

## 目标

完成企业售后技术支持知识库 Agent 的第一版后端可用编排，保持职责边界：

- FastAPI AI 服务负责 Agent 编排、RAG 策略选择、证据引用、分诊计划、诊断步骤和升级建议。
- Spring Boot 只做统一对外 API、DTO 桥接、会话/消息/评估历史持久化，不实现 RAG 或售后诊断逻辑。
- 前端后续只读取 Spring Boot `/api/*` 返回的结构化 `supportPlan`，不直连 AI 服务。

## 架构决策

- 复用现有 `StudyAgentWorkflow`，不新增第二套 runtime。当前 workflow 已经具备类 LangGraph 的节点式执行、trace step、RAG 调用、引用和学习闭环输出。
- 当 `agent_name` 包含 `support` / `after-sales` / `customer-success`，或 `variables.mode` / `variables.scenario` 为 `support` / `after-sales` / `technical-support` / `customer-support` 时进入售后支持模式。
- 售后支持模式默认把 `basic-rag` 路由到 `advanced-rag`，优先获得 query rewrite、multi-query、hybrid/rerank 和 parent-child 证据。
- 保留原有学习输出兼容性：`followUpQuestions`、`studyPlan`、`reviewCards` 仍返回；新增机器可读的 `supportPlan` 作为售后场景主结构。

## 编排节点

售后支持模式下的节点顺序：

```text
detect_support_mode
-> classify_question
-> select_rag_strategy
-> retrieve_and_generate
-> cite_sources
-> generate_support_plan
-> compose_support_response
-> generate_follow_up_questions
-> generate_study_plan
-> generate_review_cards
```

`supportPlan` 包含：

- `issueSummary`：售后案例摘要。
- `clarificationQuestions`：产品版本、部署环境、租户/区域、报错、告警码、trace id、变更窗口等澄清问题。
- `evidenceReferences`：最多 3 条引用证据，保留 title、chunk id 和 score。
- `diagnosticSteps`：顺序化排障步骤，包含动作、预期信号、证据提示和失败兜底。
- `escalation`：是否升级、严重度、原因、建议队列、工单摘要和工单字段。
- `riskNotes`：生产变更、数据安全、证据不足等风险提示。
- `nextActions`：下一步动作清单。

## 本次落地

- `ai-service/app/schemas/agent.py`
  - 新增 `DiagnosticStep`、`EscalationRecommendation`、`SupportPlan`。
- `ai-service/app/agents/workflow.py`
  - 新增售后模式识别、中文分诊计划、中文输出组合、严重度判断、证据引用摘要。
- `ai-service/app/services/agent_service.py`
  - 将 `support_plan` 写入 response 和 trace attributes。
- `backend-java/src/main/java/com/example/agentknowledge/client/dto/AiAgentInvokeResponse.java`
  - 对齐 AI 服务 snake_case `support_plan` 契约。
- `backend-java/src/main/java/com/example/agentknowledge/dto/agent/AgentInvokeResponse.java`
  - 对外暴露 camelCase `supportPlan`。
- `backend-java/src/main/java/com/example/agentknowledge/service/AgentService.java`
  - 映射支持计划、诊断步骤和升级建议。
- `backend-java/src/main/java/com/example/agentknowledge/dto/chat/AssistantTurnResponse.java`
  - Chat assistant-turn 返回 `supportPlan`。
- `backend-java/src/main/java/com/example/agentknowledge/service/AssistantTurnService.java`
  - 透传 `supportPlan`。
- 测试覆盖：
  - AI 服务支持模式 workflow。
  - Java AgentService DTO 映射。
  - AssistantTurn / weak-point 旧流程兼容。

## 验证

```powershell
cd ai-service
.\.venv\bin\python.exe -m pytest tests\test_agent_workflow.py -q --basetemp ..\.tmp\pytest-agent
```

```powershell
mvn.cmd -f backend-java\pom.xml test "-Dtest=AgentServiceTest,AssistantTurnServiceTest,WeakPointPracticeServiceTest"
```

## 剩余风险

- 目前售后分诊计划仍是规则化编排 + RAG 证据组合，尚未引入专门的 LLM 结构化 planner。
- Java 已透传结构化字段，但前端展示会在后续前端模块中补齐。
- 工单系统尚未接入；当前只返回 `ticketFields`，后续可接入 Jira/飞书/企业微信或内部工单 API。
