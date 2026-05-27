# 2026-05-26 Basic RAG 开发失败经验复盘

## 背景

本次任务目标是按 `PROJECT_CONTEXT.md` 优先完成 Basic RAG 主链路：FastAPI 负责 ingest、chunk、embedding、retrieve、generate，Spring Boot 负责对外 API、调用 AI 服务、保存 RAG run 和检索结果，本地 PostgreSQL + pgvector 承载业务数据和向量数据。

开发过程中出现了多处值得沉淀的问题。以下记录用于后续继续开发时快速避坑。

## 问题 1：后端初次验证缺少 Maven 依赖和插件缓存

- 现象：首次运行 Java 后端验证时，Maven 需要下载依赖和插件，本地缓存不足导致验证无法直接完成。
- 触发场景：执行后端测试、打包和启动验证。
- 根因：本地 Maven 仓库不完整，网络默认受限，需要显式允许下载依赖。
- 解决方案：获得网络权限后补齐 Maven 依赖和插件缓存，再运行后端验证。
- 后续避免：首次接手本项目时，先确认 Maven 依赖是否已缓存；如果没有缓存，应把依赖下载作为环境准备步骤记录清楚。
- 自动化测试：已重新运行 `mvn clean test`、`mvn package -DskipTests` 和后端健康检查。

## 问题 2：数据库账号、密码和数据库名需要先确认

- 现象：后端启动和 Flyway 迁移前，本地 PostgreSQL 连接信息不明确，数据库 `agent_knowledge` 不存在。
- 触发场景：启动 Spring Boot、执行数据库迁移、验证 `/api/knowledge-bases`。
- 根因：本地环境不是项目默认配置，需要使用用户提供的本机账号密码和数据库名。
- 解决方案：使用本地 PostgreSQL 用户 `postgres`，通过本地环境提供密码；创建 `agent_knowledge` 数据库后再启动后端。
- 后续避免：验证数据库任务时先确认四项：host、port、username、database。密码只保存在本地环境，不写入代码、测试或仓库文档。
- 自动化测试：后端 health、actuator health、knowledge bases 查询均已验证通过。

## 问题 3：`psycopg[binary]` 在当前环境安装失败

- 现象：给 AI 服务新增 PostgreSQL 访问依赖时，`psycopg[binary]` 无法在当前环境解析或安装成功。
- 触发场景：执行 `pip install -e .` 安装 AI 服务依赖。
- 根因：当前 Python 环境和包源条件下，`psycopg-binary` 轮子不可用或解析失败。
- 解决方案：改用纯 Python 驱动 `pg8000`，减少本地编译和平台依赖。
- 后续避免：本项目当前优先使用 `pg8000` 做轻量数据库访问；如果后续换回 psycopg，需要先验证 Windows 本地安装和 CI 环境。
- 自动化测试：切换到 `pg8000` 后，`pip install -e .` 和 `pip install -e ".[dev]"` 均通过。

## 问题 4：`pg8000` cursor 不支持直接作为 context manager

- 现象：使用 `with connection.cursor() as cursor` 时运行失败。
- 触发场景：实现 `PostgresDocumentRepository` 的数据库读写。
- 根因：`pg8000.dbapi` cursor 对象不提供与 psycopg 一致的 context manager 行为。
- 解决方案：在 repository 中增加内部 `_cursor()` context manager，统一创建和关闭 cursor。
- 后续避免：跨数据库驱动时不要假设 cursor、connection 的上下文管理协议完全一致；repository 层封装好驱动差异。
- 自动化测试：AI 服务数据库 ingest 和 query smoke 已走通。

## 问题 5：Pydantic v1 不支持 `model_copy`

- 现象：运行 Python 单测时，reranker 中调用 `model_copy` 报错。
- 触发场景：执行 Basic RAG pipeline 测试。
- 根因：当前项目使用 Pydantic v1，`model_copy` 是 Pydantic v2 API。
- 解决方案：改为 Pydantic v1 兼容的 `copy(update=...)`。
- 后续避免：新增 Pydantic 写法前先确认项目版本；除非整体升级，否则 schema/model 代码保持 v1 API。
- 自动化测试：`.\.venv\bin\python.exe -m pytest` 已通过。

## 问题 6：Java JSONB 字段不能用普通 `String` 承载对象

- 现象：保存 `rag_retrieval_results.metadata` 时出现 JSON 解析异常。
- 触发场景：Spring Boot 保存 FastAPI 返回的 citation metadata。
- 根因：数据库字段是 JSONB，FastAPI 返回的是 JSON 对象；Java 实体中使用 `String` 容易形成二次 JSON 编码或类型不匹配。
- 解决方案：将 `RagRetrievalResult.metadata` 和响应 DTO 中的 metadata 改为 `Map<String, Object>`。
- 后续避免：JSONB 字段如果语义是对象，Java 侧优先用 `Map<String, Object>` 或明确的结构化 DTO，不用裸字符串。
- 自动化测试：完整 Spring -> FastAPI -> PostgreSQL RAG query 已成功保存 run 和 retrieval results。

## 问题 7：PowerShell 直接拼 `curl.exe -d` JSON 容易破坏引号

- 现象：调用 Spring `POST /api/rag/query` 时，后端收到的 JSON 字段缺少双引号，导致请求解析失败。
- 触发场景：在 PowerShell 中直接用 `curl.exe -d "{...}"` 拼接复杂 JSON。
- 根因：PowerShell、curl 和 JSON 字符串转义规则叠加后，双引号容易被吞掉或转义错误。
- 解决方案：改用 PowerShell 对象 `ConvertTo-Json` 生成 JSON，再用 `Invoke-RestMethod` 发送请求。
- 后续避免：Windows 本地验证 HTTP JSON API 时，优先使用 `Invoke-RestMethod`；需要 curl 时把 JSON 放入文件再传入。
- 自动化测试：使用 `Invoke-RestMethod` 后，完整 HTTP 链路返回成功。

## 问题 8：完整 HTTP 联调脚本耗时偏长

- 现象：通过后台任务启动 FastAPI 和 Spring Boot，再执行完整链路请求，整体等待时间偏长。
- 触发场景：使用 PowerShell `Start-Job` 启动两个服务并等待健康检查。
- 根因：服务启动、依赖初始化、Maven 启停和后台任务输出收集都需要等待；脚本没有专门封装超时和日志裁剪。
- 解决方案：本次手动等待健康检查后完成验证，并在结束后停止服务。
- 后续避免：建议新增专门的本地 integration 脚本，封装启动、健康检查、测试请求、日志输出和清理逻辑。
- 自动化测试：目前完整链路已人工脚本验证通过，但还没有沉淀成稳定的自动化集成测试。

## 已补充的测试

- 新增 `ai-service/tests/test_basic_rag_pipeline.py`，覆盖内存模式下 Basic RAG query、retrieve、citation、trace 的主链路。
- Python 编译检查和单测已通过。
- Java 目前通过 `mvn test` 保证编译通过，但缺少针对 `AiServiceClient`、`RagService` 和 repository persistence 的精细单测。

## 后续改进建议

- 增加 Java `RagService` 单元测试，mock `AiServiceClient` 后验证 `rag_runs` 和 `rag_retrieval_results` 保存逻辑。
- 增加 Java AI client 契约测试，固定 FastAPI `/ai/rag/query` 请求和响应样例。
- 增加本地集成脚本，统一启动 FastAPI、Spring Boot、执行 ingest、query、校验 run 保存。
- 将当前 stub embedding、stub reranker、stub generator 标记在 README 和实验文档中，避免误以为语义效果已经真实可用。
