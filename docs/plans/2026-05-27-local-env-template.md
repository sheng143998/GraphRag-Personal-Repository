# 2026-05-27 本地 `.env` 空字段配置

## 背景

当前 RAG 实验接口 HTTP smoke 被本地 PostgreSQL 凭据阻塞。用户希望先在项目根目录创建一个 `.env` 文件，字段留空，由用户自行补全本机数据库连接信息。

## 当前目标

创建根目录 `.env`，只写入环境变量名，不写入真实密码、账号或连接串。

## 涉及模块

- 根目录本地环境配置
- 项目过程文档

## 预计修改文件

- `.env`
- `docs/reviews/2026-05-27-local-env-template-review-prompt.md`
- `docs/testing/failures/2026-05-27-local-env-template-notes.md`
- `docs/handoff/CURRENT_STATE.md`

## 非范围

- 不写入真实数据库密码。
- 不修改 `.env.example`。
- 不启动数据库或后端服务。

## 验证方式

- 确认 `.env` 文件存在。
- 确认 `.env` 字段值为空。
- 确认 `.gitignore` 已忽略 `.env`。

## 当前风险

- Spring Boot 本身不会自动读取根目录 `.env`；如果通过 Maven/PowerShell 启动，需要后续由启动脚本或终端环境变量加载这些字段。
