# 脚本模块

## 模块职责

脚本模块用于保存本地开发、依赖启动、依赖停止和数据库重置相关的辅助脚本。脚本会影响本地环境，运行前需要先确认当前数据库和服务状态。

## 技术栈

- PowerShell。
- Docker Compose。
- PostgreSQL 命令行工具，按脚本需要使用。

## 目录结构说明

```text
scripts/
├─ dev-start.ps1        # 启动本地依赖
├─ dev-stop.ps1         # 停止本地依赖
└─ reset-local-db.ps1   # 重置本地数据库
```

## 本地使用方式

在项目根目录执行脚本。

```powershell
.\scripts\dev-start.ps1
.\scripts\dev-stop.ps1
```

重置数据库前请确认没有需要保留的本地数据。

```powershell
.\scripts\reset-local-db.ps1
```

## 常用命令

```powershell
Get-ExecutionPolicy
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\scripts\dev-start.ps1
.\scripts\dev-stop.ps1
```

## 环境变量说明

脚本可能读取根目录 `.env` 或本地环境变量。真实密码只保存在本地，不写入脚本正文。

常见变量：

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `SPRING_DATASOURCE_URL`
- `AI_DATABASE_URL`

## 关键脚本说明

- `dev-start.ps1`：启动本地基础依赖，适合开发前执行。
- `dev-stop.ps1`：停止本地基础依赖，适合开发结束后执行。
- `reset-local-db.ps1`：重置本地数据库，可能删除本地数据，执行前必须确认。

## 重点审查文件

- `dev-start.ps1`
- `dev-stop.ps1`
- `reset-local-db.ps1`
- 根目录 `docker-compose.yml`
- `infra/postgres/init.sql`

## 与其他模块的调用关系

```text
脚本
-> Docker Compose
-> PostgreSQL 与 pgvector
-> Java 后端和 Python 人工智能服务使用这些依赖
```

## 当前已实现能力

- 本地依赖启动脚本。
- 本地依赖停止脚本。
- 本地数据库重置脚本。

## 当前占位实现

- 还没有统一启动前端、Java 后端和人工智能服务的完整集成脚本。
- 还没有完整 HTTP 联调脚本。

## 后续待补能力

- 增加一键本地联调脚本。
- 增加健康检查等待逻辑。
- 增加日志收集和失败提示。
- 增加集成测试数据准备脚本。

## 常见问题

- 如果脚本无法执行，先检查 PowerShell 执行策略。
- 如果 Docker 命令不可用，先确认 Docker 已启动并在系统路径中。
- 如果数据库重置失败，检查是否仍有服务占用数据库连接。
## 2026-06-08 Local Full-Chain Automation

Docker is optional for the current local full-chain smoke path. When a local PostgreSQL instance is already available and `.env` contains `DB_URL`, `DB_USERNAME`, and `DB_PASSWORD`, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1
```

For a faster run after the backend jar has already been built:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1 -SkipBuild
```

The script starts FastAPI on `127.0.0.1:8001` in stub/in-memory mode, starts Spring Boot on `127.0.0.1:8080`, waits for both health endpoints, runs `smoke_test.py`, and stops the services it started unless `-KeepServices` is passed.

`smoke_test.py` also supports:

- `SMOKE_BASE_URL`, default `http://localhost:8080/api`
- `SMOKE_AI_BASE_URL`, default `http://localhost:8001/ai`
- `SMOKE_TIMEOUT`, default `15`
