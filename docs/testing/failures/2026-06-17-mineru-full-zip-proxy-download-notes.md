# 2026-06-17 MinerU full_zip_url 下载受系统代理影响

## 现象

PDF 进入 MinerU standard batch 模式后，提交、上传、轮询均成功，轮询最终返回 `done` 和 `full_zip_url`。但 AI 服务下载结果 zip 失败，入库报错：

```text
RuntimeError: parser mineru-pdf-adapter returned empty content for file_type=pdf,
status=completed,
error=done_without_result_content; errors=zip:ConnectError
```

## 诊断

使用两个 Python 环境分别验证：

- `ai-service\.venv`
- `C:\Users\admin\PyCharmMiscProject\.venv`

结论一致：

- `POST https://mineru.net/api/v4/file-urls/batch` 成功，`code=0`。
- 文件上传成功，HTTP 200。
- `GET /api/v4/extract-results/batch/{batch_id}` 成功返回 `done`。
- `full_zip_url` 存在，域名为 `cdn-mineru.openxlab.org.cn`。
- 使用 `httpx` 默认 `trust_env=True` 下载 zip 报 `ConnectError`。
- 使用 `trust_env=False` 下载同一个签名 zip 返回 HTTP 200，`content-type=application/zip`。

系统层面 `Test-NetConnection cdn-mineru.openxlab.org.cn -Port 443` 是通的，因此不是基础 TCP 不通，而是 Python `httpx` 继承系统代理环境变量后，代理路径访问 MinerU CDN 失败。

## 修复

`MinerUPdfParser` 保持提交、上传和轮询阶段使用默认 `httpx.AsyncClient` 行为；只在下载 `full_zip_url` / `markdown_url` 时使用独立客户端：

```python
httpx.AsyncClient(
    timeout=httpx.Timeout(120.0, connect=10.0),
    trust_env=False,
    follow_redirects=True,
)
```

这样既不影响 `mineru.net` API 访问，也绕开了 `cdn-mineru.openxlab.org.cn` 在本机代理路径下的 `ConnectError`。

## 验证

```powershell
& 'C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe' -m pytest tests\test_mineru_pdf_parser.py -q
& 'C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe' -m pytest -q
```

结果：

- MinerU parser 定向测试：6 passed。
- AI 服务全量测试：57 passed。
- 真实连通性探针：API `code=0`、上传 200、轮询 `done`、`trust_env=False` 下载 zip HTTP 200。
