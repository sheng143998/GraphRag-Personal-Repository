# 2026-06-09 文档入库处理中卡住失败记录

## 现象

上传文档后，前端长期停留在“处理中”。FastAPI 日志显示 `POST /ai/ingest/document 200 OK`，但 Spring Boot 的文档状态未更新。

## 根因

Spring Boot 在保存文档前手动生成了一个 `documentId`，但 `KnowledgeDocument` 实体本身又带有 `@GeneratedValue` / `@UuidGenerator`。异步入库任务使用了保存前的 id，而数据库真实记录可能已经是另一个主键，导致异步处理器查不到对应文档，状态无法回写。

## 修复

- 使用 `documentRepository.save(document)` 返回的真实 `document.getId()` 传给异步入库任务
- 在 `DocumentIngestProcessor` 中补充中文日志
- 增加 `DocumentServiceTest`，校验异步任务使用的是持久化后的真实 id

## 验证

- `mvn.cmd -q "-Dtest=DocumentServiceTest,DocumentIngestProcessorTest" test`
