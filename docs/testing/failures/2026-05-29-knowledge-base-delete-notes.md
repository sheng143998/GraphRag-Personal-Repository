# 2026-05-29 DELETE /api/knowledge-bases/{id} 失败复盘 / 观察记录

## 无新增问题
- 编译和测试均一次通过
- 数据库已有 `ON DELETE CASCADE`，无需额外处理
- `@Transactional` 注解使用 `jakarta.transaction.Transactional`（非 Spring 的），已验证兼容

## 注意事项
- 删除 KB 会级联删除所有 documents、chunks、embeddings，不可逆
- 关联的 rag_runs、chat_sessions 等表的 `knowledge_base_id` 会被 SET NULL
