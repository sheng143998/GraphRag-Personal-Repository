# 当前交接状态
更新时间：2026-06-09

## 当前正在做什么

当前正在按用户要求补齐后端接口调用可观测性：Spring Boot 已新增统一接口调用完成日志，并补充知识库创建 / 更新 / 删除操作成功日志，便于确认前端请求是否真正进入 Java 后端。

## 当前项目完成度

- Phase 2 知识库 CRUD、文档上传 / 列表 / 详情 / 删除、Word `.docx` 解析与 MinerU PDF 解析已有工程闭环。
- Phase 3 基础 RAG 已打通 Spring Boot -> FastAPI -> PostgreSQL 的本地链路。
- Phase 4 Advanced RAG 已覆盖 hybrid-rerank、metadata-filter、parent-child、query rewrite、multi-query、rerank、上下文压缩、可配置混合检索权重与 LLM 查询转换回退。
- Phase 5 Agent 已覆盖问题分类、策略选择、assistant-turn、追问、学习计划、复习卡片和薄弱点学习闭环。
- Phase 6 GraphRAG 已覆盖实体 / 关系抽取、图谱事实持久化、遍历检索、图谱指标评估和前端查看入口。
- Phase 7 RAG 实验评估已覆盖实验 CRUD、持久化 run 评估、评估历史、汇总接口、对比页和结构化评估用例。

## 当前未提交工作

- Spring Boot：`TraceIdFilter` 已记录每次接口调用完成日志，包括 method、path、status、durationMs 与 traceId。
- Spring Boot：`KnowledgeBaseService` 已记录知识库创建、更新、删除成功日志，方便观察 CRUD 操作是否落库。
- 文档：`PROJECT_CONTEXT.md`、`docs/handoff/CURRENT_STATE.md` 已同步到 2026-06-09 状态；新增接口调用日志计划与 review 提示文档。
- `opencode.json` 是未跟踪文件，不纳入暂存、提交或推送。

## 已通过的近期验证

- Spring Boot 编译：`mvn.cmd -q -DskipTests compile` 已通过。
- AI 定向测试：`.\.venv\bin\python.exe -m pytest tests/test_agent_workflow.py tests/test_advanced_rag_strategy.py -q`，15 个测试通过。
- Spring 定向测试：`mvn.cmd test "-Dtest=AgentServiceTest,AssistantTurnServiceTest"`，2 个测试通过；沙箱内 Maven 访问本地 `maven-repo` jar 可能被拒，必要时使用非沙箱运行。
- 前端：`npm.cmd --prefix frontend run typecheck` 与 `npm.cmd --prefix frontend run build` 已通过。
- 语法：`python -m py_compile smoke_test.py` 已通过。

## 待重新验证

- 非 Docker 全链路：`powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1` 已重新运行，147 项检查全部通过。
- 文档质量门禁：`git diff --check` 与英文模板词扫描已在 docs-only 提交前通过。

## 当前限制与后续方向

- `.env` 缺少模型配置时仍会 fallback 到 stub provider。
- OpenAI-compatible adapter 已有轻量重试，但限流、熔断和成本统计仍待补齐。
- 基于 LLM 的 GraphRAG 抽取仍待实现，并需要结构化 fallback。
- 历史 UI 英文文案仍需单独中文化整理。
---

## 2026-06-08 本地全链路验证更新

本轮已完成：

- 新增 `scripts/test-fullchain-local.ps1` 本地全链路自动化脚本。
- 新增离线 Advanced RAG 策略对比辅助代码与测试。
- 补充异步文档入库、RAG bridge 行为、前端构建与 smoke 相关验证。
- Advanced RAG 覆盖 query rewrite、multi-query、metadata filter、hybrid rerank、run detail 与 `rewrittenQuery` 持久化检查。

验证记录：

- AI 侧 pytest、后端 Maven 测试、前端类型检查 / 构建 与本地 smoke 脚本 均已在对应阶段跑通过。
- 后续如遇 Maven 本地仓库权限问题，需要使用非沙箱方式运行后端测试。

