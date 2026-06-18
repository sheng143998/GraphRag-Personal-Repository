# 智维售后 AgentOps 平台

智维售后 AgentOps 平台是一个面向企业售后技术支持知识库的 RAG + Agent 工程系统。项目采用 `React + Spring Boot + FastAPI + PostgreSQL/pgvector` 架构，把文档入库、混合检索、售后诊断 Agent、RAGAS 评测、人工审核、实验对比和可观测性串成完整闭环。

项目当前以 React 前端为主工作台，旧 Vue 前端已删除。浏览器只访问 Spring Boot `/api/*`，FastAPI AI 服务只作为内部 RAG / Agent / evaluator 服务使用。

## 个人知识库来源

本项目使用的个人知识库语料来自 [Obsidian AI 学习笔记库](https://github.com/HeWhenJay/obsidian-study-notes)。该笔记库整理了 AI Agent、RAG、LangChain、LangGraph、GraphRAG、多 Agent、MCP、A2A、Agent Skills、AutoGen、CrewAI 等学习笔记、图解和示例代码。

这个平台用于把上述笔记沉淀成本地可检索、可追溯、可评估的知识库：从 Obsidian Markdown 笔记入库，到 RAG/GraphRAG 检索、引用来源展示、问答生成、售后诊断和评测闭环。需要阅读原始笔记内容时，请访问笔记仓库；需要体验检索问答链路时，请运行本项目。

## 当前状态

- 前端：React 18 + TypeScript + Vite，覆盖售后问答、文档入库、知识库、实验评测、图谱、反馈和设置页面。
- Java 后端：Spring Boot 统一暴露 `/api/*`，负责业务 CRUD、数据库迁移、RAG run 持久化、评测集管理、批量评测编排和 AI 服务桥接。
- Python AI 服务：FastAPI 暴露内部 `/ai/*`，负责文档解析、chunk、embedding、检索、重排、生成、Advanced RAG preset、GraphRAG、Support Supervisor Agent、RAGAS 和 evaluator。
- 数据库：PostgreSQL + pgvector，统一承载业务数据、文档 chunk、embedding、RAG run、retrieval results、评测集、评测历史和图谱事实。
- 评测平台：已支持评测集管理、单样本评估、批量跑同一批样本对比不同 RAG preset，并结构化记录 `recall@k`、`precision@k`、`MRR`、`citation_hit`、token、成本和分阶段耗时。
- AgentOps 路线图：已完成 Support Supervisor 与 RAGAS 半自动测评闭环；下一阶段重点补齐 Agent Flight Recorder、Tool Registry、MCP、Agent Memory、AgentEval、风险审批与知识运营控制面。

## 系统总览

```mermaid
flowchart LR
  User["客户 / 售后工程师 / 研发"] --> React["React AgentOps 控制台<br/>frontend-react"]
  React --> Api["Spring Boot 业务后端<br/>统一 /api/*"]
  Api --> DB[("PostgreSQL + pgvector<br/>业务数据 / 文档 / Chunk / 向量 / 评测 / trace")]
  Api --> AI["FastAPI AI 服务<br/>内部 /ai/*"]

  subgraph Runtime["AI Runtime"]
    RAG["Advanced RAG<br/>混合检索 / 重排 / 生成"]
    Supervisor["Support Supervisor<br/>LangGraph StateGraph"]
    Eval["RAGAS / Evaluator<br/>测评集 / 离线评分 / 报告回填"]
    Graph["GraphRAG<br/>实体 / 关系 / 图谱事实"]
  end

  subgraph AgentOps["AgentOps 扩展路线图"]
    Recorder["Agent Flight Recorder<br/>运行回放 / 工具调用 / 风险决策"]
    Tools["Tool Registry<br/>工具 schema / 权限 / 审计"]
    Memory["Agent Memory<br/>客户环境 / 历史故障 / 专家经验"]
    MCP["MCP Client / Server<br/>知识库 / 工单 / 日志 / 评测工具"]
    AgentEval["AgentEval<br/>行为 / 工具 / 记忆 / 风险评分"]
  end

  AI --> RAG
  AI --> Supervisor
  AI --> Eval
  AI --> Graph
  Supervisor --> RAG
  Supervisor --> Recorder
  Supervisor --> Tools
  Supervisor --> Memory
  Tools --> MCP
  Eval --> AgentEval
  RAG --> DB
  Supervisor --> DB
  Eval --> DB
  Graph --> DB
  Recorder --> DB
  Tools --> DB
  Memory --> DB
  MCP --> DB
  AgentEval --> DB
  Api --> React
```

- 前端只调用 Spring Boot `/api/*`，不直接调用 FastAPI。
- Spring Boot 只做业务、桥接和持久化，不实现 RAG / evaluator 算法。
- FastAPI 负责 RAG、Agent、GraphRAG、文档解析、检索生成和指标计算。
- 数据库变更必须通过 `backend-java/src/main/resources/db/migration/` 下的 Flyway 迁移脚本。

## 详细业务流程图

### 售后问题从提交到解决

```mermaid
flowchart TD
  A["客户报障 / 售后工程师输入问题"] --> B["React 售后问答工作台<br/>选择知识库、客户、产品版本、环境变量"]
  B --> C["Spring Boot 创建会话与 run 记录<br/>生成 traceId / 校验权限 / 透传上下文"]
  C --> D["FastAPI Support Supervisor<br/>初始化 SupportState"]

  D --> E{"关键信息是否完整"}
  E -->|缺少版本 / 环境 / 日志| F["澄清 Agent<br/>生成必须补充的问题"]
  F --> G["前端展示澄清问题<br/>用户补充信息"]
  G --> C

  E -->|信息足够| H["检索 Agent<br/>根据问题类型选择 RAG preset"]
  H --> I["混合检索<br/>向量检索 + 关键词检索 + rerank + parent-child 上下文"]
  I --> J{"是否包含日志 / 错误码 / traceId"}
  J -->|是| K["代码 / 日志分析工具 Agent<br/>抽取错误码、堆栈、配置项、时间线"]
  J -->|否| L["诊断 Agent<br/>基于证据生成原因假设"]
  K --> L

  L --> M["诊断方案<br/>根因假设 / 排查步骤 / 引用证据 / 下一步动作"]
  M --> N["风险审查 Agent<br/>检查危险操作、证据不足、不可执行步骤"]
  N --> O{"是否需要人工复核或升级"}

  O -->|高风险 / 缺证据| P["工单升级 Agent<br/>生成升级摘要、复现信息、所需日志、推荐负责人"]
  P --> Q["人工审核队列<br/>二线 / 研发确认"]
  Q --> R{"审核结果"}
  R -->|通过| S["输出待执行 supportPlan<br/>可带升级工单"]
  R -->|拒绝 / 退回| T["专家修订<br/>补充答案、证据或知识缺口"]

  O -->|风险可控| U["评估审查 Agent<br/>检查引用、完整性、SOP 可执行性"]
  U --> V{"评估是否通过"}
  V -->|通过| W["返回结构化 supportPlan<br/>结论 / 证据 / 步骤 / 风险 / 下一步"]
  V -->|不通过| Q

  S --> X["沉淀运行记录<br/>workflowSteps / citations / latency / token"]
  W --> X
  T --> Y["回流知识运营<br/>记忆、文档任务、测评样本候选"]
  X --> Y
```

### Support Supervisor 运行时编排

售后 Agent 不是单个提示词直出答案，而是由 `Support Supervisor` 统一编排多个职责明确的节点。Supervisor 负责维护状态、决定下一步节点、记录 `workflowSteps`，并最终产出结构化 `supportPlan`。

```mermaid
flowchart TD
  Start["START<br/>question + variables + chat context"] --> Init["初始化 SupportState<br/>runtime / required_gates / trace"]
  Init --> Clarify["clarification_node<br/>检查客户、产品、版本、环境、日志是否足够"]
  Clarify --> C1{"needs_clarification"}
  C1 -->|true| EndClarify["END: needs_clarification<br/>只返回澄清问题，允许跳过后续 gate"]

  C1 -->|false| Retrieve["retrieval_node<br/>检索知识库、相似经验、候选证据"]
  Retrieve --> EvidenceCheck{"证据是否足够"}
  EvidenceCheck -->|不足| WeakEvidence["标记 weak_evidence<br/>后续强制进入人工复核"]
  EvidenceCheck -->|足够| LogGate{"是否有日志 / 错误码 / trace"}

  WeakEvidence --> LogGate
  LogGate -->|有| LogNode["log_analysis_node<br/>提取错误码、堆栈、配置、时间线"]
  LogGate -->|无| Diagnose
  LogNode --> Diagnose["diagnosis_node<br/>生成根因假设、排查步骤和答案草稿"]

  Diagnose --> Risk["risk_review_node<br/>检查高风险命令、误导性建议、无证据结论"]
  Risk --> RiskGate{"risk_level"}
  RiskGate -->|high / blocked| Escalate["escalation_node<br/>生成升级工单草稿和交接材料"]
  RiskGate -->|low / medium| Eval["evaluation_review_node<br/>检查最终方案质量"]
  Escalate --> Eval

  Eval --> FinalGate{"final_status"}
  FinalGate -->|completed| Completed["END: completed<br/>supportPlan 可直接展示"]
  FinalGate -->|needs_review| Review["END: needs_review<br/>进入人工审核队列"]

  Init -.记录.-> Recorder["Flight Recorder<br/>规划中持久化 run / step / tool call"]
  Retrieve -.记录.-> Recorder
  LogNode -.记录.-> Recorder
  Diagnose -.记录.-> Recorder
  Risk -.记录.-> Recorder
  Eval -.记录.-> Recorder
```

```mermaid
flowchart LR
  State["SupportState"] --> Inputs["输入<br/>question / context / variables"]
  State --> Evidence["证据<br/>retrievalResults / citations"]
  State --> Tools["工具<br/>knowledge.search / log.parse / ticket.escalate"]
  State --> Diagnosis["诊断<br/>rootCauseHypotheses / diagnosticSteps"]
  State --> Safety["安全闸门<br/>riskFlags / escalationRequired"]
  State --> Eval["评估<br/>evidenceCoverage / answerQuality / reviewRequired"]
  State --> Output["输出<br/>supportPlan / workflowSteps / trace / candidateEvalCase"]
```

对应实现位置：

- `ai-service/app/agents/graphs/support_supervisor.py`：Supervisor 状态图入口与路由。
- `ai-service/app/agents/states/support_state.py`：跨节点共享状态。
- `ai-service/app/agents/nodes/`：澄清、检索、诊断、风险审查、工单升级、代码 / 日志分析、评估审查等节点。
- `ai-service/app/services/agent_service.py`：对外 Agent 调用入口，负责选择售后模式并返回 `supportPlan`。

### 文档入库与知识运营

```mermaid
flowchart TD
  A["React 文档中心<br/>单文件 / 多文件 / 文件夹上传"] --> B["Spring Boot DocumentController<br/>校验知识库、文件大小、相对路径"]
  B --> C["创建 documents 记录<br/>状态 PROCESSING"]
  C --> D{"入库调度模式"}
  D -->|local| E["Spring @Async 本地线程池"]
  D -->|rabbitmq| F["RabbitMQ 文档入库消息"]
  E --> G["调用 FastAPI /ai/ingest/document"]
  F --> G

  G --> H{"文件类型"}
  H -->|Markdown / TXT| I["保留标题层级与代码块"]
  H -->|DOCX| J["提取段落、标题、表格、嵌套表格"]
  H -->|PDF| K["MinerU 解析<br/>轮询 batch 结果 / 下载 markdown 或 zip"]
  H -->|Excel / CSV| L["结构化表格解析<br/>sheet / columns / row_range"]

  I --> M["动态 chunk 策略路由"]
  J --> M
  K --> M
  L --> M
  M --> N["recursive-overlap / parent-child / table-row-group / qna-pair / code-aware"]
  N --> O["生成 embedding<br/>写入 document_chunks / chunk_embeddings"]
  O --> P["更新文档状态<br/>INDEXED / FAILED + 错误原因"]
  P --> Q["知识库可检索"]

  Q --> R["质量扫描<br/>低质量 chunk / 空内容 / 弱 OCR / 缺元数据"]
  R --> S["知识缺口任务<br/>补文档、补 SOP、补错误码说明"]
  S --> T["可转为测评样本候选"]
```

### 测评集生成、人工审核与前端评测

```mermaid
flowchart TD
  A["选择知识库 / 文档 / chunk 范围"] --> B["生成测评集草稿<br/>rule / llm / ragas / auto"]
  B --> C{"生成模式"}
  C -->|rule| D["规则式草稿<br/>快速覆盖标题、摘要、关键句"]
  C -->|llm| E["LLM 复杂题型<br/>概念、排障、对比、操作步骤"]
  C -->|ragas| F["RAGAS TestsetGenerator<br/>生成问题、参考答案、上下文"]
  C -->|auto| G["优先 RAGAS / LLM<br/>失败回退 rule 并标记需审核"]

  D --> H["DRAFT JSON / CSV"]
  E --> H
  F --> H
  G --> H
  H --> I["React 实验页导入草稿"]
  I --> J["页面内人工审核<br/>编辑问题、标准答案、证据 chunk、备注、topK"]
  J --> K{"审核决定"}
  K -->|通过| L["APPROVED 样本<br/>进入评测集"]
  K -->|拒绝| M["REJECTED 样本<br/>保留原因，不参与评测"]
  K -->|待审| J

  L --> N["创建或选择实验"]
  N --> O["批量运行 RAG preset<br/>basic / hybrid-rerank / parent-child / graph-rag"]
  O --> P["Spring Boot 持久化 run / evaluation"]
  P --> Q["指标展示<br/>evidenceRecall / chunkRecall / documentRecall / precision / MRR / citation"]
  P --> R["导出 RAGAS JSONL"]
  R --> S["离线 RAGAS 评分"]
  S --> T["报告回填数据库<br/>ragasScores / metricNames / judge model"]
  T --> Q
  Q --> U["低分样本归因<br/>检索失败、证据缺失、回答幻觉、标准答案问题"]
  U --> V["生成知识缺口 / Golden trace / 回归集"]
```

### 工具调用、MCP 与审计链路

```mermaid
flowchart TD
  A["Supervisor 需要外部能力<br/>查知识、查工单、解析日志、跑评测"] --> B["Tool Router"]
  B --> C["Tool Registry<br/>工具名、schema、权限、风险等级、超时、重试策略"]
  C --> D{"工具类型"}
  D -->|local tool| E["本地工具<br/>knowledge.search / log.parse / case.searchSimilar"]
  D -->|MCP tool| F["MCP Client Adapter<br/>连接 knowledge-mcp / ticket-mcp / log-mcp / eval-mcp"]

  E --> G["执行工具并返回结构化结果"]
  F --> G
  G --> H["参数与结果脱敏"]
  H --> I["写入工具调用审计<br/>toolName / arguments / resultSummary / latency / error"]
  I --> J{"是否失败"}
  J -->|失败| K["fallback 策略<br/>降级检索、重试、人工复核"]
  J -->|成功| L["结果进入 SupportState"]
  K --> L
  L --> M["后续诊断 / 风险审查 / 评估审查"]
```

### Agent 记忆与专家经验沉淀

```mermaid
flowchart TD
  A["售后请求进入 Supervisor"] --> B["读取候选记忆<br/>客户环境、历史故障、专家经验"]
  B --> C["MemoryPolicy<br/>按客户、产品、版本、错误码、置信度过滤"]
  C --> D["诊断 Agent 使用相关记忆"]
  D --> E["最终 supportPlan"]
  E --> F{"问题是否解决 / 是否有专家修订"}
  F -->|未解决| G["不写长期记忆<br/>只记录失败 trace 和知识缺口"]
  F -->|已解决| H["生成经验记忆草稿<br/>故障现象、根因、解决步骤、适用版本"]
  H --> I["人工审核<br/>确认可复用、无敏感信息、证据充分"]
  I --> J{"审核结果"}
  J -->|通过| K["写入长期记忆 / 经验记忆"]
  J -->|拒绝| L["归档为不可复用案例"]
  K --> M["下次相似故障召回"]
```

### AgentOps 前端操作路径

```mermaid
flowchart LR
  A["智能体运维总览"] --> B["售后问答工作台<br/>处理当前问题"]
  A --> C["运行回放<br/>复盘一次 Agent 决策"]
  A --> D["工具与 MCP 中心<br/>查看工具健康度和审计"]
  A --> E["评测实验室<br/>测评集、批量评测、RAGAS 报告"]
  A --> F["人工审核队列<br/>高风险动作、低置信答案、样本审核"]
  A --> G["知识运营<br/>知识缺口、补文档任务、低质量 chunk"]
  C --> H["失败运行转测评样本"]
  C --> I["失败运行转知识缺口"]
  E --> G
  F --> G
  G --> B
```

## 本地依赖

- Node.js 24 或兼容版本
- Java 21
- Maven 3.9+
- Python 3.12
- PostgreSQL + pgvector
- Docker / Docker Compose，可用于启动本地依赖

## 快速开始

1. 准备环境变量：

```powershell
Copy-Item .env.example .env
```

2. 启动基础依赖：

```powershell
.\scripts\dev-start.ps1
```

3. 启动 Java 后端：

```powershell
cd backend-java
mvn spring-boot:run
```

4. 启动 Python AI 服务：

```powershell
cd ai-service
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

如果本机虚拟环境是 `bin` 目录，可改用：

```powershell
.\.venv\bin\python.exe -m uvicorn app.main:app --reload --port 8001
```

5. 启动 React 前端：

```powershell
npm.cmd --prefix frontend-react install
npm.cmd --prefix frontend-react run dev
```

## 常用验证

```powershell
npm.cmd --prefix frontend-react run typecheck
npm.cmd --prefix frontend-react run build
mvn.cmd -f backend-java\pom.xml test
.\ai-service\.venv\bin\pytest.exe ai-service\tests
```

## 模块说明

- `frontend-react/`：React 前端主工作台，负责知识库、文档入库、售后问答、实验评测、图谱、反馈和设置交互。
- `backend-java/`：Spring Boot 业务后端，负责 `/api/*`、Flyway 迁移、业务持久化、RAG run 记录和 AI 服务桥接。
- `ai-service/`：FastAPI AI 服务，负责 `/ai/*`、文档解析、Advanced RAG、GraphRAG、Support Supervisor Agent、RAGAS、evaluator 和 trace。
- `infra/`：本地基础设施配置，当前重点是 PostgreSQL + pgvector。
- `scripts/`：本地依赖启动、停止、数据库重置和全链路 smoke 辅助脚本。
- `docs/`：计划、交接、review prompt、失败复盘和架构说明。

## 模块流程图

### React 前端工作台

```mermaid
flowchart TD
  Route["路由入口<br/>src/app/router.tsx"] --> Layout["工作台布局<br/>WorkbenchLayout"]
  Layout --> Chat["售后问答页<br/>ChatPage"]
  Layout --> Docs["文档中心<br/>DocumentCenter"]
  Layout --> Experiments["评测实验页<br/>ExperimentsWorkspace"]
  Layout --> Knowledge["知识库 / 图谱 / 设置"]
  Chat --> ApiClient["统一 API Client<br/>src/api/*"]
  Docs --> ApiClient
  Experiments --> ApiClient
  Knowledge --> ApiClient
  ApiClient --> Spring["Spring Boot /api/*"]
  Spring --> ViewState["页面状态<br/>加载 / 空态 / 错误 / 结果展示"]
  ViewState --> Layout
```

### Spring Boot 业务后端

```mermaid
flowchart TD
  Controller["Controller<br/>/api/*"] --> Service["Service<br/>业务编排"]
  Service --> Repository["Repository<br/>JPA / 查询"]
  Service --> AiClient["AiServiceClient<br/>调用 /ai/*"]
  Repository --> DB[("PostgreSQL<br/>业务表 / 评测表 / RAG run")]
  AiClient --> FastAPI["FastAPI AI 服务"]
  FastAPI --> Service
  Service --> Response["统一响应<br/>ApiResponse + traceId"]
  Response --> Frontend["React 前端"]
  Migration["Flyway migration"] --> DB
```

### FastAPI AI 服务

```mermaid
flowchart TD
  InternalApi["内部接口<br/>/ai/*"] --> Ingest["文档解析与入库<br/>parser / chunker / embedding"]
  InternalApi --> Rag["RAG 查询<br/>retrieve / rerank / generate"]
  InternalApi --> Agent["Support Supervisor<br/>LangGraph StateGraph"]
  InternalApi --> Eval["RAGAS / evaluator<br/>生成测评集 / 离线评估"]
  Ingest --> DB[("PostgreSQL + pgvector")]
  Rag --> DB
  Agent --> Rag
  Agent --> Nodes["Agent 节点<br/>澄清 / 检索 / 日志分析 / 诊断 / 风险 / 升级 / 评审"]
  Eval --> DB
  Nodes --> Trace["trace / workflowSteps / supportPlan"]
  Rag --> Trace
  Eval --> Trace
  Trace --> Spring["Spring Boot 桥接层"]
```

### 数据与基础设施

```mermaid
flowchart TD
  Compose["Docker Compose / infra"] --> Postgres["PostgreSQL"]
  Postgres --> Pgvector["pgvector 扩展"]
  Flyway["Spring Boot Flyway"] --> Schema["统一数据库迁移"]
  Schema --> Tables["业务表 / 文档表 / Chunk / 向量 / 评测表 / 图谱事实"]
  Pgvector --> Tables
  Tables --> Query["RAG 检索与业务查询"]
  Query --> Backend["Spring Boot / FastAPI"]
```

### 脚本与文档

```mermaid
flowchart TD
  Scripts["scripts/"] --> DevStart["启动本地依赖"]
  Scripts --> Testset["生成 / 审核 / 运行 RAGAS 测评"]
  Scripts --> Smoke["smoke / reset / 辅助验证"]
  Docs["docs/"] --> Plans["计划文档"]
  Docs --> Reviews["代码审查 prompt"]
  Docs --> Handoff["当前交接状态"]
  Plans --> Work["功能开发"]
  Reviews --> Work
  Handoff --> Work
  Work --> Context["PROJECT_CONTEXT.md"]
```

## 当前重点文档

- 项目上下文：[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)
- 当前交接：[docs/handoff/CURRENT_STATE.md](docs/handoff/CURRENT_STATE.md)
- API 设计：[docs/architecture/api-design.md](docs/architecture/api-design.md)
- 数据库设计：[docs/architecture/database-design.md](docs/architecture/database-design.md)
- 售后 Agent 架构：[docs/plans/2026-06-18-support-supervisor-multi-agent-workflow.md](docs/plans/2026-06-18-support-supervisor-multi-agent-workflow.md)
- RAGAS 测评闭环：[docs/plans/2026-06-18-ragas-testset-generation-report-review-flow.md](docs/plans/2026-06-18-ragas-testset-generation-report-review-flow.md)
- AgentOps 生产级升级路线图：[docs/plans/2026-06-18-agentops-production-upgrade-roadmap.md](docs/plans/2026-06-18-agentops-production-upgrade-roadmap.md)

## 开发约定

- 每次开发前先看 `PROJECT_CONTEXT.md` 和 `docs/handoff/CURRENT_STATE.md`。
- Prompt 统一放在 `ai-service/app/prompts/`。
- 前端 API 调用统一放在 `frontend-react/src/api/`。
- Java DTO / Entity / migration / 前端类型 / Python schema 需要保持字段契约一致。
- 不提交真实 API key、数据库密码、模型 token 或完整认证头。
