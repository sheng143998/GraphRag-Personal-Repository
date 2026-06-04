# 2026-05-29 DELETE /api/documents/{id} 文档删除

## 背景
文档 CRUD 缺少删除接口。

## 实现方案
1. Controller 新增 `@DeleteMapping("/{id}")`，返回 `ApiResponse<Void>`
2. Service 新增 `@Transactional delete()` — 验证存在 + 删除
3. DB `ON DELETE CASCADE`：document → chunks → embeddings

## 涉及文件
- `DocumentController.java` — `@DeleteMapping`
- `DocumentService.java` — `delete()`
- `frontend/src/api/documents.ts` — `deleteDocument` + `fetchDocumentById`

## 验证
- ✅ `mvn compile` + `mvn test`
- ✅ HTTP smoke：200 删除、404 重复删除
