# API 设计文档

更新时间：2026-06-05

本文档记录当前项目已落地和后续开发需要遵守的接口契约。项目采用前端 -> Spring Boot -> FastAPI AI Service 的调用边界：

- 前端只调用 Spring Boot `/api/*`。
- Spring Boot 对外提供业务 API，并在需要 RAG / 文档解析时调用 FastAPI `/ai/*`。
- FastAPI 只作为内部 AI / RAG 服务，不直接暴露给前端。

## 1. 通用约定

### 1.1 Spring Boot 响应包裹

所有 Spring Boot `/api/*` 接口统一返回：

```json
{
  "success": true,
  "data": {},
  "error": null,
  "traceId": "uuid"
}
```

失败响应：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "错误信息"
  },
  "traceId": "uuid"
}
```

前端 `frontend/src/api/client.ts` 会自动解包 `data`，并从响应体或 `X-Trace-Id` 提取 trace id。

### 1.2 类型枚举

文档类型 `documentType` 与 AI Service 枚举保持小写：

| 值 | 含义 |
| --- | --- |
| `tech_note` | 技术笔记 |
| `development_experience` | 开发经验 |
| `project_experience` | 项目经验 |
| `interview_experience` | 面试经验 |
| `code_snippet` | 代码片段 |
| `course_note` | 课程 / 书籍笔记 |
| `job_description` | 招聘 JD / 简历等岗位相关资料 |

文件类型 `fileType`：

| 值 | 含义 |
| --- | --- |
| `md` | Markdown |
| `txt` | 纯文本 |
| `html` | HTML |
| `docx` | Word 文档 |
| `pdf` | PDF |
| `xlsx` | Excel |
| `xls` | Excel |
| `csv` | CSV |

### 1.3 当前边界与限制

- `POST /api/documents/upload` 的 JSON 模式适合文本内容；multipart 模式适合真实文件上传。
- Spring Boot multipart 上传会将原始文件 bytes 编码为 Base64 后传给 AI Service 的 `content_base64`。
- PDF 解析走 MinerU Agent API；若 MinerU 任务长时间处于 `pending`，当前 AI Service 最多轮询 120 秒后返回 `chunk_count=0`。
- Java 调用 AI Service 的读超时默认来自 `AI_SERVICE_READ_TIMEOUT`，长耗时 PDF 解析建议后续改为异步任务模型。
- 当前 embedding / LLM / reranker 仍为 stub 或第一版占位实现，RAG 生成质量不代表最终能力。

## 2. Spring Boot 对外接口

Base URL：`http://localhost:8080`

### 2.1 健康检查

`GET /api/health`

返回：

```json
{
  "status": "UP",
  "service": "backend-java",
  "timestamp": "2026-06-04T00:00:00Z"
}
```

### 2.2 系统设置

`GET /api/settings`

返回：

```json
{
  "apiBaseUrl": "/api",
  "aiServiceBaseUrl": "http://localhost:8001",
  "defaultKnowledgeBaseId": "",
  "timeoutMs": 15000,
  "includeTraceHeader": true
}
```

## 3. 知识库接口

### 3.1 创建知识库

`POST /api/knowledge-bases`

请求：

```json
{
  "name": "工程知识库",
  "description": "技术笔记、项目经验和复盘材料",
  "ownerId": "local-user",
  "defaultRagStrategy": "basic-rag"
}
```

响应 `data`：

```json
{
  "id": "uuid",
  "name": "工程知识库",
  "description": "技术笔记、项目经验和复盘材料",
  "ownerId": "local-user",
  "status": "ACTIVE",
  "defaultRagStrategy": "basic-rag",
  "documentCount": 0,
  "chunkCount": 0,
  "createdAt": "2026-06-04T00:00:00Z",
  "updatedAt": "2026-06-04T00:00:00Z"
}
```

### 3.2 查询知识库列表

`GET /api/knowledge-bases`

响应 `data`：`KnowledgeBaseResponse[]`

### 3.3 查询知识库详情

`GET /api/knowledge-bases/{id}`

响应 `data`：`KnowledgeBaseResponse`

### 3.4 更新知识库

`PUT /api/knowledge-bases/{id}`

请求字段均可选：

