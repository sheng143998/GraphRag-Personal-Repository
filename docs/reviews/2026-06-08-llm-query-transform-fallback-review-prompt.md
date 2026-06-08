# 审查提示：LLM 查询转换回退

请审查按请求启用的 LLM 查询转换实现。

重点关注：

- 该能力默认关闭，只能通过 retrieval options 显式启用。
- LLM 输出无效、为空或不符合预期时，应回退到现有规则转换器。
- Advanced RAG trace payload 在相关场景中应标识 provider 与 fallback reason。
- Spring Boot 和前端应继续只承担 API 桥接与 UI 职责。
- 使用 stub provider 时，现有全链路行为应保持通过。

验证命令：

```powershell
cd ai-service
.\.venv\bin\python.exe -m pytest tests/test_advanced_rag_strategy.py -q
.\.venv\bin\python.exe -m pytest tests -q
```

```powershell
python -m py_compile smoke_test.py
powershell -ExecutionPolicy Bypass -File .\scripts\test-fullchain-local.ps1
```
