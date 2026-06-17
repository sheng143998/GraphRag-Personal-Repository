# 2026-06-17 Block-aware / QA / Code Chunking Review Prompt

请重点 review AI 服务文档入库切分增强：

- `ai-service/app/rag/chunkers/base.py`
  - Markdown fenced code block 是否保持原子 chunk，不被 recursive overlap 拆开。
  - Markdown 图片引用是否单独标记为 `split_level=image-reference`，并继续降权为图片说明类弱证据。
  - `QAPairChunker` 是否能稳定识别常见 Q/A、Question/Answer、问题/答案格式，并在没有问答对时 fallback。
  - `CodeAwareChunker` 是否优先保留 fenced code block，并能对裸 Python / JS / Java 风格代码按函数、类、方法切分。
  - chunk metadata 是否保留足够的检索归因字段：`question_text`、`answer_text`、`language`、`symbol_name`、`start_line`、`end_line`。
- `ai-service/app/rag/parsers/base.py`
  - DOCX 解析是否跳过 base64 原文噪声，并保留标题与表格结构。
  - MinerU PDF 完成态 metadata 是否覆盖 heading、image、table、code、formula、page marker 统计。
- `ai-service/app/services/ingest_service.py`
  - `interview_experience` 是否默认路由到 `qna-pair`。
  - `code_snippet` 是否默认路由到 `code-aware`。
  - 显式 `chunk_strategy` override 是否仍然优先生效。
- `ai-service/tests/`
  - 是否覆盖 Markdown 原子块、DOCX 标题表格、MinerU metadata、Q&A、code-aware 和入库路由回归。

验证命令：

```powershell
cd ai-service
.\.venv\bin\python.exe -m pytest tests\test_parent_child_chunker.py -q
.\.venv\bin\python.exe -m pytest tests\test_parent_child_chunker.py tests\test_advanced_rag_strategy.py tests\test_docx_parser.py tests\test_mineru_pdf_parser.py -q
```

已知限制：

- code-aware 目前是正则级轻量切分，不是 AST 级语义切分。
- MinerU metadata 是基于 Markdown 结果的 block 统计，不包含原始坐标框。
