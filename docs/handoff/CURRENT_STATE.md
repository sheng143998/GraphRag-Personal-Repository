# 当前状态

更新时间：2026-06-17

## 已完成
- 文档上传入口支持单篇、多篇和文件夹上传。
- Spring Boot 新增 `POST /api/documents/upload/batch`，按文件创建多条 `PROCESSING` 文档记录，并保留文件夹相对路径到 `sourcePath`。
- 文档入库任务新增 `DocumentIngestDispatcher`，默认走 Spring `@Async` 本地线程池；配置 `DOCUMENT_INGEST_MODE=rabbitmq` 后可发布到 RabbitMQ 并由 listener 消费。
- RabbitMQ 模式新增交换机、队列、路由键配置和 JSON 消息转换；当前消费者仍在 Spring Boot 内调用 FastAPI `/ai/ingest/document`，保持 FastAPI 只处理单文档解析/切分/入库。
- 前端上传组件新增单篇、多篇、文件夹三种模式，文件夹上传会传 `webkitRelativePath`。
- 实验评估页开始向“工作流入口”升级，新增直接运行 RAG、导入评测集、保存样本、批量评估的入口设计。
- 后端新增评测集导入 DTO、API 与服务逻辑，支持按 `experimentId + caseId` 幂等导入。
- 前端新增导入评测集的类型与 API 封装，新增直接运行 RAG 的 API 封装。
- AI 服务默认 chunk 切分升级为 `recursive-overlap`，保留 `simple-window` 兼容路径；`parent-child` 改为章节感知 parent / child 切分，并补齐 chunk metadata。
- AI 服务入库新增 parent-child 自动降级：自动路由到 `parent-child` 的短文档，或最长章节仍低于 child 阈值的文档，会改走 `recursive-overlap`，避免一父一子内容完全相同；显式 `chunk_strategy=parent-child` 不受影响。
- AI 服务 parent-child chunker 层新增兜底：显式 parent-child 下，如果 parent 只能切出一个完全相同 child，会降级为单条 `recursive-overlap` child chunk，并记录 `parent_child_downgrade_reason=single-child-identical-parent`；同章节重复内容也会去重。
- AI 服务新增 `table-row-group` 表格切分策略，`csv` / `xls` / `xlsx` 自动路由到表头 + 行组 chunk；chunk metadata 保留 `sheet_name`、`row_range`、`column_names` 和 `block_type=table_rows`。
- AI 服务修复 XLSX context 乱码：`.xlsx` 不再按 UTF-8 文本读取二进制内容，而是直接解析 OpenXML workbook/sharedStrings/worksheet，生成结构化 sheet/table/row 数据后交给 `TableRowGroupChunker`；chunk context 输出 `Sheet / Columns / Row`，文档级 metadata 不保存完整大表结构。
- Spring Boot multipart 上传默认上限统一为 50MB，可通过 `DOCUMENT_UPLOAD_MAX_FILE_SIZE` / `DOCUMENT_UPLOAD_MAX_REQUEST_SIZE` 覆盖；`.env.example` 与后端 README 已同步。
- AI 服务完成 Markdown block-aware、DOCX 结构保留、MinerU PDF block metadata、Q&A chunker 与 code-aware chunker：Markdown 代码块不拆、图片引用单独标记；DOCX 标题与表格转为结构化 Markdown；MinerU 完成态记录 heading/image/table/code/formula/page 统计；面试经验默认 `qna-pair`；代码片段默认 `code-aware`。
- DOCX parser 现在会明确暴露 `python-docx` 缺失或 DOCX 内容损坏错误，不再静默返回空文本；本地项目 `.venv` 已验证可解析表格 DOCX，日志中的 `C:\Users\admin\PyCharmMiscProject\.venv` 缺少 `docx` 依赖。
- DOCX 表格输出新增 `Table N Rows` 结构化行坐标描述：单元格按 `R行C列=值` 展开，嵌套表格递归保留在所在单元格，横向合并单元格标记 `continues into C...`。
- MinerU PDF 轮询默认参数调整为 `MINERU_POLL_TIMEOUT_SECONDS=300`、`MINERU_POLL_INTERVAL_SECONDS=5`，并写入 `.env.example`；运行时仍可通过环境变量覆盖。
- MinerU 标准 batch 上传轮询端点已修复：`POST /api/v4/file-urls/batch` 得到 `batch_id` 后改查 `/api/v4/extract-results/batch/{batch_id}`，读取 `extract_result` 中的完成态和 `full_zip_url`；此前误查 `/api/v4/extract/task/{batch_id}` 会把错误响应吞掉并表现为超时。
- MinerU 完成态结果读取已补强：当 `full_zip_url` / `markdown_url` 出现在 batch 顶层或嵌套字段而非 `extract_result[0]` 时也能识别；zip 中没有 `.md` 时会解析 `content_list.json`；如果仍为空，入库错误会带上 parser `status` 和 `last_poll_error`。
- MinerU 结果下载已绕开系统代理：提交、上传、轮询仍使用默认环境代理；下载 `full_zip_url` / `markdown_url` 时单独使用 `trust_env=False` 客户端，修复本机代理导致 `cdn-mineru.openxlab.org.cn` `ConnectError` 的问题。
- `datasets/processed/rag-folder-evaluation-cases-20260616.json` 已完成 chunkId 二次审计，18 条样例的 `relevantChunkIds` / `expectedCitationChunkIds` 已收紧到直接证据 chunk，第一条已改用 `04-RAG与向量数据库.md` 的离线/在线流程 chunk。
- 实验页导入评测集时新增“导入目标实验”选择和“导入后自动运行一次 RAG 全链路”开关，导入成功后会调用 `/api/rag/evaluation-cases/run-batch` 按样例问题逐条生成 RAG run 并评估。
- 修复导入按钮不可点击问题：导入目标不再强依赖左侧“所属实验”筛选，未选择筛选时会回退到当前样例所属实验或第一个实验。
- 新增 `docs/experiments/2026-06-16-rag-evaluation-chunk-lookup.sql`，用于按 `relevant_chunk_ids` 和 `expected_citation_chunk_ids` 展开查询真实 chunk 内容。

