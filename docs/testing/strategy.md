# Testing Strategy

测试分为四类：

- 单元测试：隔离模块，不依赖外部服务。
- 外部依赖单元测试：依赖 PostgreSQL、Redis、模型服务等，但不跑完整应用。
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
## 2026-06-08 Current Automated Verification

- Frontend: `npm.cmd run typecheck`, `npm.cmd run build`.
- Backend: `mvn test`; current service-level coverage includes RAG bridge persistence/failure cases and async document ingest success/failure cases.
- AI service: `.venv\bin\python.exe -m pytest`; current coverage includes Basic RAG, Advanced RAG, OpenAI-compatible adapter parsing, and offline strategy comparison metrics.
- Full-chain local smoke: `powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1 -SkipBuild`.
- Direct smoke script: `python smoke_test.py`; accepts `SMOKE_BASE_URL`, `SMOKE_AI_BASE_URL`, and `SMOKE_TIMEOUT`.

The full-chain smoke now treats RAG query failure as a hard failure and includes an `advanced-rag` trace assertion for completed status, citation presence, and stored `rewrittenQuery`.

## 2026-06-08 Agent Workflow Validation

- AI pytest covers question classification, automatic strategy selection, RAG execution, citations, and workflow step trace metadata.
- Backend Maven tests cover the Spring Boot `/api/agent/invoke` bridge request/response mapping.
- Local full-chain smoke covers Spring Boot -> FastAPI Agent invocation and now passes 47/47 checks.

## 2026-06-08 GraphRAG Validation

- AI pytest covers deterministic GraphRAG entity/relationship extraction, graph query augmentation, trace attributes, and citation graph metadata.
- Frontend typecheck/build verifies the `GraphRAG` strategy option is available to the workbench.
- Local full-chain smoke covers Spring Boot -> FastAPI `strategyName=graph-rag` invocation and now passes 54/54 checks.

## 2026-06-08 GraphRAG Persistence Validation

- Flyway migration `V202606081300__create_graph_facts.sql` is included in the backend package and executed during local Spring Boot startup.
- AI pytest covers persisted graph fact lookup through the in-memory repository.
- Full-chain smoke remains 54/54 after adding graph fact tables and ingest-time graph extraction.

## 2026-06-08 Graph Facts Query Validation

- Backend Maven tests now include `GraphFactServiceTest`, covering entity filter normalization, DTO mapping, and the 100-row query limit.
- Frontend typecheck/build covers the new `/graph` workbench page and `frontend/src/api/graph.ts`.
- The local full-chain script now runs the AI service in database-backed mode (`AI_RAG_USE_DATABASE=true`) so AI ingest writes graph facts into the same PostgreSQL database that Spring Boot reads.
- Local full-chain smoke now covers `GET /api/graph/facts` and `GET /api/graph/facts?entity=GraphRAG`, passing 60/60 checks with persisted entity and relationship counts.

## 2026-06-08 GraphRAG Traversal Retrieval Validation

- AI pytest covers one-hop graph expansion terms and traversal relationships in GraphRAG trace/citation metadata.
- `smoke_test.py` now checks Spring Boot RAG run retrieval metadata for `graph_expansion_terms` and `graph_traversal_relationships`.
- Local full-chain smoke should pass 62/62 checks after this change.

## 2026-06-08 GraphRAG Offline Evaluation Fixture Validation

- AI pytest now compares `advanced-rag` and `graph-rag` on fixed graph relationship and expansion cases.
- The fixture expects GraphRAG to improve recall@k, precision@k, MRR, and citation hit for entity/relationship questions without using Docker or real model calls.

## 2026-06-08 Assistant Turn Chat Flow Validation

- Backend Maven tests include `AssistantTurnServiceTest`, covering user/assistant message persistence and Agent request context propagation.
- Frontend typecheck/build covers the new `sendAssistantTurn()` API wiring and chat store flow.
- `smoke_test.py` now covers `POST /api/chat/{sessionId}/assistant-turn`, assistant workflow metadata, persisted messages, and feedback submission against the assistant message.

## 2026-06-08 Agent Follow-Up Questions Validation

