# 2026-06-17 企业售后技术支持知识库 Agent Review Prompt

请重点审查本次售后技术支持 Agent 编排：

- RAG / Agent 编排是否仍在 `ai-service`，Spring Boot 是否只做 DTO 桥接和持久化边界。
- `supportPlan` 字段是否足以支撑企业售后场景：澄清问题、证据引用、诊断步骤、升级建议、风险提示和下一步动作。
- 支持模式识别是否过宽或过窄，是否会误伤普通学习问答。
- 默认把售后场景路由到 `advanced-rag` 是否合理，显式非 basic 策略是否被保留。
- 中文输出是否可读，是否仍有不必要英文面向用户暴露。
- 升级建议是否对无证据、高严重度、生产变更、敏感信息等风险有足够保护。
- Java DTO 映射是否完整保留 `support_plan`，旧 assistant-turn / weak-point 流程是否保持兼容。

验证命令：

```powershell
cd ai-service
.\.venv\bin\python.exe -m pytest tests\test_agent_workflow.py -q --basetemp ..\.tmp\pytest-agent
```

```powershell
mvn.cmd -f backend-java\pom.xml test "-Dtest=AgentServiceTest,AssistantTurnServiceTest,WeakPointPracticeServiceTest"
```