## 已验证
- `mvn.cmd -f backend-java/pom.xml test`
- `npm.cmd --prefix frontend run typecheck`
- `mvn.cmd -f backend-java/pom.xml -q -DskipTests compile`
- `C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe -m pytest C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\tests\test_parent_child_chunker.py -q`
- `C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe -m pytest C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\tests\test_basic_rag_pipeline.py C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\tests\test_advanced_rag_strategy.py -q`
- `C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe -m pytest C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\tests\test_parent_child_chunker.py C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\tests\test_advanced_rag_strategy.py -q`
- `C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe -m pytest C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\tests\test_parent_child_chunker.py C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\tests\test_advanced_rag_strategy.py C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\tests\test_docx_parser.py C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\tests\test_mineru_pdf_parser.py -q`
- `C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe -m pytest -q`（52 passed，pytest cache 权限 warning 不影响结果）
- `C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe -m pytest -q`（54 passed，pytest cache 权限 warning 不影响结果）
- `C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe -m pytest tests\test_mineru_pdf_parser.py -q`（5 passed，pytest cache 权限 warning 不影响结果）
- `C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe -m pytest -q`（56 passed，pytest cache 权限 warning 不影响结果）
- `C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe -m pytest tests\test_mineru_pdf_parser.py -q`（6 passed，pytest cache 权限 warning 不影响结果）
- `C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe -m pytest -q`（57 passed，pytest cache 权限 warning 不影响结果）
- `ai-service/.venv/bin/python.exe -m pytest ai-service/tests/test_parent_child_chunker.py -k "xlsx or table_files or parent_child_ingest_query"`（3 passed，pytest cache 权限 warning 不影响结果）
- `.venv/bin/python.exe -m pytest -q`（ai-service 目录，58 passed，pytest cache 权限 warning 不影响结果）
- `npm.cmd --prefix frontend run typecheck`
- `mvn.cmd -f backend-java/pom.xml test`
- MinerU 真实连通性探针：`PyCharmMiscProject\.venv` 中 API 提交 `code=0`、上传 200、轮询 `done`，使用 `trust_env=False` 下载结果 zip 返回 HTTP 200 / `application/zip`。
- `datasets/processed/rag-folder-evaluation-cases-20260616.json` JSON 解析通过；96 个 chunk 引用均在 `document_chunks` 中存在，且均属于对应样例的 `relevantDocumentIds`；未发现 `GraphRAG关系`、图片说明或 prompt 示例类弱证据 chunk 残留。
- `npm.cmd --prefix frontend run build`
- `mvn.cmd -f backend-java\pom.xml test -Dtest=RagExperimentServiceTest`

## 重点文件
- `frontend/src/components/UploadEntry.vue`
- `frontend/src/api/documents.ts`
- `frontend/src/stores/workbench.ts`
- `frontend/src/types/index.ts`
- `backend-java/src/main/java/com/example/agentknowledge/controller/DocumentController.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentIngestDispatcher.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentIngestProcessor.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentIngestRabbitListener.java`
- `backend-java/src/main/java/com/example/agentknowledge/config/RabbitMqConfig.java`
- `docs/plans/2026-06-16-multi-document-folder-upload-async-queue.md`
- `frontend/src/pages/experiments/ExperimentsPage.vue`
- `frontend/src/api/experiments.ts`
- `frontend/src/api/rag.ts`
- `frontend/src/types/index.ts`
- `backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
- `ai-service/app/rag/chunkers/base.py`
- `ai-service/app/rag/parsers/base.py`
- `ai-service/app/services/ingest_service.py`
- `ai-service/tests/test_parent_child_chunker.py`
- `ai-service/tests/test_docx_parser.py`
- `ai-service/tests/test_mineru_pdf_parser.py`
- `datasets/processed/rag-folder-evaluation-cases-20260616.json`
- `frontend/src/pages/experiments/ExperimentsPage.vue`
- `frontend/src/styles.css`
- `docs/experiments/2026-06-16-rag-evaluation-chunk-lookup.sql`
- `docs/plans/2026-06-17-table-row-group-chunking.md`
- `docs/reviews/2026-06-17-table-row-group-chunking-review-prompt.md`
- `docs/plans/2026-06-17-block-aware-qa-code-chunking.md`
- `docs/reviews/2026-06-17-block-aware-qa-code-chunking-review-prompt.md`
- `docs/testing/failures/2026-06-17-mineru-standard-batch-polling-timeout-notes.md`
- `docs/reviews/2026-06-17-mineru-standard-batch-polling-timeout-review-prompt.md`

## 下一步
- 如需验证 RabbitMQ 模式，启动 RabbitMQ 后设置 `DOCUMENT_INGEST_MODE=rabbitmq`，再上传多文件观察消息发布与消费日志。
- 如果要进一步增强第三阶段，可新增数据库任务表或死信队列重试策略，避免消费失败只依赖 RabbitMQ 默认行为。
- 启动前端并验证实验页新入口的实际渲染与交互。
- 若需要，再把导入样本的 CSV/JSON 示例补到页面说明里。
- 如果继续优化 chunking，下一步可把 code-aware 从正则级升级到 AST/tree-sitter 级，并把 MinerU 原始 layout block 坐标透传到 chunk metadata。
