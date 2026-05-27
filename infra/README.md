# 基础设施模块

## 模块职责

基础设施模块用于保存本地开发依赖的配置和初始化脚本。当前重点是 PostgreSQL 与 pgvector，后续可以继续加入 Redis、对象存储、反向代理和容器编排配置。

## 技术栈

- PostgreSQL。
- pgvector。
- Docker Compose。
- 后续预留 Redis。

## 目录结构说明

```text
infra/
├─ postgres/
│  └─ init.sql       # PostgreSQL 初始化脚本
├─ docker/           # 容器配置预留目录
└─ nginx/            # 反向代理配置预留目录
```

## 本地启动方式

基础设施通常通过根目录脚本启动。

```powershell
.\scripts\dev-start.ps1
```

也可以根据 `docker-compose.yml` 手动启动本地依赖。

```powershell
docker compose up -d
```

## 常用命令

```powershell
docker compose up -d
docker compose ps
docker compose logs
docker compose down
```

## 环境变量说明

- `POSTGRES_DB`：数据库名称。
- `POSTGRES_USER`：数据库用户名。
- `POSTGRES_PASSWORD`：数据库密码。

真实密码只放在本地环境或本机配置中，不写入仓库文档。

## 关键代码入口

- `postgres/init.sql`：数据库初始化入口。
- 根目录 `docker-compose.yml`：本地依赖编排入口。
- `scripts/dev-start.ps1`：本地依赖启动脚本。
- `scripts/dev-stop.ps1`：本地依赖停止脚本。

## 重点审查文件

- `postgres/init.sql`
- 根目录 `docker-compose.yml`
- `scripts/dev-start.ps1`
- `scripts/dev-stop.ps1`
- Java 后端迁移目录：`backend-java/src/main/resources/db/migration/`

## 与其他模块的调用关系

```text
Java 后端
-> PostgreSQL

Python 人工智能服务
-> PostgreSQL
-> pgvector
```

## 当前已实现能力

- PostgreSQL 初始化脚本预留。
- pgvector 作为向量检索扩展的基础依赖。
- 本地开发脚本可统一启动依赖。

## 当前占位实现

- Redis 尚未接入。
- nginx 配置仍是预留目录。
- docker 目录仍是预留目录。

## 后续待补能力

- 明确数据卷策略。
- 增加 Redis。
- 增加更完整的本地初始化说明。
- 增加集成测试环境启动脚本。

## 常见问题

- 如果数据库无法启动，先检查 Docker 是否可用。
- 如果 pgvector 扩展不可用，检查镜像是否包含 vector 扩展。
- 如果迁移失败，先查看 Java 后端 Flyway 日志。
