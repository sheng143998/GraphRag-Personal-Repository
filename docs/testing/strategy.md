# 测试策略

测试分为四类：

- 单元测试：隔离模块，不依赖外部服务。
- 外部依赖单元测试：依赖 PostgreSQL、Redis、模型服务等，但不启动完整应用。
- 集成测试：运行在真实部署环境上，不做 mock。
- Playwright E2E 测试：覆盖前后端完整交互。

## 第一阶段测试重点

- Python：chunker、parser、prompt builder、retriever adapter、trace schema。
- Java：service 规则、controller contract、AI client 错误处理、Flyway migration。
- 前端：API client、上传表单、聊天页面、引用来源展示。
- 数据库：pgvector extension、向量索引、metadata filter。

## 测试失败复盘

非显而易见或跨模块问题需要在 `docs/testing/failures/` 下记录：

- 问题现象
- 复现步骤
- 根因
- 修复方案
- 补充的回归测试
- 下次排查建议

## 2026-06-08 当前自动化验证

- 前端：`npm.cmd run typecheck`、`npm.cmd run build`。
- 后端：`mvn.cmd test`；当前 service 层覆盖 RAG bridge 持久化 / 失败场景，以及异步文档入库成功 / 失败场景。
- AI 服务：`.\.venv\bin\python.exe -m pytest`；当前覆盖 Basic RAG、Advanced RAG、OpenAI-compatible adapter 解析与离线策略对比指标。
- 本地全链路 smoke 脚本：`powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1 -SkipBuild`。
- 直接 smoke 脚本：`python smoke_test.py`；支持 `SMOKE_BASE_URL`、`SMOKE_AI_BASE_URL` 与 `SMOKE_TIMEOUT`。

## 2026-06-08 文档质量门禁

- 历史文档需要保持中文正文、中文标题和中文章节名；命令、API 路径、代码标识符、字段名、模型名和技术专有名词可以保留原样。
- 文档提交前运行 `git diff --check`，修复空白、行尾和 EOF 问题。
- 文档提交前使用 `rg` 扫描历史计划、审查、验证、评估、迭代完成记录等常见英文模板词，确认没有历史英文模板结构残留。
- `PROJECT_CONTEXT.md` 与 `docs/handoff/CURRENT_STATE.md` 必须同步当前完成度、未提交改动和待验证项。
- docs-only 提交只暂存 `PROJECT_CONTEXT.md` 与 `docs/**`，不得混入功能代码、构建产物或 `opencode.json`。

全链路 smoke 脚本 已将 RAG 查询失败视为硬失败，并包含 `advanced-rag` trace 断言：完成状态、引用存在、`rewrittenQuery` 已入库。

## 2026-06-08 Agent 工作流验证

- AI 侧 pytest 覆盖问题分类、自动策略选择、RAG 执行、引用与工作流 trace 元数据。
- 后端 Maven 测试覆盖 Spring Boot `/api/agent/invoke` bridge 的请求 / 响应映射。
- 本地全链路 smoke 脚本 覆盖 Spring Boot 到 FastAPI Agent 调用。

## 2026-06-08 GraphRAG 验证

- AI 侧 pytest 覆盖确定性的 GraphRAG 实体 / 关系抽取、图查询增强、trace 属性与引用图谱元数据。
- 前端类型检查 / 构建 验证工作台可选择 `GraphRAG` 策略。
- 本地全链路 smoke 脚本 覆盖 Spring Boot 到 FastAPI 的 `strategyName=graph-rag` 调用。

## 2026-06-08 GraphRAG 持久化验证

- 后端包中包含 Flyway 迁移 `V202606081300__create_graph_facts.sql`，本地 Spring Boot 启动时会执行。
- AI 侧 pytest 覆盖通过内存仓储读取持久化图谱事实。
- 全链路 smoke 脚本 覆盖图谱事实表与入库时图谱抽取。

## 2026-06-08 图谱事实查询验证

- 后端 Maven 测试包含 `GraphFactServiceTest`，覆盖实体过滤归一化、DTO 映射与 100 行查询限制。
- 前端类型检查 / 构建 覆盖新的 `/graph` 工作台页面与 `frontend/src/api/graph.ts`。
- 本地全链路脚本以数据库模式运行 AI 服务，使 AI 入库写入的图谱事实可被 Spring Boot 读取。
- 本地全链路 smoke 脚本 覆盖 `GET /api/graph/facts` 与 `GET /api/graph/facts?entity=GraphRAG`。

## 2026-06-08 GraphRAG 遍历检索验证

- AI 侧 pytest 覆盖 GraphRAG trace / 引用元数据中的一跳图扩展词与遍历关系。
- `smoke_test.py` 检查 Spring Boot RAG run 检索元数据中的 `graph_expansion_terms` 与 `graph_traversal_relationships`。

