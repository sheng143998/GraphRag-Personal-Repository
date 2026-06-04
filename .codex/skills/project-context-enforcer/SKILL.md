---
name: project-context-enforcer
description: 在本项目 (agent-vue-java-springboot-fastapi-ai) 中强制执行 PROJECT_CONTEXT.md 的开发规范。当进行任何代码开发、功能实现、Bug 修复、架构变更、文档编写时，必须使用此 skill。触发场景包括：开始新的开发任务、修改代码、新增功能、修复问题、更新文档、完成阶段目标。
---

# 项目上下文执行器 (Project Context Enforcer)

## 概述

此 skill 确保所有开发工作严格遵循 PROJECT_CONTEXT.md 中定义的架构、规范和维护规则。

## 强制执行规则

### 规则 1：开发前必读 PROJECT_CONTEXT.md

在开始任何开发任务之前，必须先读取 PROJECT_CONTEXT.md，了解：

- 当前项目阶段状态（哪些 Phase 已完成、哪些进行中）
- 架构决策和服务职责边界
- 项目目录结构规范
- 当前待办事项和最近变更摘要

### 规则 2：严格遵循架构边界

项目采用前后端分离 + AI 服务独立化：

- 前端 (frontend/)：Vue 3 + TypeScript + Vite。负责知识库管理界面、文档上传、对话交互、检索可视化、RAG 策略配置、问答反馈。
- 业务后端 (backend-java/)：Java + Spring Boot。负责用户/会话/权限、知识库/文档/标签 CRUD、调用 AI 服务、记录问答历史、系统配置。
- AI 服务 (ai-service/)：Python + FastAPI + LangChain + LangGraph。负责文档解析/清洗/切分、Embedding、向量检索、Advanced RAG 策略、Agent 编排、RAG 评估。

禁止跨职责开发：不要在 Spring Boot 中实现 RAG 逻辑，不要在 FastAPI 中实现业务 CRUD，不要在前端直接调用 AI 服务。

### 规则 3：遵循目录结构规范

所有新增文件必须放在正确的目录下：

- docs/architecture/：架构设计文档
- docs/plans/：按日期命名的实施计划
- docs/reviews/：按日期命名的 review prompt
- docs/testing/failures/：失败记录和观察笔记
- docs/handoff/：交接文档和当前状态
- frontend/src/pages/：前端页面组件
- frontend/src/components/：前端通用组件
- backend-java/src/main/java/com/example/agentknowledge/：Spring Boot 源码
- ai-service/app/：FastAPI AI 服务源码

### 规则 4：任务完成后必须维护文档

每完成一个阶段目标或关键任务后，必须同步更新 PROJECT_CONTEXT.md：

1. 更新项目状态行（日期 + 状态）
2. 在对应的日期小节中添加阶段级变更摘要
3. 添加关键文档索引

接口级实现细节、验证命令和失败复盘放入对应的 docs/ 子目录。

### 规则 5：文档命名规范

- 计划文档：docs/plans/YYYY-MM-DD-{task-slug}.md
- Review 文档：docs/reviews/YYYY-MM-DD-{task-slug}-review-prompt.md
- 失败记录：docs/testing/failures/YYYY-MM-DD-{task-slug}-notes.md
- 交接文档：docs/handoff/YYYY-MM-DD-{task-slug}.md

## 开发工作流

### 开始新任务时

1. 读取 PROJECT_CONTEXT.md
2. 确认任务属于哪个 Phase / 模块
3. 确认相关服务边界
4. 创建 docs/plans/YYYY-MM-DD-{task-slug}.md 计划文档
5. 开始实施

### 完成任务时

1. 创建 docs/reviews/YYYY-MM-DD-{task-slug}-review-prompt.md
2. 如有失败/观察，记录到 docs/testing/failures/YYYY-MM-DD-{task-slug}-notes.md
3. 更新 PROJECT_CONTEXT.md：更新日期和状态行，在对应日期小节添加变更摘要，添加关键文档索引

## 关键上下文速查

- 项目是本地知识库 Agent / Advanced RAG 练习项目
- 数据库：PostgreSQL + pgvector
- 向量数据库和业务数据共用 PostgreSQL
- 配置文件：根目录 .env，AI 服务配置在 ai-service/app/core/config.py
- GitHub 远程：https://github.com/sheng143998/GraphRag-Personal-Repository.git
- Git 分支前缀：codex/
