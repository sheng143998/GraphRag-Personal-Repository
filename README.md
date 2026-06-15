# 本地知识库 Agent / Advanced RAG 项目

这是一个用于练习本地知识库、Advanced RAG、Agent 编排和 RAG 评测闭环的三服务项目。项目采用 `Vue 3 + Spring Boot + FastAPI + PostgreSQL/pgvector` 架构，重点不是只做一个问答页面，而是把文档入库、检索、生成、评估、实验对比和可观测性串成完整工程链路。

## 个人知识库来源

本项目使用的个人知识库语料来自 [Obsidian AI 学习笔记库](https://github.com/HeWhenJay/obsidian-study-notes)。该笔记库整理了 AI Agent、RAG、LangChain、LangGraph、GraphRAG、多 Agent、MCP、A2A、Agent Skills、AutoGen、CrewAI 等学习笔记、图解和示例代码。

这个搜索项目用于把上述笔记沉淀成本地可检索、可追溯、可评估的知识库：从 Obsidian Markdown 笔记入库，到 RAG/GraphRAG 检索、引用来源展示、问答生成和学习薄弱点分析。需要阅读原始笔记内容时，请访问笔记仓库；需要体验检索问答链路时，请运行本项目。

## 当前状态

- 前端：Vue 3 + TypeScript + Pinia + Vite，已重构为 Coze Studio 风格工作台，覆盖聊天、文档、知识库、实验评测、图谱、反馈和设置页面。
- Java 后端：Spring Boot 统一暴露 `/api/*`，负责业务 CRUD、数据库迁移、RAG run 持久化、评测集管理、批量评测编排和 AI 服务桥接。
- Python AI 服务：FastAPI 暴露内部 `/ai/*`，负责文档解析、chunk、embedding、检索、重排、生成、Advanced RAG preset、GraphRAG、Agent 和 evaluator。
- 数据库：PostgreSQL + pgvector，统一承载业务数据、文档 chunk、embedding、RAG run、retrieval results、评测集、评测历史和图谱事实。
- 评测平台：已支持评测集管理、单样本评估、批量跑同一批样本对比不同 RAG preset，并结构化记录 `recall@k`、`precision@k`、`MRR`、`citation_hit`、token、成本和分阶段耗时。

## 架构边界

```text
Browser
-> frontend/src/api/*
-> Spring Boot /api/*
-> FastAPI /ai/*
-> PostgreSQL + pgvector
```

- 前端只调用 Spring Boot `/api/*`，不直接调用 FastAPI。
- Spring Boot 只做业务、桥接和持久化，不实现 RAG / evaluator 算法。
- FastAPI 负责 RAG、Agent、GraphRAG、文档解析、检索生成和指标计算。
- 数据库变更必须通过 `backend-java/src/main/resources/db/migration/` 下的 Flyway 迁移脚本。

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

5. 启动前端：

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

## 常用验证

```powershell
npm.cmd --prefix frontend run typecheck
npm.cmd --prefix frontend run build
mvn.cmd -f backend-java\pom.xml test
.\ai-service\.venv\bin\pytest.exe ai-service\tests
```

## 模块说明

- `frontend/`：Coze 风格前端工作台，负责知识库、文档、聊天、实验评测、图谱、反馈和设置交互。
- `backend-java/`：Spring Boot 业务后端，负责 `/api/*`、Flyway 迁移、业务持久化、RAG run 记录和 AI 服务桥接。
- `ai-service/`：FastAPI AI 服务，负责 `/ai/*`、文档解析、Advanced RAG、GraphRAG、Agent、evaluator 和 trace。
- `infra/`：本地基础设施配置，当前重点是 PostgreSQL + pgvector。
- `scripts/`：本地依赖启动、停止、数据库重置和全链路 smoke 辅助脚本。
- `docs/`：计划、交接、review prompt、失败复盘和架构说明。

## 当前重点文档

- 项目上下文：[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)
- 当前交接：[docs/handoff/CURRENT_STATE.md](docs/handoff/CURRENT_STATE.md)
- API 设计：[docs/architecture/api-design.md](docs/architecture/api-design.md)
- 数据库设计：[docs/architecture/database-design.md](docs/architecture/database-design.md)
- 当前评测计划：[docs/plans/2026-06-15-advanced-rag-preset-evaluation-runner.md](docs/plans/2026-06-15-advanced-rag-preset-evaluation-runner.md)

## 开发约定

- 每次开发前先看 `PROJECT_CONTEXT.md` 和 `docs/handoff/CURRENT_STATE.md`。
- Prompt 统一放在 `ai-service/app/prompts/`。
- 前端 API 调用统一放在 `frontend/src/api/`。
- Java DTO / Entity / migration / 前端类型 / Python schema 需要保持字段契约一致。
- 不提交真实 API key、数据库密码、模型 token 或完整认证头。
