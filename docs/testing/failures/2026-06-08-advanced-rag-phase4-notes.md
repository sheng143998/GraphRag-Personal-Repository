# 2026-06-08 Advanced RAG Phase 4 验证记录与问题复盘

## 问题一：当前 shell Python 缺少 pytest / pydantic

### 问题现象

执行：

```powershell
pytest ai-service/tests -q
```

失败：

```text
pytest: 无法将 pytest 识别为 cmdlet
```

继续执行：

```powershell
python -m pytest ai-service/tests -q
```

失败：

```text
No module named pytest
```

执行 Python import smoke：

```powershell
python -c "import sys; sys.path.insert(0, 'ai-service'); from app.services.rag_service import RagService"
```

失败：

```text
ModuleNotFoundError: No module named 'pydantic'
```

### 根因分析

当前 shell 使用的 Python 环境没有安装 AI 服务运行依赖和测试依赖。`python -m compileall ai-service/app` 只能做语法编译，不会实际 import 外部依赖，因此可以通过；但 import smoke 和 pytest 需要 `pydantic`、`pytest` 等依赖。

### 处理方式

本轮记录为环境依赖缺失，未在项目中新增依赖或提交真实环境配置。已完成以下可执行验证：

- `python -m compileall ai-service/app` 通过。
- `mvn compile -q -f backend-java/pom.xml` 通过。
- `npm run build` 通过。

### 后续建议

后续需要在 AI 服务虚拟环境或项目标准 Python 环境中安装依赖后再执行：

```powershell
python -m pytest ai-service/tests -q
```

如果项目后续固定使用 venv，应在 `ai-service/README.md` 中明确创建、激活和安装依赖命令。

## 问题二：PowerShell 写 Java 文件时引入 UTF-8 BOM

### 问题现象

修改 `RagService.java` 后执行：

```powershell
mvn compile -q -f backend-java/pom.xml
```

失败，报错包含：

```text
非法字符: '\ufeff'
```

### 根因分析

使用 PowerShell / .NET 写文件时默认 UTF-8 编码可能带 BOM，Java 编译器将文件开头 BOM 识别为非法字符。

### 修复方案

使用无 BOM UTF-8 重新写入文件：

```powershell
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($path, $text, $utf8NoBom)
```

修复后 `mvn compile` 通过。

### 后续避免方式

后续修改 Java / Python / TypeScript 文件时，尽量使用专用 Edit/Write 工具；若必须用 PowerShell 写入文件，需要显式使用 `UTF8Encoding($false)`。
## 2026-06-08 OpenAI-compatible adapter parser tests

新增 `ai-service/tests/test_openai_compatible_adapters.py` 覆盖：

- embedding 响应按 `index` 排序；
- rerank `results` 响应按原始 document index 还原；
- rerank `output.results` 形态兼容；
- 直接 `scores` 列表不足时补 0。

当前 shell 运行：

```powershell
python -m pytest ai-service/tests/test_openai_compatible_adapters.py -q
```

失败原因仍是本地 Python 环境缺少 `pytest`：

```text
No module named pytest
```

处理建议：进入 AI 服务依赖环境后重新运行该测试与全量 `ai-service/tests`。
## 2026-06-08 全链路 HTTP smoke 阻塞

尝试检查 Docker：

```powershell
docker --version
if ($?) { docker compose ps }
```

结果：Docker CLI 存在，但 Docker Desktop daemon 未运行，无法连接 `dockerDesktopLinuxEngine`。因此当前环境暂不能启动 `docker-compose.yml` 中的 PostgreSQL / Redis，也不能完成 FastAPI + Spring Boot + 数据库的全链路 HTTP smoke。

处理建议：启动 Docker Desktop 后执行：

```powershell
scripts/dev-start.ps1
```

再分别启动 AI 服务、Java 后端和前端进行 `/api/rag/query` 多策略验证。