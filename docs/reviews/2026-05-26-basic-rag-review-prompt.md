# 2026-05-26 Basic RAG review 提示

## 本次 review 目标

请按 `PROJECT_CONTEXT.md` 的 RAG 优先级 review 本次 Basic RAG 主链路开发，重点确认 Spring Boot、FastAPI、PostgreSQL + pgvector 三段链路是否契约一致、可验证、可继续扩展到 Advanced RAG。

本次完成的是第一版可跑通的基础 RAG 链路：文档内容进入 chunk 和 embedding 表，问题进入 FastAPI RAG 服务检索，返回答案与引用，Java 后端保存 RAG run 和 retrieval results。

## 本次接口范围

### Spring Boot 对外接口

- `POST /api/rag/query`
  - 入口：`backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
  - 作用：接收用户问题、知识库、会话和 topK 参数，调用 AI 服务完成 RAG 问答，并保存运行记录。
- `GET /api/rag/runs/{id}`
  - 入口：`backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
  - 作用：查询一次 RAG 运行记录和检索结果。

### FastAPI 内部接口

- `POST /ai/rag/query`
  - 入口：`ai-service/app/api/routes/rag.py`
  - 作用：执行 Basic RAG query，返回 answer、citations、trace。
- `POST /ai/ingest/document`
  - 入口：`ai-service/app/api/routes/ingest.py`
  - 作用：接收文档内容，切分 chunk，生成 embedding，并写入数据库。

## 主调用链路

```text
Vue sendChatMessage
-> Spring RagController.query
-> Spring RagService.query
-> AiServiceClient.queryRag
-> FastAPI POST /ai/rag/query
-> Python RagService.query
-> DatabaseRetriever
-> PostgreSQL document_chunks / chunk_embeddings
-> stub LLM generator
-> FastAPI 返回 answer / citations / trace
-> Spring 保存 rag_runs / rag_retrieval_results
-> Spring 返回 RagRunResponse
```

## 重点 review 顺序

1. FastAPI schema 与数据库访问
   - `ai-service/app/schemas/rag.py`
   - `ai-service/app/schemas/ingest.py`
   - `ai-service/app/db/repositories.py`
   - 检查请求/响应字段、`knowledge_base_id` 过滤、chunk/embedding 写入、连接释放。

2. Retriever 与检索排序逻辑
   - `ai-service/app/rag/retrievers/base.py`
   - `ai-service/app/rag/strategies/base.py`
   - 检查 vector score、keyword score、hybrid score 的融合逻辑，以及 `top_k` 和 metadata filter 是否被正确传递。

3. Java 调用 AI 服务的 DTO 契约
   - `backend-java/src/main/java/com/example/agentknowledge/client/AiServiceClient.java`
   - `backend-java/src/main/java/com/example/agentknowledge/client/dto/AiRagQueryRequest.java`
   - `backend-java/src/main/java/com/example/agentknowledge/client/dto/AiRagQueryResponse.java`
   - `backend-java/src/main/java/com/example/agentknowledge/client/dto/AiSourceMetadata.java`
   - `backend-java/src/main/java/com/example/agentknowledge/client/dto/AiTraceMetadata.java`
   - 检查 Java DTO 是否与 FastAPI `/ai/rag/query` schema 对齐。

4. Java RAG run 与 retrieval result 持久化
   - `backend-java/src/main/java/com/example/agentknowledge/service/RagService.java`
   - `backend-java/src/main/java/com/example/agentknowledge/domain/RagRun.java`
   - `backend-java/src/main/java/com/example/agentknowledge/domain/RagRetrievalResult.java`
   - `backend-java/src/main/java/com/example/agentknowledge/repository/RagRunRepository.java`
   - `backend-java/src/main/java/com/example/agentknowledge/repository/RagRetrievalResultRepository.java`
   - 检查 `metadata` 使用 `Map<String, Object>` 承载 JSONB，避免 JSON 字符串二次解析错误。