## 2026-06-08 GraphRAG 离线评估样例验证

- AI 侧 pytest 在固定图关系与扩展问题上对比 `advanced-rag` 与 `graph-rag`。
- 样例预期 GraphRAG 在实体 / 关系问题上提升 recall@k、precision@k、MRR 与 citation hit，且不依赖 Docker 或真实模型调用。

## 2026-06-08 助手轮次聊天流验证

- 后端 Maven 测试包含 `AssistantTurnServiceTest`，覆盖用户 / 助手消息持久化与 Agent 请求上下文传递。
- 前端类型检查 / 构建 覆盖 `sendAssistantTurn()` API 接线与聊天 store 流程。
- `smoke_test.py` 覆盖 `POST /api/chat/{sessionId}/assistant-turn`、助手工作流元数据、持久化消息与针对助手消息的反馈提交。

## 2026-06-08 Agent 追问问题验证

- AI 侧 pytest 覆盖 `generate_follow_up_questions` 工作流步骤、trace 属性与三个生成追问。
- 后端 Maven 测试覆盖 `follow_up_questions` 到 `followUpQuestions` 的 DTO 传播。
- 前端类型检查 / 构建 覆盖聊天工作台中的可点击追问。
- `smoke_test.py` 验证 assistant-turn 经 Spring Boot 返回至少三个非空 `followUpQuestions`。

## 2026-06-08 Agent 学习计划验证

- AI 侧 pytest 覆盖 `generate_study_plan` 工作流步骤、trace 属性与三个结构化学习步骤。
- 后端 Maven 测试覆盖 `study_plan` 到 `studyPlan` 的 DTO 传播。
- 前端类型检查 / 构建 覆盖聊天工作台学习计划面板。
- `smoke_test.py` 验证直接 Agent 与 assistant-turn 响应包含 `studyPlan`，且 trace 属性一致。

## 2026-06-08 Agent 复习卡片验证

- AI 侧 pytest 覆盖 `generate_review_cards` 工作流步骤、trace 属性与主动回忆卡片生成。
- 后端 Maven 测试覆盖 `review_cards` 到 `reviewCards` 的 DTO 传播。
- 前端类型检查 / 构建 覆盖聊天工作台复习卡片面板。
- `smoke_test.py` 验证直接 Agent 与 assistant-turn 响应包含至少两张 `reviewCards`，且 trace 问题一致。

## 2026-06-08 薄弱点记录验证

- 后端 Maven 测试覆盖从复习卡片记录会话薄弱点，并通过 assistant-turn 响应传播。
- 前端类型检查 / 构建 覆盖薄弱点 API 类型、store 状态与聊天工作台面板。
- `smoke_test.py` 验证 assistant-turn 返回薄弱点，且 `GET /api/chat/{sessionId}/weak-points` 能读取持久化薄弱点。

## 2026-06-08 薄弱点状态评估验证

- 后端 Maven 测试覆盖 `MASTERED` / `NEEDS_REVIEW` 薄弱点状态更新。
- 前端类型检查 / 构建 覆盖聊天工作台中的薄弱点评估操作。
- `smoke_test.py` 验证 `PATCH /api/chat/{sessionId}/weak-points/{weakPointId}` 可将持久化薄弱点更新为 `MASTERED`。

## 2026-06-08 薄弱点优先级验证

- 后端 Maven 测试覆盖薄弱点列表排序契约。
- `smoke_test.py` 在标记掌握后重新拉取薄弱点，并断言 `NEEDS_REVIEW` 项仍排在前面。

## 2026-06-08 薄弱点进度汇总验证

- 后端 Maven 测试覆盖总数、待复习、已掌握、困难项、复习次数、完成率与下一项聚合。
- 前端类型检查 / 构建 覆盖 `fetchWeakPointSummary()`、Pinia 汇总状态与聊天工作台进度卡片。
- `smoke_test.py` 在标记掌握前后验证 `GET /api/chat/{sessionId}/weak-points/summary`。

## 2026-06-08 RAG 实验评估验证

- 后端 Maven 测试包含 `RagExperimentServiceTest`，覆盖持久化 run 查询、检索证据映射、FastAPI evaluator 请求构造、分数持久化、状态更新与 notes 追加。
- `smoke_test.py` 从持久化 Advanced RAG run 评估已创建实验，并验证 `COMPLETED` 状态、grounded score、retrieval score 与 evaluator notes。

## 2026-06-08 薄弱点练习流验证

