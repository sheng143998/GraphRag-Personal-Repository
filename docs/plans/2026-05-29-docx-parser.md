# 2026-05-29 Word (.docx) 解析器 — python-docx 接入 AI 服务

## 背景
AI 服务当前所有解析器均为 stub（`PlainTextParser`），`DocxParser` 只是简单的 `strip()`。需要接入 python-docx 实现真正的 Word 文档文本提取。

## 实现方案
1. 安装 `python-docx` 依赖
2. `DocumentPayload` 新增 `content_base64: str | None` 字段，支持二进制内容
3. 重写 `DocxParser.parse()` — 从 base64 解码后用 python-docx 提取段落文本
4. 更新 `InlineContentLoader` 支持 base64 解码

## 涉及文件
- `ai-service/app/schemas/ingest.py` — DocumentPayload 新增 content_base64
- `ai-service/app/rag/parsers/base.py` — DocxParser 重写
- `ai-service/app/rag/loaders/base.py` — InlineContentLoader 支持 base64
- `ai-service/requirements.txt` — 新增 python-docx

## 验证方式
- Python compileall
- 直接调用 AI ingest API，传入 base64 编码的 .docx 内容