---

## 2026-06-08 Agent 与聊天学习闭环更新

本轮已完成：

- FastAPI Agent 支持问题分类、策略选择、RAG 执行、引用返回与工作流步骤。
- Spring Boot 新增 `/api/agent/invoke` 和 `/api/chat/{sessionId}/assistant-turn` 桥接能力。
- 前端聊天页使用 assistant-turn，并自动创建会话；浏览器请求仍只走 Spring Boot `/api/*`。
- Agent 已补齐追问问题、学习计划、复习卡片、薄弱点记录、薄弱点评估、排序、汇总、练习、自动评分、复习日程和队列控件。

当前剩余较大工作：

- 继续增强 Agent 的真实 LLM 编排与 GraphRAG 抽取能力。
- 对历史页面中的英文 UI 文案做独立中文化整理。

---

## 2026-06-08 GraphRAG 与图谱事实更新

本轮已完成：

- AI 服务新增确定性实体 / 关系抽取、GraphRAG 查询增强与图谱引用元数据。
- Spring Boot 通过 Flyway 管理图谱事实表，并提供 `GET /api/graph/facts` 查询接口。
- 前端新增 `/graph` 工作台页面查看实体和关系。
- 本地全链路脚本在数据库模式下运行 AI 服务，保证 AI 入库图谱事实可被 Spring Boot 读取。
- GraphRAG evaluator notes 已加入实体覆盖、关系命中和扩展词命中指标，前端实验视图可展示图谱指标。

当前剩余较大工作：

- 增加基于 LLM 的 GraphRAG 抽取，并提供结构化回退。
- 丰富 GraphRAG 评估对比维度。

---

## 2026-06-08 RAG 实验评估体系更新

本轮已完成：

- Spring Boot 新增实验评估接口，基于持久化 RAG run 调用 FastAPI evaluator。
- 评估历史已持久化到 `rag_experiment_evaluations`，实验摘要同步更新。
- 新增最近 RAG run 列表、评估汇总接口、实验页 run 选择与评估历史展示。
- 新增评估对比页，支持策略 / 实验聚合、筛选、排行与最近评估明细。
- 结构化评估用例支持相关 chunk/document id、期望引用 chunk id 与 top-k，评分逻辑仍在 FastAPI。

当前剩余较大工作：

- 增加更多固定评估集和策略对比样例。
- 将评估结果用于自动化 RAG 参数优化建议。

---

## 2026-06-08 Advanced RAG 工程化更新

本轮已完成：

- Parent-Child 上下文优先使用真实 `parent_chunk_id`，并保留邻近窗口 fallback。
- 新增可选 `ParentChildChunker`，支持父块 / 子块入库，父块不参与检索和 embedding。
- 可配置混合检索支持 `retrieval_options` / `retrievalOptions`，并持久化 vector / keyword 权重元数据。
- Query-aware context compression 已记录压缩模式、压缩比例与上下文统计。
- GraphRAG evaluator 已融合图谱元数据指标。

当前剩余较大工作：

- 扩展 LLM-backed 查询转换与图谱抽取。
- 增加更多检索预设和前端可视化解释。

---

## 2026-06-08 LLM 查询转换回退更新

本轮已完成：

- 在 AI 服务中新增按请求开启的 LLM 查询改写与多查询扩展。
- 现有规则查询转换仍是默认路径。
- LLM 输出无效或不符合预期时，会回退到规则转换器。
- Advanced RAG trace 步骤会记录 provider 与 fallback 元数据。
- 全链路 smoke 脚本 脚本会在 stub LLM 回退场景下覆盖该可选路径。

当前剩余较大工作：

- 增加基于 LLM 的 GraphRAG 抽取，并提供结构化回退。
- 增加查询转换与混合检索预设的 UI 控件。

---

## 2026-06-08 RAG 检索选项 UI 更新

本轮已完成：

