# 2026-06-09 AI Agent 请求入口日志补齐计划

## 背景

知识库对话报错时，Spring Boot 日志显示 Java 调用 AI Agent 接口读取超时，但 FastAPI 控制台没有明显日志，无法判断请求是否真正到达 Python 服务。

## 目标

- FastAPI 收到任何 `/ai/*` 请求时都打印开始 / 完成 / 失败日志
- `/ai/agent/invoke` 打印 Agent 调用参数摘要和完成摘要
- Agent 工作流内部打印开始 / 完成 / 失败耗时

## 改动

- `ai-service/app/main.py` 新增 HTTP middleware，记录 `method`、`path`、`status`、`durationMs`、`traceId`
- `ai-service/app/api/routes/agent.py` 新增 Agent invoke 入口和完成日志
- `ai-service/app/services/agent_service.py` 新增 Agent workflow 开始、失败、完成日志
- Python 日志文本使用 ASCII，避免 Windows 控制台编码导致日志乱码

## 验证

- `ai-service/.venv/bin/python.exe -m py_compile ai-service/app/main.py ai-service/app/api/routes/agent.py ai-service/app/services/agent_service.py`
- `mvn.cmd -q -DskipTests compile`