- 后端 Maven 测试包含 `WeakPointPracticeServiceTest`，覆盖薄弱点 prompt 构造、assistant-turn 调用与 `weak-point-practice` variables。
- 前端类型检查 / 构建 覆盖 `practiceWeakPointTurn()` API 映射、Pinia 练习 action 与聊天页练习按钮接线。
- `smoke_test.py` 验证持久化薄弱点可触发练习轮次，并返回选中的薄弱点、助手消息、复习卡片与更新后的薄弱点。

## 2026-06-08 RAG 评估工作台验证

- 后端 Maven 测试覆盖最近 RAG run summary 映射与 limit 限制。
- 前端类型检查 / 构建 覆盖最近 run 加载、实验评估 API 映射与实验页 run 选择器。
- `smoke_test.py` 在实验评估前验证 `GET /api/rag/runs?limit=10` 包含已创建 run。

## 2026-06-08 RAG 评估历史验证

- 后端 Maven 测试覆盖事务化实验评估、evaluator 请求映射、分数持久化与 `rag_experiment_evaluations` 历史行创建。
- 前端类型检查 / 构建 覆盖 `ExperimentEvaluationHistory` 响应类型与实验页最近评估历史列表。
- `smoke_test.py` 验证 Advanced RAG 实验评估响应包含 `data.evaluation.runId`、非空 `data.history` 与非空 `data.experiment.evaluations`。

## 2026-06-08 RAG 评估对比看板验证

- 后端 Maven 测试验证评估历史响应包含 run 问题、策略、retriever、model、latency 与 run 创建时间。
- 前端类型检查 / 构建 覆盖最近历史看板、实验平均值、最新趋势标签与问题快照历史行。
- `smoke_test.py` 分别从 Advanced RAG 与 Basic RAG run 评估同一实验，并验证至少两条可对比历史。

## 2026-06-08 RAG 评估汇总接口验证

- 后端 Maven 测试验证 `RagExperimentService.summarizeEvaluations()` 返回最近数量、平均值、最佳实验与最近评估行。
- 前端类型检查 / 构建 覆盖 `fetchExperimentEvaluationSummary()`、Pinia 汇总状态、hydrate 加载与看板使用。
- `smoke_test.py` 在两次实验评估后验证 `GET /api/rag/experiment-evaluations/summary?limit=10`。

## 2026-06-08 RAG 评估器答案对齐验证

- AI 侧 pytest 覆盖相同引用集下 expected/generated answer 匹配与不匹配的得分差异。
- 确定性 evaluator 会将引用支持与答案对齐结合，避免仅因有引用就得到满分 grounded score。
- 后端 Maven 测试断言 Spring 会将 `expectedAnswer` 转发到 FastAPI evaluator 请求。

## 2026-06-08 RAG 评估对比页面验证

- 前端类型检查 / 构建 覆盖 `/experiments/comparison`、summary 复用、策略级聚合、实验级聚合与最近评估行。
- 页面复用 `GET /api/rag/experiment-evaluations/summary`；既有全链路 smoke 脚本 继续在 Advanced RAG 与 Basic RAG 评估后验证 API 契约。
- 前端类型检查 / 构建 同时覆盖对比页策略 / 实验筛选、筛选后聚合行与空状态。

## 2026-06-08 结构化 RAG 评估用例验证

- AI 侧 pytest 覆盖结构化评估用例中的 recall@k、precision@k、MRR 与 citation hit。
- 后端 Maven 测试断言 Spring 将可选 evaluation case id 与相关 chunk/document id 转发给 FastAPI，不把评分逻辑移入 Java。
- 前端类型检查 / 构建 覆盖扩展后的实验评估请求类型。
- `smoke_test.py` 为 Advanced RAG 实验评估发送结构化用例，并验证响应 notes 包含结构化检索指标。

## 2026-06-08 结构化 RAG 评估 UI 验证

- 前端类型检查 / 构建 覆盖通过 Spring Boot 加载选中 RAG run 详情、从 top retrieval result 派生结构化用例、清空用例、评估时提交可选结构化字段。
- UI 仍只调用 Spring Boot `/api/*`，不直接调用 FastAPI。
- UI 接线后，本地全链路 smoke 脚本 保持通过。

## 2026-06-08 薄弱点练习评估验证

- 后端 Maven 测试覆盖已掌握 / 仍需复习两类确定性答案评分。
- 后端 Maven 测试覆盖 practice-turn 响应包含 assessment、updated weak point 与 summary。
- 前端类型检查 / 构建 覆盖薄弱点答案输入、练习评估展示与 store 刷新行为。
- `smoke_test.py` 向薄弱点练习接口提交 `userAnswer`，并验证 assessment 状态、更新后的薄弱点与 summary。

## 2026-06-08 薄弱点复习日程验证

