# 基础设施模块

## 模块职责

`infra/` 保存本地开发依赖的初始化和预留配置。当前重点是 PostgreSQL + pgvector，后续可继续加入 Redis、对象存储、反向代理和容器编排配置。

## 技术栈

- PostgreSQL
- pgvector
- Docker Compose
- 预留 Redis / nginx / docker 配置目录

## 目录结构

```text
infra/
├── postgres/
│   └── init.sql       # PostgreSQL 初始化脚本
├── docker/            # 容器配置预留
└── nginx/             # 反向代理配置预留
```

## 本地启动

通常从项目根目录通过脚本启动：

```powershell
.\scripts\dev-start.ps1
```

也可以直接使用 Docker Compose：

```powershell
docker compose up -d
docker compose ps
docker compose logs
docker compose down
```

## 环境变量

- `POSTGRES_DB`：数据库名。
- `POSTGRES_USER`：数据库用户名。
- `POSTGRES_PASSWORD`：数据库密码。
- `DB_URL` / `DB_USERNAME` / `DB_PASSWORD`：Java 和 Python 共同使用的统一数据库配置。

真实密码只放在本地环境，不写入仓库。

## 关键文件

- `infra/postgres/init.sql`：数据库初始化入口。
- `docker-compose.yml`：本地依赖编排入口。
- `backend-java/src/main/resources/db/migration/`：共享数据库 schema 的 Flyway 迁移目录。

## 当前能力

- PostgreSQL 本地依赖。
- pgvector 扩展基础依赖。
- 支持业务数据、document chunks、embeddings、RAG runs、retrieval results、evaluation cases、evaluation history 和 graph facts。

## 后续优化

- 补充 Redis 作为缓存 / 任务队列依赖。
- 增加数据卷说明和备份恢复说明。
- 增加集成测试环境启动脚本。
- 如果批量评测改为异步任务，补充对应队列基础设施说明。
