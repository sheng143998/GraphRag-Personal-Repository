# 脚本模块

## 模块职责

`scripts/` 保存本地开发、依赖启动、依赖停止、数据库重置、全链路 smoke 和简历生成等辅助脚本。部分脚本会修改本地环境或数据，运行前需要确认当前服务和数据库状态。

## 技术栈

- PowerShell
- Docker Compose
- Python
- PostgreSQL 命令行工具，按脚本需要使用

## 目录结构

```text
scripts/
├── dev-start.ps1                  # 启动本地依赖
├── dev-stop.ps1                   # 停止本地依赖
├── reset-local-db.ps1             # 重置本地数据库
├── test-fullchain-local.ps1       # 本地全链路 smoke
└── *.py                           # 文档 / 简历等辅助脚本
```

## 常用命令

```powershell
.\scripts\dev-start.ps1
.\scripts\dev-stop.ps1
.\scripts\reset-local-db.ps1
```

重置数据库前请确认没有需要保留的本地数据。

## 本地全链路 smoke

当本地 PostgreSQL 已可用，且 `.env` 包含 `DB_URL`、`DB_USERNAME`、`DB_PASSWORD` 时，可以运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1
```

如果后端 jar 已构建，可跳过构建：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1 -SkipBuild
```

该脚本会启动 FastAPI 和 Spring Boot，等待 health endpoint，就绪后执行 `smoke_test.py`，默认会停止它启动的服务。传入 `-KeepServices` 可保留服务。

## smoke_test.py 环境变量

- `SMOKE_BASE_URL`：默认 `http://localhost:8080/api`
- `SMOKE_AI_BASE_URL`：默认 `http://localhost:8001/ai`
- `SMOKE_TIMEOUT`：默认 `15`

## 注意事项

- PowerShell 脚本无法执行时，先检查执行策略：

```powershell
Get-ExecutionPolicy
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

- Docker 命令不可用时，确认 Docker Desktop 已启动且在系统 PATH 中。
- 数据库重置失败时，检查是否仍有 Java / Python 服务占用连接。
- 简历相关脚本和生成文档属于个人材料，不应混入项目功能提交。
