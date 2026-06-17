# 2026-06-17 MinerU 标准 batch 轮询假超时

## 现象

配置 `MINERU_API_TOKEN` 后，PDF 入库进入 MinerU standard 模式。日志显示：

- `POST https://mineru.net/api/v4/file-urls/batch` 成功返回。
- 文件 `PUT` 上传成功。
- 后续一直轮询 `GET https://mineru.net/api/v4/extract/task/{batch_id}`。
- 本地最终走到 `TIMEOUT`，入库侧报 `parser mineru-pdf-adapter returned empty content for file_type=pdf` 或使用 PDF 文本兜底。

## 根因

`/api/v4/file-urls/batch` 返回的是批处理 `batch_id`，不是单任务 `task_id`。

原实现把 `batch_id` 赋值给 `task_id`，随后查 `/api/v4/extract/task/{batch_id}`。该端点面向单任务查询，不能正确返回 batch 文件的解析结果。由于 parser 对轮询阶段 `code != 0` 的响应直接 `continue`，错误没有暴露出来，最终表现为一直轮询直到超时。

正确链路是：

```text
POST /api/v4/file-urls/batch
-> PUT file_urls[0]
-> GET /api/v4/extract-results/batch/{batch_id}
-> data.extract_result[0].state / full_zip_url / err_msg
```

## 修复

- `MinerUPdfParser` 在 standard 文件上传模式下记录 `batch_id` 和 `standard_file_batch`。
- standard batch 轮询改为 `/api/v4/extract-results/batch/{batch_id}`。
- 从 `data.extract_result` 中选择当前文件结果，读取 `state`、`full_zip_url`、`markdown_url`、`err_msg`。
- timeout metadata 增加 `last_poll_error`，以后非 0 响应不会完全不可见。
- 新增 standard batch 成功和失败回归测试，断言不会再请求 `/api/v4/extract/task/{batch_id}`。

## 后续补充：完成态但没有 Markdown URL

后续日志出现：

```text
[MinerU] DONE but no md_url in response
RuntimeError: parser mineru-pdf-adapter returned empty content for file_type=pdf
```

这说明轮询端点已经正确返回 `done`，但结果下载逻辑仍过窄：

- 只从 `extract_result[0]` 读取 `full_zip_url` / `markdown_url`，没有兼容 batch 顶层 `data.full_zip_url`。
- zip 里只尝试读取 `.md` 文件，没有兼容 MinerU 常见的 `content_list.json`。
- zip 下载 / 解包异常被吞掉后只打印没有 `md_url`，空内容错误缺少 parser metadata。

补充修复：

- 递归扫描 `result_payload` 和 batch 顶层 `poll_data`，识别 zip / markdown URL。
- zip 中优先读取 `.md` / `.markdown`；若没有 Markdown，则解析 `.json`，优先 `content_list.json`，提取 text、table、caption、latex、html 等字段。
- completed metadata 增加 `result_source` 与 `last_poll_error`。
- `IngestService` 空内容错误补充 parser `status`、`error` / `last_poll_error`。
- 新增 `done + 顶层 full_zip_url + content_list.json` 回归测试。

## 验证

```powershell
& 'C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe' -m pytest tests\test_mineru_pdf_parser.py -q
& 'C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe' -m pytest -q
```

结果：

- `tests/test_mineru_pdf_parser.py`: 6 passed。
- AI 服务全量测试：57 passed。
- pytest cache 权限 warning 不影响测试结果。
