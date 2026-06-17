# 2026-06-15 递归重叠与章节化 Parent-Child 切分 Review Prompt

请审查 `recursive-overlap-parent-child-chunking` 相关改动，重点确认实现是否符合项目架构边界、数据流和验证要求。

## 重点文件

- `ai-service/app/rag/chunkers/base.py`
- `ai-service/app/services/ingest_service.py`
- `ai-service/tests/test_parent_child_chunker.py`
- `ai-service/README.md`
- `PROJECT_CONTEXT.md`
- `docs/handoff/CURRENT_STATE.md`

## Review 关注点

- 默认未传 `chunk_strategy` 时是否走 `recursive-overlap`，且显式传 `simple-window` 时是否仍兼容旧路径。
- `recursive-overlap` 是否优先按标题、段落、行、句子、标点和字符窗口递归切分，并写入 `char_start`、`char_end`、`heading_path`、`section_title` 等 metadata。
- `parent-child` 是否优先使用 Markdown / MinerU Markdown 标题章节作为 parent，过长章节是否会继续递归拆分，child 是否带 overlap 并保留 parent metadata。
- parent chunk 是否仍不会参与 embedding，retrieval 是否继续只召回 child chunk。
- 新增 metadata 是否仅写入 `document_chunks.metadata` JSONB，不需要数据库迁移。
- 测试是否覆盖默认策略、兼容策略和章节化 parent-child 行为。

## 已验证

```powershell
C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe -m pytest C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\tests\test_parent_child_chunker.py -q
C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\.venv\bin\python.exe -m pytest C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\tests\test_basic_rag_pipeline.py C:\Users\admin\Desktop\agent-vue-java-springboot-fastapi-ai\ai-service\tests\test_advanced_rag_strategy.py -q
```

两组 pytest 均通过；当前本机 pytest cache 目录写入有权限 warning，不影响测试结果。
