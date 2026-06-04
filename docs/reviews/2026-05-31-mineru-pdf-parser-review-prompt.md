# Review: 2026-05-31 MinerU PDF 解析器 — 接入 MinerU Agent API

## 变更概述
将 `MinerUPdfParser` 从 reserved stub 升级为真正的 PDF 解析器，接入 MinerU Agent 轻量 API（无需 Token，异步提交+轮询）。

## 需要 Review 的文件

### 1. `ai-service/app/core/config.py` — 新增 MinerU 配置
- `mineru_api_base_url: str` — 默认 `https://mineru.net/api/v1/agent`
- `mineru_api_token: str` — 默认空（Agent API 无需 Token）
- 均支持 `.env` 覆盖：`MINERU_API_BASE_URL` / `MINERU_API_TOKEN`

### 2. `ai-service/app/rag/parsers/base.py` — MinerUPdfParser (v1)
- 版本从 `reserved-v1` 升级为 `v1`
- 核心流程：
  1. 从 `source_path` / `content` 获取 PDF URL
  2. `POST {base_url}/parse/url` 提交解析任务
  3. 轮询 `GET {base_url}/parse/{task_id}`（间隔 2s，超时 120s）
  4. `state=done` → 下载 markdown CDN → 返回文本
  5. `state=failed` → 返回错误 metadata
- 使用 `httpx.AsyncClient` 异步 HTTP 调用
- 完整错误处理：submit_failed / submit_error / timeout / failed

### 3. `ai-service/pyproject.toml`
- 新增依赖声明 `"httpx>=0.27.0,<1.0.0"`

### 4. `docs/plans/2026-05-31-mineru-pdf-parser.md`
- 实施计划文档

## 验证结果
- Python compileall 全量通过
- 未运行集成测试（需真实 MinerU API 调用 + PDF URL）

## 关于 .env

当前 Agent API 无需 Token 即可使用。如需切换为标准精准解析 API，请在 `.env` 中配置：
```
MINERU_API_BASE_URL=https://mineru.net/api/v4
MINERU_API_TOKEN=your_token_here
```

## 待讨论
1. 是否需要支持文件上传模式（`/parse/file`）？当前仅支持 URL 模式
2. 是否需要支持批量解析？
3. 超时和轮询间隔是否需要可配置？
