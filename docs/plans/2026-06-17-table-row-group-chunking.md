# 2026-06-17 表格行组 Chunk 切分

## 目标

按照 chunk 优化优先级第 1 项，为 Excel / CSV 表格类文件增加 `table-row-group` 切分策略，避免继续用字符窗口切表格内容。

## 范围

- AI 服务新增表格行组 chunker。
- 表格文件自动路由到 `table-row-group`。
- CSV / 管道表格文本按表头和行组生成 chunk。
- chunk metadata 保留 sheet、行范围、列名和行组信息。
- Spring Boot 和前端不实现 RAG / chunking 算法。

## 实现要点

- `TableRowGroupChunker` 将表格内容组织为：
  - `Sheet: ...`
  - `Columns: ...`
  - `Row N: column=value | ...`
- metadata 新增 / 使用：
  - `chunk_strategy=table-row-group`
  - `chunk_algorithm=table-row-group`
  - `block_type=table_rows`
  - `sheet_name`
  - `row_range`
  - `row_start`
  - `row_end`
  - `column_names`
  - `row_group_index`
- 默认 `table_row_group_size=25`，可通过 metadata 覆盖。

## 验证

```powershell
cd ai-service
.\.venv\bin\python.exe -m pytest tests\test_parent_child_chunker.py -q
.\.venv\bin\python.exe -m pytest tests\test_parent_child_chunker.py tests\test_advanced_rag_strategy.py -q
```

## 后续

- 下一优先级是 Markdown block-aware chunking：代码块保持原子、图片链接单独标记。
- 后续可增强 `SpreadsheetParser`，直接解析真实 `.xlsx` workbook 的 sheet / rows，而不是只依赖解析后的文本。