- AI pytest covers the new `generate_follow_up_questions` workflow step, trace attribute, and three generated follow-up prompts.
- Backend Maven tests cover `follow_up_questions` to `followUpQuestions` DTO propagation through Agent and assistant-turn services.
- Frontend typecheck/build covers clickable follow-up prompts in the chat workbench.
- `smoke_test.py` now verifies assistant-turn returns at least three non-empty `followUpQuestions` through Spring Boot.
- Local full-chain smoke now passes 74/74 checks, including direct Agent and assistant-turn follow-up trace assertions.

## 2026-06-08 Agent Study Plan Validation

- AI pytest covers the `generate_study_plan` workflow step, trace attribute, and three structured study plan steps.
- Backend Maven tests cover `study_plan` to `studyPlan` DTO propagation through Agent and assistant-turn services.
- Frontend typecheck/build covers the chat workbench study plan panel.
- `smoke_test.py` now verifies direct Agent and assistant-turn responses include `studyPlan` with at least three steps and matching trace attributes.
- Local full-chain smoke now passes 78/78 checks.

## 2026-06-08 Agent Review Cards Validation

- AI pytest covers the `generate_review_cards` workflow step, trace attribute, and active-recall review card generation.
- Backend Maven tests cover `review_cards` to `reviewCards` DTO propagation through Agent and assistant-turn services.
- Frontend typecheck/build covers the chat workbench review card panel.
- `smoke_test.py` now verifies direct Agent and assistant-turn responses include at least two `reviewCards` with matching trace questions.
- Local full-chain smoke now passes 82/82 checks.

## 2026-06-08 Learning Weak Points Validation

- Backend Maven tests cover session weak point recording from review cards and assistant-turn response propagation.
- Frontend typecheck/build covers weak point API types, store state, and chat workbench panel.
- `smoke_test.py` now verifies assistant-turn returns weak points and `GET /api/chat/{sessionId}/weak-points` reads persisted weak points.
- Local full-chain smoke now passes 85/85 checks.

## 2026-06-08 Weak Point Assessment Validation

- Backend Maven tests cover `MASTERED` / `NEEDS_REVIEW` weak point status updates.
- Frontend typecheck/build covers weak point assessment actions in the chat workbench.
- `smoke_test.py` now verifies `PATCH /api/chat/{sessionId}/weak-points/{weakPointId}` updates a persisted weak point to `MASTERED`.
- Local full-chain smoke now passes 87/87 checks.

## 2026-06-08 Weak Point Prioritization Validation

- Backend Maven tests cover the weak point list ordering contract.
- `smoke_test.py` now re-lists weak points after a mastery update and expects a `NEEDS_REVIEW` item first.
- Local full-chain smoke now passes 89/89 checks.

## 2026-06-08 Weak Point Progress Summary Validation

- Backend Maven tests cover total, needs-review, mastered, hard, review-count, completion-rate, and next-item aggregation.
- Frontend typecheck/build covers `fetchWeakPointSummary()`, Pinia summary state, and the chat workbench progress cards.
- `smoke_test.py` verifies `GET /api/chat/{sessionId}/weak-points/summary` before and after marking a weak point mastered.

## 2026-06-08 RAG Experiment Evaluation Validation

- Backend Maven tests include `RagExperimentServiceTest`, covering persisted run lookup, retrieval evidence mapping, FastAPI evaluator request construction, score persistence, status update, and notes append behavior.
- `smoke_test.py` now evaluates the created RAG experiment from the persisted Advanced RAG run and verifies `COMPLETED` status, grounded score, retrieval score, and evaluator notes.
- Local full-chain smoke now passes 94/94 checks.

## 2026-06-08 Weak Point Practice Flow Validation

- Backend Maven tests include `WeakPointPracticeServiceTest`, covering weak point prompt construction, assistant-turn invocation, and `weak-point-practice` variables.
- Frontend typecheck/build covers `practiceWeakPointTurn()` API mapping, Pinia practice action, and chat page `Practice` button wiring.
- `smoke_test.py` now verifies a persisted weak point can trigger a practice turn and returns the selected weak point, assistant message, review cards, and updated weak points.
- Local full-chain smoke now passes 99/99 checks.

## 2026-06-08 RAG Evaluation Workbench Validation