```json
{
  "name": "工程知识库",
  "description": "更新后的描述",
  "ownerId": "local-user",
  "status": "ACTIVE",
  "defaultRagStrategy": "hybrid-rerank"
}
```

响应 `data`：`KnowledgeBaseResponse`

### 3.5 删除知识库

`DELETE /api/knowledge-bases/{id}`

响应 `data`：`null`

## 4. 文档接口

### 4.1 JSON 文档上传

`POST /api/documents/upload`

`Content-Type: application/json`

请求：

```json
{
  "knowledgeBaseId": "uuid",
  "title": "Spring 事务传播机制",
  "documentType": "tech_note",
  "fileName": "spring-transaction.md",
  "fileType": "md",
  "mimeType": "text/markdown",
  "sourceType": "LOCAL_UPLOAD",
  "sourcePath": "spring-transaction.md",
  "content": "# Spring 事务\n\n正文内容...",
  "summary": "可选摘要",
  "metadata": {
    "tags": ["spring", "transaction"]
  }
}
```

说明：

- JSON 模式中的 `content` 当前按文本内容处理。
- 二进制文件优先使用 multipart 模式。

### 4.2 multipart 文件上传

`POST /api/documents/upload`

`Content-Type: multipart/form-data`

表单字段：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `knowledgeBaseId` | 是 | 知识库 UUID |
| `title` | 是 | 文档标题 |
| `documentType` | 是 | 文档类型，小写枚举 |
| `sourceType` | 否 | 默认 `LOCAL_UPLOAD` |
| `sourcePath` | 否 | 来源路径或 URL |
| `summary` | 否 | 摘要 |
| `metadata` | 否 | 当前以字符串写入 `multipart_metadata` |
| `file` | 是 | 上传文件 |

响应 `data`：

```json
{
  "id": "uuid",
  "knowledgeBaseId": "uuid",
  "knowledgeBaseName": "工程知识库",
  "title": "27万本科Java简历",
  "documentType": "job_description",
  "fileName": "27万本科Java~.pdf",
  "fileType": "pdf",
  "mimeType": "application/pdf",
  "sourceType": "LOCAL_UPLOAD",
  "sourcePath": null,
  "parserName": "mineru-pdf-adapter",
  "parserVersion": "v1",
  "status": "INDEXED",
  "summary": null,
  "metadata": "{}",
  "chunkCount": 8,
  "chunks": [],
  "createdAt": "2026-06-04T00:00:00Z",
  "updatedAt": "2026-06-04T00:00:00Z"
}
```

### 4.3 查询文档列表

`GET /api/documents`

可选 query：

| 参数 | 说明 |
| --- | --- |
| `knowledgeBaseId` | 只查询指定知识库文档 |

响应 `data`：`DocumentResponse[]`

列表场景下 `chunks` 通常为空，`chunkCount` 为统计值。

### 4.4 查询文档详情

`GET /api/documents/{id}`

响应 `data`：`DocumentResponse`

详情中的 `chunks` 按 `chunkIndex` 升序返回：

```json
{
  "id": "uuid",
  "chunkIndex": 0,
  "title": "Spring 事务传播机制",
  "contentPreview": "前 500 字内容预览",
  "chunkStrategy": "simple-window",
  "pageNumber": null,
  "sheetName": null,
  "rowRange": null,
  "metadata": "{}"
}
```

### 4.5 删除文档

`DELETE /api/documents/{id}`

响应 `data`：`null`

## 5. RAG 问答接口

### 5.1 发起问答

`POST /api/rag/query`

请求：

```json
{
  "knowledgeBaseId": "uuid",
  "sessionId": "uuid",
  "messageId": "uuid",
  "question": "Spring REQUIRED 和 REQUIRES_NEW 有什么区别？",
  "strategyName": "basic-rag",
  "retrieverType": "hybrid",
  "topK": 5
}
```

响应 `data`：

```json
{
  "runId": "uuid",
  "traceId": "trace-id",
  "status": "completed",
  "answer": "回答内容",
  "citations": ["引用标题或片段"],
  "strategyName": "basic-rag",
  "retrieverType": "hybrid"
}
```

### 5.2 查询 RAG 运行详情