5. 配置默认值与环境变量
   - `backend-java/src/main/resources/application.yml`
   - `.env.example`
   - `ai-service/app/core/config.py`
   - 检查 `AI_SERVICE_MOCK_ENABLED=false` 是否符合真实联调默认路径，数据库账号密码是否只通过本地环境传入，没有写进代码或文档。

6. 测试和验证覆盖
   - `ai-service/tests/test_basic_rag_pipeline.py`
   - 检查 Python 内存模式是否覆盖 Basic RAG 主链路。
   - Java 目前主要通过 `mvn test` 编译验证，建议后续补 `AiServiceClient` mock 测试和 `RagService` 持久化测试。

## 已执行验证

- Python 单测：在 `AI_RAG_USE_DATABASE=false` 下运行 `.\.venv\bin\python.exe -m pytest`，结果通过。
- Python 编译检查：在 `AI_RAG_USE_DATABASE=false` 下运行 `.\.venv\bin\python.exe -m compileall app tests`，结果通过。
- Java 编译测试：在 `backend-java/` 下运行 `mvn test`，结果通过。
- AI 服务数据库 smoke：使用本地 PostgreSQL、`agent_knowledge` 数据库和测试知识库，调用 ingest 后再 query，能返回引用。
- 完整 HTTP 链路：启动 FastAPI 8001 与 Spring Boot 后端，通过 `Invoke-RestMethod` 调用 `POST /api/rag/query`，真实走通 Spring -> FastAPI -> PostgreSQL，返回 `success:true`、answer 和 citation，并写入运行记录。

## 当前占位实现

- LLM 生成器仍是 stub answer，尚未接入真实模型服务。
- Embedding 是 deterministic hash embedding，维度为 1536，用于本地验证 `vector(1536)` 写入和检索，不代表真实语义向量质量。
- Reranker 仍是 stub，仅保留接口位置。
- 当前只实现 Basic RAG，Advanced RAG 的 query rewrite、multi-query、parent-child、context compression、GraphRAG 还未实现。
- Ingest 当前主要是直接传入文本内容的 API 链路，真实文件上传、格式解析、OCR、MinerU PDF 解析还未接入完整流程。
- 前端上传和部分界面仍需继续对齐真实后端接口。

## Review 时特别注意

- pgvector 字段是 `vector(1536)`，当前 embedding 维度必须稳定为 1536。
- `rag_retrieval_results.metadata` 是 JSONB，Java 侧必须使用 `Map<String, Object>`，不要改回 `String`。
- 本次默认关闭 Java AI mock：`AI_SERVICE_MOCK_ENABLED=false`，否则无法验证真实 Spring -> FastAPI 链路。
- PowerShell 下不要直接用 `curl.exe -d` 拼复杂 JSON，容易出现引号转义问题；优先使用 `ConvertTo-Json` + `Invoke-RestMethod`。
- 本地数据库密码、模型 key、token 只能放本地环境变量，不应写入仓库文档或代码。

## 给下一个 Codex 的 review 提示

请你从 `POST /api/rag/query` 开始 review Basic RAG 主链路。先检查 Spring Controller、Service、AI Client 和 DTO 是否与 FastAPI `/ai/rag/query` 契约一致，再检查 Python `RagService`、`DatabaseRetriever`、`PostgresDocumentRepository` 是否正确使用 `knowledge_base_id`、`top_k`、query embedding、metadata 和 pgvector。最后检查 `rag_runs`、`rag_retrieval_results` 的保存字段是否足够支撑后续 RAG 评估与 trace 可观测性。

本次 review 请优先提出：

- 跨服务 schema 不一致问题。
- 检索排序和过滤逻辑的正确性风险。
- JSONB、UUID、时间字段、embedding 维度等数据库类型风险。
- 当前 stub 实现进入真实模型前必须补齐的边界。
- Java 还缺哪些自动化测试。
