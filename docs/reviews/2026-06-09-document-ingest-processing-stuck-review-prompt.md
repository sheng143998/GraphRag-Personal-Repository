# 2026-06-09 文档入库处理中卡住 Review 提示

请重点检查以下文件：

- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentIngestProcessor.java`
- `backend-java/src/test/java/com/example/agentknowledge/service/DocumentServiceTest.java`

重点关注：

1. 异步处理是否使用了保存后的真实文档 id
2. 成功 / 失败时是否都会回写文档状态
3. 新增日志是否能明确定位卡在“提交任务 / 调 AI / 回写状态”哪一步
4. 新增测试是否覆盖了 id 传递错误这一回归风险