`GET /api/rag/runs/{id}`

响应 `data`：

```json
{
  "id": "uuid",
  "traceId": "trace-id",
  "sessionId": "uuid",
  "messageId": "uuid",
  "knowledgeBaseId": "uuid",
  "question": "原始问题",
  "rewrittenQuery": null,
  "strategyName": "basic-rag",
  "retrieverType": "hybrid",
  "finalContext": "最终上下文",
  "answer": "回答内容",
  "modelName": "stub-llm",
  "promptName": "rag_answer",
  "promptVersion": "v1",
  "latencyMs": 123,
  "status": "completed",
  "errorMessage": null,
  "createdAt": "2026-06-04T00:00:00Z",
  "retrievalResults": [
    {
      "id": "uuid",
      "chunkId": "uuid",
      "documentId": "uuid",
      "rank": 1,
      "score": 0.93,
      "rerankScore": null,
      "retrieverType": "hybrid",
      "source": "vector",
      "metadata": {},
      "selectedForContext": true
    }
  ]
}
```

## 6. RAG 实验接口

### 6.1 查询实验列表

`GET /api/rag/experiments`

响应 `data`：`RagExperimentResponse[]`

### 6.2 查询实验详情

`GET /api/rag/experiments/{id}`

响应 `data`：`RagExperimentResponse`

### 6.3 创建实验

`POST /api/rag/experiments`

请求：

```json
{
  "knowledgeBaseId": "uuid",
  "name": "Hybrid + Rerank 对比实验",
  "description": "验证混合检索和重排收益",
  "strategy": "hybrid-rerank",
  "datasetName": "engineering-smoke",
  "sampleCount": 20,
  "precisionScore": 0.82,
  "recallScore": 0.76,
  "status": "DRAFT",
  "notes": "观察记录"
}
```

响应 `data`：

```json
{
  "id": "uuid",
  "knowledgeBaseId": "uuid",
  "name": "Hybrid + Rerank 对比实验",
  "description": "验证混合检索和重排收益",
  "strategy": "hybrid-rerank",
  "datasetName": "engineering-smoke",
  "sampleCount": 20,
  "precisionScore": 0.82,
  "recallScore": 0.76,
  "precision": "82%",
  "recall": "76%",
  "status": "DRAFT",
  "notes": "观察记录",
  "createdAt": "2026-06-04T00:00:00Z",
  "updatedAt": "2026-06-04T00:00:00Z"
}
```

### 6.4 更新实验

`PUT /api/rag/experiments/{id}`

请求字段同创建接口，均为可选。

响应 `data`：`RagExperimentResponse`

### 6.5 删除实验

`DELETE /api/rag/experiments/{id}`

响应 `data`：`null`

## 7. Chat 接口

当前 Chat 接口主要记录会话和消息，RAG 问答仍走 `/api/rag/query`。

### 7.1 创建会话

`POST /api/chat/sessions`

请求：

```json
{
  "knowledgeBaseId": "uuid",
  "title": "Spring 面试复习"
}
```

响应 `data`：

```json
{
  "id": "uuid",
  "knowledgeBaseId": "uuid",
  "title": "Spring 面试复习",
  "sessionStatus": "ACTIVE",
  "createdAt": "2026-06-04T00:00:00Z",
  "updatedAt": "2026-06-04T00:00:00Z"
}
```

### 7.2 查询会话列表

`GET /api/chat/sessions`

响应 `data`：`ChatSessionResponse[]`

### 7.3 新增消息

`POST /api/chat/{sessionId}/messages`

请求：

```json
{
  "role": "user",
  "content": "问题或回答内容",
  "citations": "可选引用 JSON 字符串"
}
```

响应 `data`：

```json
{
  "id": "uuid",
  "sessionId": "uuid",
  "role": "user",
  "content": "问题或回答内容",
  "citations": null,
  "traceId": "trace-id",
  "createdAt": "2026-06-04T00:00:00Z"
}
```

### 7.4 查询会话消息

`GET /api/chat/{sessionId}/messages`

响应 `data`：`ChatMessageResponse[]`

## 8. 反馈接口

### 8.1 创建反馈

`POST /api/feedback`

请求：

