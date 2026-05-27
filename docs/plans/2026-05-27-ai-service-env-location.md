# 2026-05-27 AI 服务环境配置定位计划

## 要解决的问题

用户需要找出 `ai-service` 的 `.env` 配置文件位置，并确认 AI 服务实际从哪里读取环境变量。

## 调研过程中发现的重要信息

- `ai-service/` 目录下没有 `.env`、`.env.*` 或 `*.env` 文件。
- 项目根目录存在 `.env.example`，其中包含 AI 服务相关配置示例。
- AI 服务配置入口是 `ai-service/app/core/config.py`。
- `config.py` 通过系统环境变量读取 `AI_DATABASE_URL`，如果没有则读取 `DATABASE_URL`。

## 涉及模块

- `ai-service`
- 根目录环境变量模板
- 项目交接文档

## 验证方式

- 使用文件搜索查找 `ai-service` 下的 `.env` 相关文件。
- 使用全项目文件搜索确认项目自有环境模板。
- 读取 `ai-service/app/core/config.py` 确认实际配置读取逻辑。
- 读取根目录 `.env.example` 确认 AI 服务变量示例。

## 当前风险

- 项目根目录可能存在用户本地 `.env`，但当前工作区搜索结果未发现。
- 真实密码不能写入文档，只能说明变量名和文件位置。
