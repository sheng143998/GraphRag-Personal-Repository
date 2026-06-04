# 2026-05-29 DELETE /api/knowledge-bases/{id} 知识库删除 review 提示

## 涉及文件
- `backend-java/.../controller/KnowledgeBaseController.java` — `@DeleteMapping("/{id}")`
- `backend-java/.../service/KnowledgeBaseService.java` — `@Transactional delete()`
- `frontend/src/api/knowledgeBases.ts` — `deleteKnowledgeBase`

## 变更要点
1. 删除前通过 `getReference` 验证存在，404 → `ResourceNotFoundException`
2. `@Transactional` 确保事务一致性
3. 数据库 `ON DELETE CASCADE`：KB → documents → chunks → embeddings 全链路级联
4. 关联表（rag_runs、chat_sessions、rag_feedback）使用 `ON DELETE SET NULL`

## 验证结果
- ✅ `mvn compile` + `mvn test`
- ✅ HTTP smoke：200 删除、404 重复删除

## 重点 review
- `@Transactional` 是否必要（数据库级联已处理）
- `delete()` 返回 void + Controller 返回 `ApiResponse<Void>` 是否一致
