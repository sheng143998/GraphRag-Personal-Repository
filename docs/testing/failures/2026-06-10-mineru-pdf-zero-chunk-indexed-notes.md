# 2026-06-10 MinerU PDF 解析超时导致 0 chunk 仍标记成功

## 问题现象

上传 PDF 后，前端显示文档已经入库成功，`documents` 表也能看到 PDF 记录，但 `document_chunks` 没有对应 chunk。

## 日志证据

Java 侧：

- `POST /api/documents/upload` 先返回 200，文档进入异步处理。
- 异步处理结束时出现 `chunks=0, parser=mineru-pdf-adapter, fileType=pdf`。
- 旧逻辑仍将文档状态更新为 `INDEXED`。

Python 侧：

- MinerU `POST /api/v1/agent/parse/file` 返回 `code=0` 和 `task_id`。
- 后续轮询一直是 `waiting-file`。
- 120 秒后出现 `TIMEOUT after 120s`。
- 旧逻辑返回 HTTP 200，且 `chunk_count=0`。

## 根因

这不是 chunk 写库 SQL 漏执行，而是解析结果为空却被当成成功：

1. `MinerUPdfParser` 在 MinerU timeout / failed / 空 Markdown 时返回空文本。
2. `IngestService` 没有校验 `parsed_content.text` 是否为空。
3. `SimpleChunker` 对空文本返回空列表。
4. `IngestService` 没有校验 `chunks` 是否为空，继续返回成功响应。
5. `DocumentIngestProcessor` 只看 AI 服务 HTTP 成功，不检查 `chunk_count`，最终把 Java 文档标记成 `INDEXED`。

## 修复方案

- AI 服务：解析结果为空时直接抛错，不再进入保存 document / chunk 的成功路径。
- AI 服务：chunker 产出为空时直接抛错。
- PDF parser：MinerU timeout / failed / done 但 Markdown 为空时，先尝试使用兜底文本提取结果。
- Java 后端：AI ingest 响应为空或 `chunk_count <= 0` 时，视为入库失败，文档状态写为 `FAILED`。
- 测试：新增 Java 单测覆盖 `chunk_count=0` 必须失败；新增 Python 单测覆盖 MinerU timeout 兜底文本。

## 验证

- `mvn.cmd -f backend-java/pom.xml test`
- `mvn.cmd -f backend-java/pom.xml -Dtest=DocumentIngestProcessorTest test`
- `.\ai-service\.venv\bin\python.exe -m pytest ai-service/tests/test_mineru_pdf_parser.py ai-service/tests/test_basic_rag_pipeline.py -q`
- `.\ai-service\.venv\bin\python.exe -m py_compile ai-service/app/rag/parsers/base.py ai-service/app/services/ingest_service.py ai-service/tests/test_mineru_pdf_parser.py`

## 后续建议

- 如果 MinerU 长时间保持 `waiting-file`，需要检查它的 Agent API 文件上传参数是否与当前账号 / API 版本匹配。
- 后续可以把 MinerU poll timeout 做成环境变量，避免大 PDF 被固定 120 秒截断。
- 可增加一个“重新解析文档”接口，用于修复历史上已经被错误标成 `INDEXED` 但 chunk 数为 0 的文档。
