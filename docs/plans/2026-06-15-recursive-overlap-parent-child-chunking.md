# 2026-06-15 递归重叠与章节化 Parent-Child 切分

## 目标

在现有 AI 服务文档入库链路中落地两项 chunk 切分增强：

- 将默认 flat chunker 从固定字符窗口升级为 `recursive-overlap`，优先按标题、段落、行、句子和兜底字符窗口切分，并支持 overlap。
- 将 `parent-child` 从固定 parent / child 字符窗口升级为章节感知切分：parent 优先对应标题章节，过长章节再递归切分；child 在 parent 内部做带 overlap 的递归切分。

## 边界

- 只修改 FastAPI AI 服务的文档切分逻辑和测试。
- Spring Boot 仍只负责业务编排、桥接和持久化，不实现 RAG / chunking 算法。
- 前端浏览器请求仍只进入 Spring Boot `/api/*`，不直接访问 AI 服务。
- 不调整数据库 schema；新增字段全部进入现有 `document_chunks.metadata` JSONB。

## 预计修改

- `ai-service/app/rag/chunkers/base.py`
- `ai-service/app/services/ingest_service.py`
- `ai-service/tests/test_parent_child_chunker.py`
- `ai-service/README.md`
- `PROJECT_CONTEXT.md`
- `docs/handoff/CURRENT_STATE.md`

## 新增 metadata

- `chunk_algorithm`
- `chunk_size`
- `chunk_overlap`
- `char_start`
- `char_end`
- `split_level`
- `heading_path`
- `section_index`
- `section_title`
- `parent_heading`
- `parent_char_start`
- `parent_char_end`
- `child_index_in_parent`

## 验证方式

```powershell
cd ai-service
python -m pytest tests/test_parent_child_chunker.py -q
python -m pytest tests/test_parent_child_chunker.py tests/test_advanced_rag_strategy.py -q
```

## 风险

- overlap 会增加 chunk 数量和 embedding 成本，需要通过现有 RAG 评测指标观察 recall / citation_hit 是否抵消成本增长。
- 章节标题识别主要面向 Markdown / MinerU Markdown 输出；纯 TXT、DOCX 仍会退化为段落 / 句子切分。