- 聊天页新增混合检索预设与 LLM 查询转换开关。
- Pinia 状态层会把控件状态转换为 `retrievalOptions` 并随 assistant-turn 请求发送。
- Spring Boot assistant-turn / Agent bridge 透传 `retrievalOptions` 到 FastAPI。
- FastAPI Agent 工作流在 `retrieve_and_generate` 步骤暴露检索选项可观测字段。
- smoke 脚本增加 assistant-turn 检索选项透传断言。

当前剩余较大工作：

- 增加基于 LLM 的 GraphRAG 抽取，并提供结构化回退。
- 对历史页面中遗留的英文 UI 文案做一次独立中文化整理。

---

## 2026-06-09 文档入库处理中卡住修复

- 当前已修复上传文档后前端长期显示“处理中”的主要原因：异步入库现在使用 `documentRepository.save(...)` 返回的真实文档 id，而不是保存前手动生成的 id。
- FastAPI 返回 `POST /ai/ingest/document 200 OK` 后，Spring Boot 异步处理器可以用同一个真实 `documentId` 找到文档记录并回写 `INDEXED`。
- `DocumentIngestProcessor` 已补充可读中文日志，覆盖异步开始、调用 AI、AI 返回、状态写回成功和失败写回。
- 已新增 `DocumentServiceTest` 防止 id 传递问题回归。
- 验证命令已通过：`mvn.cmd -q "-Dtest=DocumentServiceTest,DocumentIngestProcessorTest" test`。

---

## 2026-06-09 知识库对话 AI 调用超时修复

- 用户贴出的错误根因是 `SocketTimeoutException: Read timed out`，不是 FastAPI 返回格式异常；`application/octet-stream` 是超时后 Spring 读取响应时的外层表现。
- Spring Boot 默认 `AI_SERVICE_READ_TIMEOUT` 已从 30 秒调整为 180 秒，仍可通过环境变量覆盖。
- 前端聊天类请求已设置 180 秒超时，覆盖 assistant-turn、旧 RAG query 与薄弱点练习。
- `AiServiceClient.invokeAgent(...)` 已增加调用开始和成功返回日志，便于用 traceId 定位 Java -> FastAPI -> 模型服务耗时。
- 验证命令已通过：`mvn.cmd -q -DskipTests compile`、`npm.cmd --prefix frontend run typecheck`。

---

## 2026-06-09 FastAPI Agent 请求日志补齐

- 用户反馈 Java 后端有 `SocketTimeoutException: Read timed out`，但 Python 侧没有明显日志。
- 已在 FastAPI `app/main.py` 增加 HTTP middleware，所有 `/ai/*` 请求都会记录 start / completed / failed、path、status、durationMs 与 `X-Trace-Id`。
- 已在 `/ai/agent/invoke` 路由和 `AgentService` 增加 Agent 调用入口、完成、失败日志。
- Python 新增运行日志使用 ASCII 文案，避免 Windows 控制台编码导致日志乱码。
- 后续判断：如果 Java 再超时但 Python 没有 `AI request start`，说明请求没到当前 AI 服务；如果有 start 但没有 completed，继续看 Agent workflow / embedding / rerank / LLM 卡点。
- 验证命令已通过：`ai-service\.venv\bin\python.exe -m py_compile ai-service\app\main.py ai-service\app\api\routes\agent.py ai-service\app\services\agent_service.py`、`mvn.cmd -q -DskipTests compile`。

---

## 2026-06-09 统一数据库环境变量

- 用户明确要求数据库统一使用 `DB_URL=jdbc:postgresql://localhost:5432/agent_knowledge`、`DB_USERNAME=postgres`、`DB_PASSWORD=123456`。
- `.env` 已移除 `DATABASE_URL` / `AI_DATABASE_URL` 等额外数据库 URL，仅保留统一三项和 `AI_RAG_USE_DATABASE=true`。
- `.env.example`、Spring Boot 默认配置、AI 服务配置和 README 已同步为统一三项。
- AI 服务现在从 `DB_URL` / `DB_USERNAME` / `DB_PASSWORD` 推导 Python PostgreSQL URL，验证为 `PostgresDocumentRepository`。
- 修复后需重启 AI 服务；之前上传但只写到内存仓库的旧文档 chunks / embeddings 不会自动补回，需要重新上传或重建入库。

