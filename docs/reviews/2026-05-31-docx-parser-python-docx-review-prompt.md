# Review: 2026-05-31 Word (.docx) 解析器 — python-docx 接入 AI 服务

## 变更概述
将 AI 服务 `DocxParser` 从 stub（继承 `PlainTextParser`，仅 `strip()`）升级为真正的 Word 文档解析器，接入 python-docx 库提取段落和表格文本。

## 需要 Review 的文件

### 1. `ai-service/app/schemas/ingest.py`
- `DocumentPayload` 新增 `content_base64: str | None = None` 字段
- 向前兼容，不影响现有调用方

### 2. `ai-service/app/rag/parsers/base.py` — DocxParser (L38-L79)

- 从继承 `PlainTextParser` 改为继承 `BaseParser`
- 版本从隐式 v1 升级为显式 `v2`
- 核心逻辑：
  - 优先从 `content_base64` 获取 base64 内容（回退到 `content`）
  - base64 解码后用 `python-docx.Document` 解析
  - 提取所有段落文本（`para.text`）
  - 提取所有表格文本（`cell.text`，用 ` | ` 分隔）
  - 异常时静默回退，不影响整体流程
- 需确认：异常处理是否过于宽松？是否需要记录解析失败日志？

### 3. `ai-service/app/rag/loaders/base.py` — InlineContentLoader (L8-L14)
- 新增 base64 解码逻辑：若 `content_base64` 非空，先解码再返回 UTF-8 文本
- 解码失败回退到 `payload.content`

### 4. `ai-service/pyproject.toml`
- 新增依赖声明 `"python-docx>=1.1.0,<2.0.0"`
- 注意：实际运行时依赖通过 MSYS2 pacman 安装，pyproject.toml 仅作声明

### 5. `ai-service/.venv/lib/python3.12/site-packages/system-packages.pth`
- 新增 `.pth` 文件，引用系统 site-packages：`C:\msys64\mingw64\lib\python3.12\site-packages`
- 需确认：此方案是否适合长期维护？是否应在 Docker 中统一管理依赖？

## 验证结果
- Python compileall 全量通过（0 errors）
- 未运行集成测试（需实际 .docx 文件 + 运行中 AI 服务）

## 待讨论
1. 异常处理是否应记录 warning 日志而非完全静默？
2. 是否需要支持页眉/页脚/文本框提取？
3. `.pth` 方案的长期可行性 vs Docker 统一管理
