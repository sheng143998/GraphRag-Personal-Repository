# 2026-05-31 Word (.docx) 解析器 — python-docx 接入 AI 服务

## 背景
AI 服务 `DocxParser` 原为 stub（继承 `PlainTextParser`，仅 `strip()`）。需接入 python-docx 实现真正的 Word 文档文本提取。

## 实现方案
1. MSYS2 pacman 安装 `mingw-w64-x86_64-python-docx`（含预编译 lxml）
2. venv 通过 `.pth` 文件引用系统 site-packages
3. `DocumentPayload` 新增 `content_base64: str | None` 字段
4. `DocxParser` 重写 — 继承 `BaseParser`，base64 解码后用 python-docx 提取段落和表格文本
5. `InlineContentLoader` 支持 base64 解码
6. `pyproject.toml` 添加 `python-docx>=1.1.0,<2.0.0` 依赖声明

## 涉及文件

- `ai-service/app/schemas/ingest.py` — DocumentPayload 新增 content_base64
- `ai-service/app/rag/parsers/base.py` — DocxParser 重写为 v2
- `ai-service/app/rag/loaders/base.py` — InlineContentLoader 支持 base64
- `ai-service/pyproject.toml` — 依赖声明
- `ai-service/.venv/lib/python3.12/site-packages/system-packages.pth` — 系统包引用

## 验证方式
- Python compileall 全量通过