- 后端 Maven 测试覆盖练习次数、上次练习分数、下次复习时间与到期复习汇总。
- Flyway 迁移新增薄弱点日程字段，不改变既有必填列。
- 后续迁移会将历史已掌握薄弱点回填到未来复习时间。
- 前端类型检查 / 构建 覆盖共享类型中的薄弱点日程字段与聊天工作台展示。
- `smoke_test.py` 验证 weak point summary 暴露 `dueReviewCount`，practice assessment 响应暴露 `practiceCount`、`lastPracticeScore` 与未来的 `nextReviewAt`。

## 2026-06-08 薄弱点复习队列控件验证

- 前端 typecheck 覆盖全部、到期、待复习、已掌握四类客户端薄弱点筛选。
- 聊天工作台根据 `nextReviewAt` 计算到期项，并复用既有薄弱点练习 store action。
- 前端 build 验证更新后的聊天工作台可以正常打包。
- 后端和 FastAPI API 契约不变；既有薄弱点日程与练习端点继续由全链路 smoke 脚本 覆盖。

## 2026-06-08 Parent-Child 真实父级上下文验证

- AI 侧 pytest 覆盖基于 `parent_chunk_id` 的真实 Parent-Child 上下文路径，断言父块与兄弟子块会在 rerank 前被补齐。
- 既有 Advanced RAG pytest 仍覆盖扁平 chunk 的邻近窗口 fallback 与缺失父块 fallback。
- AI 全量测试通过。
- 本地全链路 smoke 脚本 保持通过。

## 2026-06-08 Parent-Child 切分策略验证

- AI 侧 pytest 覆盖可选 `ParentChildChunker`、默认 `SimpleChunker` 行为、入库时策略选择与查询级 Parent-Child 上下文补齐。
- 父 chunk 作为上下文载体保存，但不参与检索、embedding 与图谱事实抽取。
- AI 全量测试通过。
- 本地全链路 smoke 脚本 保持通过。

## 2026-06-08 可配置混合检索验证

- AI 侧 pytest 覆盖请求级 `retrieval_options` trace 透传与混合权重归一化解析。
- Spring Boot 单元测试覆盖 `retrievalOptions` 透传到 AI RAG 查询上下文。
- 全链路 smoke 脚本 向 Advanced RAG 发送 `retrievalOptions`，并检查持久化检索元数据中的 `vector_weight` / `keyword_weight`。
- AI 全量测试、Spring Boot 全量测试、前端类型检查 / 构建 与本地全链路 smoke 脚本 均通过。

## 2026-06-08 查询感知上下文压缩验证

- AI 侧 pytest 覆盖长 Parent-Child 上下文压缩、命中子块证据保留、引用压缩元数据与 Advanced RAG trace 压缩统计。
- 全链路 smoke 脚本 检查 Parent-Child run 元数据包含 `context_compression_mode=query-aware-sentence-pack`。
- AI 全量测试通过。
- 本地全链路 smoke 脚本 通过。

## 2026-06-08 GraphRAG 评估指标验证

- AI 侧 pytest 覆盖 GraphRAG evaluator notes 中的实体覆盖、关系命中与扩展词命中。
- 全链路 smoke 脚本 评估持久化 GraphRAG run，并验证 evaluator notes 包含 GraphRAG 元数据指标。
- AI 全量测试、Spring Boot 全量测试、前端类型检查 / 构建 与本地全链路 smoke 脚本 均通过。

## 2026-06-08 GraphRAG 指标 UI 验证

- 前端类型检查 / 构建 覆盖解析 GraphRAG evaluator notes，并在实验视图中展示紧凑的实体、关系与扩展词指标。
- UI 改动复用持久化 Spring Boot 评估历史；没有新增浏览器到 FastAPI 的调用。
- 本地全链路 smoke 脚本 保持通过。

## 2026-06-08 LLM 查询转换回退验证

- AI 侧 pytest 覆盖按请求开启的 LLM 查询改写 / 多查询扩展，以及无效输出回退到规则转换器的路径。
- 全链路 smoke 脚本 在 Advanced RAG 查询中启用 `retrievalOptions.enableLlmQueryTransform`，并使用 stub LLM 输出验证回退路径保持通过。

## 2026-06-08 RAG 检索选项 UI 验证

- Spring Boot 单元测试覆盖 assistant-turn 到 AI Agent 请求上下文的 `retrievalOptions` 透传。
- AI 侧 pytest 覆盖 Agent 工作流在 `retrieve_and_generate` 步骤暴露检索选项可观测字段。
- 前端类型检查 / 构建 覆盖聊天页检索预设与 LLM 查询转换开关。
- 全链路 smoke 脚本 在 assistant-turn 请求中发送 `retrievalOptions` 并断言 Agent 工作流收到该配置。
