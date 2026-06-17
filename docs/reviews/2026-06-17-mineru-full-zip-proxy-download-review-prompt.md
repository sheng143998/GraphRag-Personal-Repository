# 审查提示：MinerU full_zip_url 代理绕过修复

请审查本次 MinerU 结果下载修复，重点关注：

- 是否只对结果 zip / markdown 下载使用 `trust_env=False`，不影响提交、上传、轮询阶段的既有网络行为。
- `follow_redirects=True` 是否适合签名 URL / CDN 场景。
- zip 和 markdown 下载失败时，`last_poll_error` 是否仍保留可诊断信息。
- 单元测试是否断言结果下载客户端使用 `trust_env=False`。
- 是否存在需要把该行为做成环境变量开关的场景。

验证命令：

```powershell
& 'C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe' -m pytest tests\test_mineru_pdf_parser.py -q
& 'C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe' -m pytest -q
```