```json
{
  "runId": "uuid",
  "sessionId": "uuid",
  "messageId": "uuid",
  "rating": 4,
  "feedbackType": "answer_quality",
  "comment": "引用准确，但回答略长"
}
```

约束：

- `rating` 范围：1 到 5。
- `feedbackType` 必填，最大 50 字符。
- `comment` 可选，最大 5000 字符。

响应 `data`：

```json
{
  "id": "uuid",
  "runId": "uuid",
  "sessionId": "uuid",
  "messageId": "uuid",
  "rating": 4,
  "feedbackType": "answer_quality",
  "comment": "引用准确，但回答略长",
  "createdAt": "2026-06-04T00:00:00Z"
}
```

## 9. FastAPI AI Service 内部接口

Base URL：`http://localhost:8001`，Spring Boot 通过 `AI_SERVICE_BASE_URL` / `app.ai-service.base-url` 配置。

### 9.1 健康检查

`GET /ai/health`

响应：

```json
{
  "status": "ok",
  "service": "ai-service"
}
```

### 9.2 文档入库

`POST /ai/ingest/document`

请求：

```json
{
  "knowledge_base_id": "uuid",
  "document_id": "uuid",
  "title": "文档标题",
  "document_type": "tech_note",
  "file": {
    "filename": "spring.md",
    "file_type": "md",
    "content": "文本内容",
    "content_base64": null,
    "source_path": null,
    "mime_type": "text/markdown"
  },
  "tags": [],
  "tech_stack": [],
  "metadata": {}
}
```

二进制文件应使用 `content_base64`。PDF 会路由到 `mineru-pdf-adapter`，`.docx` 会路由到 `docx-parser`。

响应：

```json
{
  "document_id": "uuid",
  "chunk_count": 3,
  "parser_name": "plain-text-parser",
  "file_type": "md",
  "trace": {
    "trace_id": "trace-id",
    "run_id": "run-id",
    "operation": "ingest_document",
    "strategy_name": "document-ingest",
    "status": "completed",
    "steps": []
  }
}
```

### 9.3 重建 Embedding

`POST /ai/ingest/rebuild-embeddings`

请求：

```json
{
  "knowledge_base_id": "uuid",
  "document_ids": ["uuid"]
}
```

响应：

```json
{
  "knowledge_base_id": "uuid",
  "rebuilt_documents": ["uuid"],
  "trace": {}
}
```

### 9.4 检索

`POST /ai/rag/retrieve`

请求：

```json
{
  "query": "Spring 事务传播",
  "top_k": 5,
  "strategy_name": "basic-rag",
  "context": {
    "knowledge_base_id": "uuid",
    "session_id": null,
    "message_id": null,
    "document_types": [],
    "tags": [],
    "metadata_filters": {}
  }
}
```

响应：

```json
{
  "query": "Spring 事务传播",
  "strategy_name": "basic-rag",
  "results": [
    {
      "document_id": "uuid",
      "chunk_id": "uuid",
      "title": "文档标题",
      "source_path": null,
      "score": 0.93,
      "rerank_score": null,
      "page_number": null,
      "sheet_name": null,
      "metadata": {}
    }
  ],
  "trace": {}
}
```

### 9.5 RAG 问答

`POST /ai/rag/query`

请求：

```json
{
  "question": "Spring REQUIRED 和 REQUIRES_NEW 有什么区别？",
  "top_k": 5,
  "strategy_name": "basic-rag",
  "context": {
    "knowledge_base_id": "uuid",
    "session_id": null,
    "message_id": null,
    "document_types": [],
    "tags": [],
    "metadata_filters": {}
  }
}
```

响应：

```json
{
  "question": "Spring REQUIRED 和 REQUIRES_NEW 有什么区别？",
  "answer": "回答内容",
  "citations": [],
  "trace": {}
}
```

### 9.6 RAG 评估

`POST /ai/rag/evaluate`

请求：

```json
{
  "question": "问题",
  "expected_answer": "期望答案",
  "generated_answer": "生成答案",
  "citations": [],
  "strategy_name": "basic-rag",
  "context": {
    "knowledge_base_id": "uuid",
    "session_id": null,
    "message_id": null,
    "document_types": [],
    "tags": [],
    "metadata_filters": {}
  }
}
```

