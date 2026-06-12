# 本地知识库智能体练习项目

本项目是一个本地知识库智能体与进阶检索增强生成练习项目，采用前端、业务后端、人工智能服务三段式架构。项目目标不是只做一个问答页面，而是逐步沉淀文档入库、向量检索、混合检索、重排、引用、评估和智能体编排等完整能力。

## 个人知识库来源

本项目使用的个人知识库语料来自 [Obsidian AI 学习笔记库](https://github.com/HeWhenJay/obsidian-study-notes)。该笔记库整理了 AI Agent、RAG、LangChain、LangGraph、GraphRAG、多 Agent、MCP、A2A、Agent Skills、AutoGen、CrewAI 等学习笔记、图解和示例代码。

这个搜索项目用于把上述笔记沉淀成本地可检索、可追溯、可评估的知识库：从 Obsidian Markdown 笔记入库，到 RAG/GraphRAG 检索、引用来源展示、问答生成和学习薄弱点分析。需要阅读原始笔记内容时，请访问笔记仓库；需要体验检索问答链路时，请运行本项目。

## 当前状态

当前项目已经具备三服务基础骨架，并优先推进基础检索增强生成主链路。

已完成的关键能力：

- 前端工作台基础结构。
- Java 业务后端基础接口、数据库迁移和健康检查。
- Python 人工智能服务基础接口、文档切分、向量写入和基础问答链路。
- PostgreSQL 与 pgvector 数据库表结构。
- `POST /api/rag/query` 到 `/ai/rag/query` 的真实跨服务调用链路。
- RAG 运行记录与检索结果保存。

仍然是占位或待完善的能力：

- 大模型回答生成仍是占位实现。
- 向量生成仍是本地确定性占位实现。
- 重排器仍是占位实现。
- 文件上传、多格式解析、PDF 解析和前端完整联调仍需继续推进。

## 本地依赖

- Node.js 24 或更高版本。
- Java 21。
- Maven 3.9 或更高版本。
- Python 3.12 或更高版本。
- PostgreSQL 与 pgvector。
- Docker 与 Docker Compose，推荐用于本地依赖启动。

## 快速开始

1. 复制环境变量模板。

```powershell
Copy-Item .env.example .env
```

2. 启动基础依赖。

```powershell
.\scripts\dev-start.ps1
```

3. 启动 Java 后端。

```powershell
cd backend-java
mvn spring-boot:run
```

4. 启动人工智能服务。

```powershell
cd ai-service
python -m venv .venv
.\.venv\bin\python.exe -m pip install -e .
.\.venv\bin\python.exe -m uvicorn app.main:app --reload --port 8001
```

5. 启动前端。

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

## 模块说明

- `frontend/`：前端工作台，负责知识库管理、聊天界面、上传入口和结果展示。
- `backend-java/`：业务后端，负责对外接口、业务数据、数据库迁移、调用人工智能服务和保存运行记录。
- `ai-service/`：人工智能服务，负责文档处理、检索增强生成、向量检索、重排、生成和评估能力。
- `infra/`：基础设施配置，当前重点是 PostgreSQL 与 pgvector 初始化。
- `scripts/`：本地开发辅助脚本。
- `docs/`：计划、交接、测试复盘、审查提示和架构说明。

## 关键约定

- 每次开发前先阅读 `PROJECT_CONTEXT.md` 和 `docs/handoff/CURRENT_STATE.md`。
- 不提交真实密钥、数据库密码、模型令牌或完整认证头。
- 前端请求统一走 `frontend/src/api/`。
- 人工智能服务提示词统一放在 `ai-service/app/prompts/`。
- 数据库变更必须写迁移脚本。
- 所有检索增强生成、模型、向量和重排调用必须记录追踪信息。
- 每完成一个接口或关键链路，需要输出审查提示并暂停。

## 常用文档

- 项目上下文：`PROJECT_CONTEXT.md`
- 当前交接状态：`docs/handoff/CURRENT_STATE.md`
- 计划文档：`docs/plans/`
- 审查提示：`docs/reviews/`
- 失败复盘：`docs/testing/failures/`
- 测试策略：`docs/testing/strategy.md`
