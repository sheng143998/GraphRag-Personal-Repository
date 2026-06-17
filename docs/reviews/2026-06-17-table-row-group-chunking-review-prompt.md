# 2026-06-17 表格行组 Chunk 切分 Review Prompt

请重点 review AI 服务表格文件入库切分逻辑：

- `ai-service/app/rag/chunkers/base.py`
  - `TableRowGroupChunker` 是否按表头和行组稳定生成 chunk。
  - CSV / Markdown 管道表格解析是否有明显边界问题。
  - `sheet_name`、`row_range`、`column_names`、`block_type` 等 metadata 是否足够支持检索和引用。
- `ai-service/app/services/ingest_service.py`
  - `csv` / `xls` / `xlsx` 是否自动路由到 `table-row-group`。
  - 既有 parent-child 自动降级逻辑是否不受影响。
- `ai-service/tests/test_parent_child_chunker.py`
  - 表格行组切分断言是否覆盖策略、列名、sheet 和行范围。

验证命令：

```powershell
cd ai-service
.\.venv\bin\python.exe -m pytest tests\test_parent_child_chunker.py -q
.\.venv\bin\python.exe -m pytest tests\test_parent_child_chunker.py tests\test_advanced_rag_strategy.py -q
```

已知限制：

- 当前 `SpreadsheetParser` 仍主要处理文本内容，真实 `.xlsx` workbook 的 sheet 级解析后续再增强。