- Backend Maven tests cover recent RAG run summary mapping and limit clamping.
- Frontend typecheck/build covers recent run loading, experiment evaluation API mapping, and the experiments page run selector.
- `smoke_test.py` now verifies `GET /api/rag/runs?limit=10` includes the created run before experiment evaluation.
- Local full-chain smoke now passes 101/101 checks.

## 2026-06-08 RAG Evaluation History Validation

- Backend Maven tests include `RagExperimentServiceTest`, covering transactional experiment evaluation, evaluator request mapping, score persistence, and `rag_experiment_evaluations` history row creation.
- Frontend typecheck/build covers `ExperimentEvaluationHistory` response typing and the experiments page recent evaluation history list.
- `smoke_test.py` now verifies the Advanced RAG experiment evaluation response includes `data.evaluation.runId`, non-empty `data.history`, and non-empty `data.experiment.evaluations`.
- Local full-chain smoke passed with 104/104 checks after adding the history assertions.

## 2026-06-08 RAG Evaluation Comparison Dashboard Validation

- Backend Maven tests verify evaluation history responses include run question, strategy, retriever, model, latency, and run creation time.
- Frontend typecheck/build covers the recent-history dashboard, per-experiment averages, latest delta labels, and question snapshot history rows.
- `smoke_test.py` now evaluates one experiment from both Advanced RAG and Basic RAG runs, then verifies at least two history rows for comparison.
- Local full-chain smoke passed with 108/108 checks.

## 2026-06-08 RAG Evaluation Summary Endpoint Validation

- Backend Maven tests verify `RagExperimentService.summarizeEvaluations()` returns recent count, averages, best experiment, and recent evaluation rows.
- Frontend typecheck/build covers `fetchExperimentEvaluationSummary()`, Pinia summary state, hydrate loading, and dashboard usage.
- `smoke_test.py` verifies `GET /api/rag/experiment-evaluations/summary?limit=10` after two experiment evaluations.
- Local full-chain smoke passed with 115/115 checks.

## 2026-06-08 RAG Evaluator Answer Alignment Validation

- AI pytest covers matched versus mismatched expected/generated answers with the same citation set.
- The deterministic evaluator now combines citation support with answer alignment, so citation presence alone does not force a perfect grounded score.
- Backend Maven tests assert Spring forwards `expectedAnswer` into the FastAPI evaluator request.

## 2026-06-08 RAG Evaluation Comparison Page Validation

- Frontend typecheck/build covers `/experiments/comparison`, summary reuse, strategy-level aggregation, experiment-level aggregation, and recent evaluation rows.
- The page reuses `GET /api/rag/experiment-evaluations/summary`; the existing full-chain smoke continues to validate the API contract after Advanced RAG and Basic RAG evaluations.
- Frontend typecheck/build also covers the comparison page strategy and experiment filters, including filtered aggregate rows and empty-state paths.

## 2026-06-08 Structured RAG Evaluation Case Validation

- AI pytest covers structured evaluation cases that score retrieval with recall@k, precision@k, MRR, and citation hit.
- Backend Maven tests assert Spring forwards optional evaluation case ids and relevant chunk/document ids to FastAPI without moving scoring into Java.
- Frontend typecheck/build covers the expanded experiment evaluation request type.
- `smoke_test.py` now sends a structured case for the Advanced RAG experiment evaluation and verifies the response notes include structured retrieval metrics.
- Local full-chain smoke passed with 123/123 checks.

## 2026-06-08 Structured RAG Evaluation UI Validation

- Frontend typecheck/build covers loading selected RAG run details through Spring Boot, deriving a structured case from the top retrieval result, clearing the case, and submitting optional structured fields during experiment evaluation.
- The UI still calls only Spring Boot `/api/*` endpoints; it does not call FastAPI directly.
- Local full-chain smoke remained green with 123/123 checks after the UI wiring.

## 2026-06-08 Weak Point Practice Assessment Validation

- Backend Maven tests cover deterministic weak point answer scoring for mastered and needs-review outcomes.
- Backend Maven tests cover practice-turn responses that include assessment, updated weak point, and summary.
- Frontend typecheck/build covers weak point answer inputs, practice assessment display, and store refresh behavior.
- `smoke_test.py` now submits `userAnswer` to the weak point practice endpoint and verifies assessment status, updated weak point, and summary.
- Local full-chain smoke passed with 126/126 checks.
