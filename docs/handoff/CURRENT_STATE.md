# 当前状态

更新时间：2026-06-16

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
- `ai-service/app/services/ingest_service.py`
- `ai-service/tests/test_parent_child_chunker.py`
- `datasets/processed/rag-folder-evaluation-cases-20260616.json`
- `frontend/src/pages/experiments/ExperimentsPage.vue`
- `frontend/src/styles.css`
- `docs/experiments/2026-06-16-rag-evaluation-chunk-lookup.sql`

## 下一步
- 如需验证 RabbitMQ 模式，启动 RabbitMQ 后设置 `DOCUMENT_INGEST_MODE=rabbitmq`，再上传多文件观察消息发布与消费日志。
- 如果要进一步增强第三阶段，可新增数据库任务表或死信队列重试策略，避免消费失败只依赖 RabbitMQ 默认行为。
- 启动前端并验证实验页新入口的实际渲染与交互。
- 若需要，再把导入样本的 CSV/JSON 示例补到页面说明里。
- 如果继续优化 chunking，可优先补文档类型路由策略，例如面试 Q/A、代码块、招聘 JD 和表格行组切分。