---

## 2026-06-09 全链路 TraceId 统一

- FastAPI `TraceBuilder` 现在复用 HTTP middleware 写入的 request trace id，Spring Boot 转发过来的 `X-Trace-Id` 会贯穿 Agent trace 与嵌套 RAG trace。
- FastAPI 直接被调用且没有 `X-Trace-Id` 时，middleware 会生成 trace id 并写回响应头。
- 前端知识库对话在一次提问、会话加载、薄弱点评估和薄弱点练习动作中复用同一个客户端 trace id，后续 `messages`、`weak-points`、`weak-points/summary` 刷新请求也会带同一个请求头。
- 验证已通过：`python -m compileall app`、`uv run --isolated --with pytest --with fastapi==0.95.2 --with pydantic==1.10.26 pytest tests/test_agent_workflow.py -q`、`npm run typecheck`、`mvn.cmd -q -DskipTests compile`。
- 关键文档：`docs/plans/2026-06-09-unified-trace-id.md`、`docs/reviews/2026-06-09-unified-trace-id-review-prompt.md` 与 `docs/testing/failures/2026-06-09-unified-trace-id-notes.md`。

---

## 2026-06-09 Agent RAG Run 持久化

- FastAPI Agent 响应新增 `rag_trace`，包含内部 RAG query 的 trace id、run id、attributes 和 steps。
- `rag_runs` 新增 `trace_attributes`、`trace_steps` JSONB 字段，Flyway 迁移为 `V202606092045__add_rag_run_trace_payload.sql`。
- Spring Boot assistant-turn 现在会通过 `RagRunRecorder` 把 Agent 内部 RAG run 落库，并保存 rewritten query、final context、answer、trace payload 与 top_k citation chunks。
- 新 trace 可通过 `rag_runs.trace_id = 'chat-...'` 查询到完整 RAG run；旧 trace 只能从 `chat_messages.citations` 还原 top_k，不能自动补出历史 `rag_runs`。
- 验证已通过：`python -m compileall app`、`uv run --isolated --with pytest --with fastapi==0.95.2 --with pydantic==1.10.26 pytest tests/test_agent_workflow.py -q`、`npm run typecheck`、`mvn.cmd -q -DskipTests compile`、`mvn.cmd -q "-Dtest=AgentServiceTest,AssistantTurnServiceTest,RagRunRecorderTest,RagServiceTest" test`。
- 关键文档：`docs/plans/2026-06-09-agent-rag-run-persistence.md`、`docs/reviews/2026-06-09-agent-rag-run-persistence-review-prompt.md` 与 `docs/testing/failures/2026-06-09-agent-rag-run-persistence-notes.md`。

---

## 2026-06-09 默认 LLM 查询改写更新

- Frontend 聊天页已删除 `enableLlmQueryTransform` 开关，用户不再需要手动开启查询转换。
- FastAPI `advanced-rag` 默认调用 LLM 执行 query rewrite 与 multi-query expansion，提示词要求从不同角度生成变体，并补充同义词、相关词、上位概念词和领域术语来增强语义覆盖。
- 规则型 query rewrite / multi-query 类已从查询转换器中移除；LLM 输出异常时仅回退到原始问题或已成功得到的 LLM 重写问题。
- Spring Boot 仍只负责透传业务请求和持久化 trace，不实现 RAG 查询转换逻辑。

---

## 2026-06-09 自然化 LLM 问题重写

- FastAPI `rewritten_query` prompt 已调整为输出自然、通顺、完整的主问题，避免关键词堆砌。
- 同义词、相关词、上位概念词和领域术语扩展由 `multi_query_expand` 的 query variants 承担。
- AI 测试新增 prompt 约束断言，确认主重写问题不再鼓励 standalone keyword list。
