# 当前交接状态
更新时间：2026-06-08

## 当前正在做什么

当前正在按用户要求执行两条主线：历史英文文档全文中文化已完成，并同步 `PROJECT_CONTEXT.md` 与本文件，准备先做 docs-only 提交；随后继续验证并提交 RAG 检索选项 UI / assistant-turn `retrievalOptions` 透传改动。

## 当前项目完成度

- Phase 2 知识库 CRUD、文档上传 / 列表 / 详情 / 删除、Word `.docx` 解析与 MinerU PDF 解析已有工程闭环。
- Phase 3 基础 RAG 已打通 Spring Boot -> FastAPI -> PostgreSQL 的本地链路。
- Phase 4 Advanced RAG 已覆盖 hybrid-rerank、metadata-filter、parent-child、query rewrite、multi-query、rerank、上下文压缩、可配置混合检索权重与 LLM 查询转换回退。
- Phase 5 Agent 已覆盖问题分类、策略选择、assistant-turn、追问、学习计划、复习卡片和薄弱点学习闭环。
- Phase 6 GraphRAG 已覆盖实体 / 关系抽取、图谱事实持久化、遍历检索、图谱指标评估和前端查看入口。
- Phase 7 RAG 实验评估已覆盖实验 CRUD、持久化 run 评估、评估历史、汇总接口、对比页和结构化评估用例。

## 当前未提交工作

- 文档：历史 `docs/plans/`、`docs/reviews/`、`docs/experiments/`、`docs/testing/failures/` 已完成全文中文化；`PROJECT_CONTEXT.md`、`docs/handoff/CURRENT_STATE.md`、`docs/testing/strategy.md` 已同步为中文当前状态。
- AI 服务：Agent 工作流在 `retrieve_and_generate` 步骤暴露 `retrieval_options_enabled` 与 `retrieval_option_keys`。
- Spring Boot：assistant-turn / Agent bridge 新增 `retrievalOptions` 透传，仍不实现 RAG 逻辑。
- 前端：聊天页新增混合检索预设与 LLM 查询转换开关，Pinia 状态层生成 `retrievalOptions`。
- smoke：assistant-turn 请求新增 `retrievalOptions` 并断言 Agent 工作流收到该配置。
- `opencode.json` 是未跟踪文件，不纳入暂存、提交或推送。

## 已通过的近期验证

- AI 定向测试：`.\.venv\bin\python.exe -m pytest tests/test_agent_workflow.py tests/test_advanced_rag_strategy.py -q`，15 个测试通过。
- Spring 定向测试：`mvn.cmd test "-Dtest=AgentServiceTest,AssistantTurnServiceTest"`，2 个测试通过；沙箱内 Maven 访问本地 `maven-repo` jar 可能被拒，必要时使用非沙箱运行。
- 前端：`npm.cmd --prefix frontend run typecheck` 与 `npm.cmd --prefix frontend run build` 已通过。
- 语法：`python -m py_compile smoke_test.py` 已通过。

## 待重新验证

- 非 Docker 全链路：`powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1` 上次被用户中断，需要在文档提交后重新运行。
- 文档质量门禁：`git diff --check` 与英文模板词扫描需要在 docs-only 提交前重新运行。

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