响应：

```json
{
  "result": {
    "grounded_score": 0.8,
    "retrieval_score": 0.7,
    "notes": []
  },
  "trace": {}
}
```

### 9.7 Agent 调用

`POST /ai/agent/invoke`

请求：

```json
{
  "agent_name": "study-agent",
  "user_input": "帮我生成复习追问",
  "strategy_name": "basic-rag",
  "context": {
    "knowledge_base_id": "uuid",
    "session_id": null,
    "message_id": null,
    "document_types": [],
    "tags": [],
    "metadata_filters": {}
  },
  "variables": {}
}
```

响应：

```json
{
  "agent_name": "study-agent",
  "output": "Agent 输出",
  "citations": [],
  "question_type": "interview",
  "selected_strategy_name": "advanced-rag",
  "workflow_steps": [
    {
      "name": "generate_follow_up_questions",
      "detail": "Generated study and interview follow-up questions.",
      "payload": {
        "follow_up_count": 3
      }
    }
  ],
  "follow_up_questions": [
    "Can you give a 60-second interview answer for this topic?",
    "What follow-up challenge might an interviewer ask about this topic?",
    "Which project experience can prove I really used this topic?"
  ],
  "study_plan": {
    "summary": "Prepare an interview-ready explanation for this topic.",
    "focus_areas": ["interview", "advanced-rag"],
    "steps": [
      "Review the core definition and trade-offs.",
      "Practice a concise project story.",
      "Answer one follow-up question aloud."
    ]
  },
  "review_cards": [
    {
      "question": "Give a 60-second interview explanation of this topic.",
      "expected_answer": "State the concept, explain the trade-off, and anchor it in one project example.",
      "source_hint": "source title or preview",
      "difficulty": "medium"
    }
  ],
  "trace": {}
}
```

## 10. 前端调用映射

前端统一通过 `frontend/src/api/client.ts` 调用 Spring Boot `/api`，当前页面使用的接口：

| 前端模块 | API |
| --- | --- |
| `frontend/src/api/knowledgeBases.ts` | `GET /knowledge-bases`、`POST /knowledge-bases`、`GET /knowledge-bases/{id}`、`PUT /knowledge-bases/{id}`、`DELETE /knowledge-bases/{id}` |
| `frontend/src/api/documents.ts` | `GET /documents`、`GET /documents/{id}`、`POST /documents/upload`、`DELETE /documents/{id}` |
| `frontend/src/api/chat.ts` | `POST /chat/sessions`、`GET /chat/sessions`、`POST /chat/{sessionId}/messages`、`GET /chat/{sessionId}/messages`、`POST /chat/{sessionId}/assistant-turn`、`GET /chat/{sessionId}/weak-points`、`PATCH /chat/{sessionId}/weak-points/{weakPointId}`、`POST /rag/query` |
| `frontend/src/api/experiments.ts` | `GET /rag/experiments`、`GET /rag/experiments/{id}`、`POST /rag/experiments`、`PUT /rag/experiments/{id}`、`DELETE /rag/experiments/{id}` |
| `frontend/src/api/feedback.ts` | `POST /feedback` |
| `frontend/src/api/graph.ts` | `GET /graph/facts?knowledgeBaseId={uuid}&entity={optional}` |
| `frontend/src/api/rag.ts` | `GET /rag/runs/{id}` |
| `frontend/src/api/settings.ts` | `GET /settings` |

后续新增前端页面时，必须继续通过 `src/api/` 封装，不允许页面组件直接 `fetch` 后端或直接调用 AI Service。

## 11. 后续演进建议

- 文档解析改为异步任务：上传接口先返回 `PROCESSING`，前端轮询详情或新增任务状态接口。
- 为接口补充 OpenAPI 导出或 Spring REST Docs，减少手写文档与代码漂移。
- 将 `metadata` 从字符串逐步统一为 JSON object，减少前后端转换成本。
- 为 Chat 问答建立单一业务接口：创建 user message、调用 RAG、保存 assistant message、返回完整对话状态。
- 为 MinerU 增加任务失败原因透出字段，避免 `chunkCount=0` 时缺少可诊断信息。
