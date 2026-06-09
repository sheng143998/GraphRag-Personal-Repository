# 2026-06-09 文档入库处理中卡住修复计划

## 背景

上传文档后，前端一直显示“处理中”。FastAPI 日志显示 `POST /ai/ingest/document 200 OK`，但 Spring Boot 的文档状态没有及时从 `PROCESSING` 变成 `INDEXED` 或 `FAILED`。

## 目标

- 找出文档入库状态迟迟不更新的根因
- 补充后端可观测日志
- 保证文档上传后能正确更新状态并结束前端轮询

## 处理思路

1. 检查 Spring Boot 保存文档后传给异步任务的 `documentId` 是否与数据库真实主键一致
2. 在异步处理器中补充调用前、调用后、成功、失败日志
3. 增加单元测试，防止后续再次把保存前 id 传入 AI 入库流程

## 验证

- `mvn.cmd -q "-Dtest=DocumentServiceTest,DocumentIngestProcessorTest" test`
