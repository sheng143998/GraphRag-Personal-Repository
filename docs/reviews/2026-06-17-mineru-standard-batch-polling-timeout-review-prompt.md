# 审查提示：MinerU 标准 batch 轮询假超时修复

请审查本次 MinerU PDF parser 修复，重点关注：

- standard 文件上传模式是否正确区分 `batch_id` 和单任务 `task_id`。
- `POST /api/v4/file-urls/batch` 后是否轮询 `/api/v4/extract-results/batch/{batch_id}`，而不是 `/api/v4/extract/task/{batch_id}`。
- `extract_result` 多文件数组选择逻辑是否足够稳妥，单文件入库是否读取第一项结果。
- 当 `full_zip_url` / `markdown_url` 出现在 batch 顶层 `data` 或更深层嵌套字段时，递归 URL 识别是否能覆盖。
- zip 结果中没有 `.md` 但存在 `content_list.json` 时，JSON 文本提取是否足够保守且不会产生大量重复内容。
- completed / failed / timeout 三类状态是否都能返回可诊断 metadata。
- 空解析文本抛错是否携带 parser `status` 和 `last_poll_error`，便于后续日志定位。
- agent 模式和 standard URL 模式是否保持原有行为。
- 测试是否覆盖 standard batch 成功、失败、done 后顶层 zip + content_list.json，以及原有 timeout / markdown metadata 回归。

验证命令：

```powershell
& 'C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe' -m pytest tests\test_mineru_pdf_parser.py -q
& 'C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe' -m pytest -q
```
