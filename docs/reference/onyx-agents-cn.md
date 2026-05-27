# Onyx AGENTS.md 中文学习整理版

原始项目：Onyx  
原始文档：[onyx-dot-app/onyx/AGENTS.md](https://github.com/onyx-dot-app/onyx/blob/main/AGENTS.md)  
整理目的：学习成熟 RAG / 企业搜索项目如何给 Codex、Claude Code 等编码 Agent 提供开发上下文。  
整理方式：中文改写与结构化提炼，不是逐字翻译。

## 1. 这份文档的定位

Onyx 的 `AGENTS.md` 是一份给 AI 编码 Agent 使用的项目知识库。它不是普通 README，而是直接告诉 Agent：

- 当前项目是什么
- 本地开发环境默认如何运行
- 哪些命令可以执行
- 代码应该放在哪些目录
- 测试应该怎么选
- 数据库、日志、LLM 调用和错误处理有哪些硬性规范

这种文档很适合大型项目，因为 Agent 每次接手任务时，不需要从零猜测项目结构和工程规则。

## 2. 项目概览

Onyx 是一个开源的 Gen-AI 与企业搜索平台，目标是连接公司内部文档、应用和人员，并在此基础上提供 AI 搜索、聊天和知识问答能力。

它的核心特征包括：

- 后端使用 Python、FastAPI、SQLAlchemy、Alembic、Celery
- 前端使用 Next.js、React、TypeScript、Tailwind CSS
- 关系型数据库使用 PostgreSQL
- 缓存和任务协调使用 Redis
- 搜索和向量检索使用 Vespa
- AI 能力包含 LangChain、LiteLLM、多模型 embedding、rerank、chat 等
- 同时包含社区版和企业版代码

对你的项目的启发：

- 可以把 “本地知识库 Agent 项目” 也写成一个清晰的系统，而不只是几个脚本。
- RAG 项目要从一开始就考虑异步任务、日志、测试、trace 和错误处理。
- 文档里要告诉 Agent 哪些模块是业务入口，哪些模块是底层基础设施。

## 3. 写给 Agent 的关键注意事项

Onyx 在文档开头放了很多高优先级规则，这一点非常值得学习。

这类信息通常包括：

- 本地虚拟环境如何激活
- 测试依赖的密钥和环境变量在哪里
- 前端访问地址是什么
- Playwright 或浏览器测试如何登录
- 服务默认是否已经启动
- 数据库如何连接
- 调用后端时应该走前端代理还是直接访问后端端口
- 数据库操作必须放在哪些目录中

对你的项目的启发：

你后续可以在 `PROJECT_CONTEXT.md` 里增加一个 `给 Agent 的关键规则` 部分，例如：

```md
## 给 Agent 的关键规则

- 默认优先阅读 `PROJECT_CONTEXT.md`。
- 不要把真实 API Key 写入代码。
- 所有 RAG 调用必须记录 trace。
- 所有数据库迁移必须放在指定目录。
- 新增 RAG 策略必须补充评估问题。
- 前端请求统一走 API client。
- AI 服务的 Prompt 统一放在 prompts 目录。
```

## 4. 后台任务设计

Onyx 对 Celery worker 的说明非常详细，这说明它的文档不是“介绍型”，而是“开发可执行型”。

它将后台任务拆成多个 worker 类型：

- 主 worker：负责核心后台任务和系统级协调
- 文档抓取 worker：从外部数据源拉取文档
- 文档处理 worker：解析、切分、embedding、写入索引
- 轻量 worker：处理快速、小型任务
- 重型 worker：处理耗时或资源密集型任务
- 监控 worker：采集健康状态和指标
- 用户文件处理 worker：处理用户上传文件
- 定时 worker：调度周期性任务

这部分对 RAG 项目特别有价值。因为真实 RAG 系统通常不是同步完成所有事情，而是包含：

- 文档上传
- 文档解析
- 文档清洗
- chunk 切分
- embedding 生成
- 向量入库
- 元数据更新
- 失败重试
- 定时重建索引

对你的项目的启发：

前期可以先同步处理文档，但文档里应该提前规划异步任务边界：

```text
document_upload
-> parse_document
-> clean_text
-> split_chunks
-> generate_embeddings
-> save_to_pgvector
-> update_document_status
```

后续如果引入任务队列，可以把这些步骤拆成独立任务。

## 5. 架构说明写法

Onyx 的架构部分先写技术栈，再写目录结构。这种顺序很适合 Agent 阅读。

推荐结构：

```md
## Architecture Overview

### Technology Stack

- Backend
- Frontend
- Database
- Search
- Auth
- AI / ML

### Directory Structure

backend/
web/
...
```

对你的项目的启发：

你的项目也可以采用这个结构：

```md
## Architecture Overview

### Technology Stack

- Frontend: Vue 3 + TypeScript + Vite
- Backend: Spring Boot
- AI Service: FastAPI + LangChain + LangGraph
- Database: PostgreSQL + pgvector
- Cache / Queue: Redis, optional

### Directory Structure

frontend/
backend-java/
ai-service/
infra/
docs/
datasets/
```

这样新对话里，Agent 一眼就能知道“应该在哪个服务里改代码”。

## 6. 数据库与迁移规范

Onyx 明确说明：

- 如何运行数据库迁移
- 如何创建数据库迁移
- 迁移文件需要手写并放在工具生成的位置
- 数据库相关操作必须集中在指定目录中

这类规范可以避免 Agent 在业务代码里随手写 SQL，或者绕过项目已有的数据访问层。

对你的项目的启发：

建议后续在项目文档里写清楚：

- Java 后端迁移使用 Flyway 或 Liquibase
- Python AI 服务是否只读业务表，还是也能写 RAG 表
- `document_chunks`、`chunk_embeddings`、`rag_runs` 等表由哪个服务负责写入
- pgvector 索引如何创建
- 数据库变更必须有迁移脚本，不允许只改实体类

## 7. 测试策略

Onyx 的测试策略分得很细，这对大型 AI 应用非常重要。

它将测试分成四类：

- 单元测试：隔离模块，不依赖外部服务
- 外部依赖单元测试：依赖 PostgreSQL、Redis、模型服务等，但不跑完整应用
- 集成测试：运行在真实部署环境上，不做 mock
- Playwright E2E 测试：覆盖前后端完整交互

它还给出具体建议：

- 简单纯函数适合单元测试
- 需要验证真实数据库、缓存、向量库时，写外部依赖测试
- 端到端行为优先写集成测试
- 涉及明显前后端协作的功能才写 E2E

对你的项目的启发：

你的 RAG 项目可以这样规划测试：

```md
### 测试分层

- Python 单元测试：chunker、retriever、prompt builder、reranker adapter
- Python RAG 评估测试：固定问题集、召回结果、答案质量
- Java 集成测试：知识库、文档、会话、反馈接口
- 前端 E2E 测试：上传文档、发起提问、查看引用来源
- 数据库测试：迁移脚本、pgvector 查询、metadata filter
```

## 8. 日志与可观测性

Onyx 明确告诉 Agent 在集成测试或人工调试时应该去哪里看日志。

这点对 AI 项目很关键。因为 RAG 出问题时，通常不是只看最终答案，而是要看：

- 用户原始问题
- 改写后的 query
- 使用了哪种检索策略
- 召回了哪些 chunk
- 每个 chunk 的 score
- rerank 前后顺序
- 传给 LLM 的最终上下文
- LLM 输出
- 耗时和 token 消耗

对你的项目的启发：

你后续可以设计 `rag_runs` 和 `rag_retrieval_results` 表，用来记录每次 RAG 执行过程。

建议字段：

- `run_id`
- `question`
- `rewritten_query`
- `strategy_name`
- `retriever_type`
- `retrieved_chunk_ids`
- `scores`
- `rerank_scores`
- `final_context`
- `answer`
- `latency_ms`
- `model_name`
- `created_at`

## 9. LLM 调用追踪规范

Onyx 特别强调：所有 LLM、embedding、rerank、图像、语音、意图分类调用都必须打 trace 标签。

这是一条非常成熟的工程规范。它的意义是：

- 后续可以统计不同功能的 LLM 消耗
- 可以定位某次回答到底调用了哪个模型
- 可以发现没有被追踪的模型调用
- 可以将 RAG 实验结果和具体调用链关联起来

对你的项目的启发：

你可以在 Python AI 服务中建立类似枚举：

```python
class LLMFlow(str, Enum):
    QUERY_REWRITE = "query_rewrite"
    QUERY_EXPANSION = "query_expansion"
    EMBEDDING = "embedding"
    RERANK = "rerank"
    RAG_GENERATION = "rag_generation"
    CONTEXT_GRADING = "context_grading"
    ANSWER_VERIFICATION = "answer_verification"
```

然后要求：

- 新增任何 LLM 调用前，先定义 flow 类型
- 每次调用都记录输入、输出、模型、耗时和错误
- 不允许出现没有 trace 的模型调用

## 10. 错误处理规范

Onyx 明确要求后端使用统一异常类型，而不是在各处直接抛 HTTP 异常。

这类规范能让 API 返回结构保持一致，也方便前端统一处理错误。

对你的项目的启发：

Java 后端可以设计：

```text
BusinessException
ErrorCode
GlobalExceptionHandler
ApiResponse
```

Python AI 服务可以设计：

```text
AIServiceError
RagErrorCode
FastAPI exception handler
```

建议统一错误响应：

```json
{
  "error_code": "DOCUMENT_NOT_FOUND",
  "message": "文档不存在",
  "details": {}
}
```

## 11. Plan 文档规范

Onyx 还规定了当 Agent 创建计划文档时，需要包含哪些内容。

核心结构包括：

- 要解决的问题
- 调研过程中发现的重要信息
- 实现策略
- 测试计划

并且明确不需要写时间线，也不需要写回滚计划。

对你的项目的启发：

你的项目可以增加 `docs/plans/`，每个复杂功能先写一份计划：

```md
# Plan: Hybrid Search

## Issues to Address

## Important Notes

## Implementation Strategy

## Tests

## Open Questions
```

这样后续和 Codex / Claude Code 协作时，每个功能都有清楚的上下文。

## 12. 可以直接借鉴到你项目的结构

建议将 Onyx 的经验吸收到你的 `PROJECT_CONTEXT.md` 中：

```md
## 给 Agent 的关键规则

## 本地开发入口

## 服务职责边界

## 后台任务规划

## 数据库与迁移规范

## RAG Trace 规范

## LLM 调用规范

## 测试分层

## 错误处理规范

## 创建计划文档的要求
```

## 13. 学习总结

Onyx 的 `AGENTS.md` 最大价值不在于它列出了多少技术，而在于它把“Agent 容易做错的事情”提前写清楚。

它适合学习：

- 大项目如何给 AI 编码助手提供上下文
- RAG / 搜索系统如何做工程化约束
- 后台任务、日志、测试、错误处理如何写进项目规则
- LLM 调用如何纳入可观测体系
- 如何让 Agent 每次改代码都沿着项目已有边界行动

对你的本地知识库 Agent 项目来说，最值得复制的是：

- 开头放高优先级规则
- 明确服务访问方式
- 明确数据库操作位置
- 明确测试类型选择
- 强制记录 RAG / LLM trace
- 用统一错误模型替代临时异常
- 每个复杂功能先写计划文档
