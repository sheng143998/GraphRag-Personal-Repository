# 2026-06-17 Block-aware / QA / Code Chunking

## 要解决的问题

继续优化 AI 服务文档入库切分，避免 Markdown 代码块和图片链接被普通文本窗口打散，同时让 DOCX、PDF、面试问答和代码片段保留更强结构 metadata，方便后续检索、引用和评测归因。

## 当前背景

- FastAPI AI 服务负责文档解析、切分、embedding、检索和 RAG 派生数据写入。
- Spring Boot 和前端不实现 RAG / chunking 算法，只透传文档类型、文件类型和 metadata。
- 已有 `recursive-overlap`、`parent-child`、`table-row-group` 策略，本次在此基础上继续补结构化切分能力。

## 涉及模块

- `ai-service/app/rag/chunkers/base.py`
- `ai-service/app/rag/parsers/base.py`
- `ai-service/app/services/ingest_service.py`
- `ai-service/tests/test_parent_child_chunker.py`
- `ai-service/tests/test_docx_parser.py`
- `ai-service/tests/test_mineru_pdf_parser.py`

## 实现策略

- Markdown block-aware：
  - fenced code block 作为原子单元，`split_level=code-block`，不参与普通段落合并。
  - 图片引用行作为原子单元，`split_level=image-reference`，继续由质量分类标记为 `block_type=image_caption`。
- DOCX 结构保留：
  - Word `Heading 1..6` 段落转换为 Markdown 标题。
  - Word 表格转换为 Markdown pipe table，并记录 `heading_count`、`table_count`。
- PDF MinerU metadata 强化：
  - MinerU 完成态 Markdown 增加标题、图片、表格、代码块、公式和页标记统计。
  - metadata 字段统一以 `mineru_*` 前缀记录，方便检索归因和后续版面质量评估。
- Q&A chunker：
  - 面试经验默认路由到 `qna-pair`。
  - 识别 `Q:` / `Question:` / `问题:` 与 `A:` / `Answer:` / `答案:` / `回答:`，每组问答生成一个 chunk。
  - metadata 保留 `question_text`、`answer_text`、`qa_pair_index`、`qa_question_type`。
- code-aware chunker：
  - 代码片段默认路由到 `code-aware`。
  - 优先保留 fenced code block；裸代码按顶层函数、类或方法符号切分。
  - metadata 保留 `language`、`symbol_name`、`symbol_type`、`start_line`、`end_line`。

## 重点 review 文件

- `ai-service/app/rag/chunkers/base.py`
  - Markdown 原子块、Q&A chunker、code-aware chunker 的边界行为。
- `ai-service/app/rag/parsers/base.py`
  - DOCX 标题/表格转换与 MinerU metadata 统计。
- `ai-service/app/services/ingest_service.py`
  - `interview_experience -> qna-pair`、`code_snippet -> code-aware` 路由。
- `ai-service/tests/test_parent_child_chunker.py`
  - 入库路由、Q&A、代码切分、Markdown 原子块回归。

## 测试计划

```powershell
cd ai-service
.\.venv\bin\python.exe -m pytest tests\test_parent_child_chunker.py -q
.\.venv\bin\python.exe -m pytest tests\test_parent_child_chunker.py tests\test_advanced_rag_strategy.py tests\test_docx_parser.py tests\test_mineru_pdf_parser.py -q
```

## 已知风险

- code-aware 当前是轻量正则切分，不是语言 AST 解析；复杂嵌套、装饰器、泛型和多语言混排后续可按语言引入 tree-sitter 或 AST 解析器。
- Q&A chunker 主要覆盖显式问答格式；自由文本面试复盘仍会 fallback 到 `recursive-overlap`。
- MinerU block metadata 目前基于 Markdown 输出统计，不替代 MinerU 原始 layout block 坐标。
