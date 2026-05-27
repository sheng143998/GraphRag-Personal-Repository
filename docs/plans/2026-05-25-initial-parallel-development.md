# Initial Parallel Development

## 要解决的问题

项目目前只有上下文文档，需要补齐可开发的 Monorepo 基础骨架，让前端、Java 后端、FastAPI AI 服务和数据库迁移可以并行推进。

## 调研过程中发现的重要信息

- 当前本地已具备 Node.js、Java 21、Maven、Python 3.12。
- PowerShell 直接执行 `npm` 会被执行策略拦截，后续命令使用 `npm.cmd`。
- 当前终端未识别 Docker 命令，但仍保留 Docker Compose 配置，方便 Docker Desktop 或 PATH 配置完成后使用。
- 项目要求所有 RAG 调用记录 trace，数据库变更通过迁移脚本管理。

## 实现策略

- 根目录补齐 README、`.env.example`、`.gitignore`、`docker-compose.yml` 和本地脚本。
- 前端、Java 后端、AI 服务由并行子 Agent 分别创建，写入范围互不重叠。
- 数据库依赖由根目录 Compose 管理，schema 由 Java 后端 Flyway 迁移管理。
- PDF 提取在 AI 服务中预留 MinerU adapter。

## 测试计划

- 前端先验证 TypeScript 构建。
- Java 后端先验证 Maven test。
- AI 服务先验证 Python 编译和 FastAPI health 路由。
- 后续 Docker 可用后，运行 PostgreSQL + pgvector 迁移测试。
