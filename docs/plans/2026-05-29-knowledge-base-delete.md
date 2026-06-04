# 2026-05-29 DELETE /api/knowledge-bases/{id} 知识库删除

## 背景
知识库 CRUD 最后一项：删除。

## 实现方案
1. Controller 新增 `@DeleteMapping("/{id}")`，返回 `ApiResponse<Void>`
2. Service 新增 `@Transactional delete()`，先 `getReference` 验证存在再删除
3. 数据库已有 `ON DELETE CASCADE`：删除知识库 → 级联删除 documents → 级联删除 document_chunks → 级联删除 chunk_embeddings

## 涉及文件
- `backend-java/.../controller/KnowledgeBaseController.java` — `@DeleteMapping`
- `backend-java/.../service/KnowledgeBaseService.java` — `delete()`
- `frontend/src/api/knowledgeBases.ts` — `deleteKnowledgeBase`

## 验证
- ✅ `mvn compile` + `mvn test` 通过
- HTTP smoke: `curl -X DELETE http://127.0.0.1:8080/api/knowledge-bases/{id}` → 200
- HTTP smoke: 重复删除 → 404
