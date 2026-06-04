# 2026-05-29 DELETE /api/documents/{id} review 提示

## 涉及文件
- `DocumentController.java` — `@DeleteMapping("/{id}")` → `ApiResponse<Void>`
- `DocumentService.java` — `@Transactional delete()` + `fetchDocumentById` 前端 API

## 变更要点
1. 与 KB 删除模式一致：先查存在再删，404 → `ResourceNotFoundException`
2. DB 级联：document → chunks → embeddings
3. 前端新增 `deleteDocument(id)` + `fetchDocumentById(id)`

## 验证
- ✅ `mvn compile` + `mvn test`
- ✅ HTTP smoke：200/404 正确
