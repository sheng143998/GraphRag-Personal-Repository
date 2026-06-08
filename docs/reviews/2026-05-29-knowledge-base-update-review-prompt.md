# 审查提示：知识 库 更新

请审查 `knowledge-base-update` 相关改动，重点确认实现是否符合项目架构边界、数据流和验证要求。

## 重点关注

- 前端不得直接调用 FastAPI，浏览器请求必须经过 Spring Boot `/api/*`。
- Spring Boot 只做桥接、业务持久化、DTO 映射和事务边界，不实现 RAG、GraphRAG 或 evaluator 评分逻辑。
- FastAPI 负责 RAG、Agent、GraphRAG、检索策略、生成和评估逻辑。
- 新增字段、trace payload、metadata 和 API 响应必须向后兼容。
- 测试应覆盖主要成功路径、回退路径和跨服务透传路径。

## 建议验证命令

- `git diff --check`

## 审查结论记录

- 若发现问题，应标注文件、行为风险和建议修复方式。
- 若无问题，应说明仍存在的测试缺口或后续观察点。
