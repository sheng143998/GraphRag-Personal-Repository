# 2026-05-29 GET /api/knowledge-bases/{id} 知识库详情 review 提示

## 涉及文件
- `backend-java/src/main/java/com/example/agentknowledge/controller/KnowledgeBaseController.java` — 新增 `@GetMapping("/{id}")`
- `backend-java/src/main/java/com/example/agentknowledge/service/KnowledgeBaseService.java` — 新增 `getById(UUID id)`，注入 `KnowledgeDocumentRepository`、`DocumentChunkRepository`
- `backend-java/src/main/java/com/example/agentknowledge/dto/knowledge/KnowledgeBaseResponse.java` — 新增 `documentCount`、`chunkCount` 字段
- `backend-java/src/main/java/com/example/agentknowledge/repository/KnowledgeDocumentRepository.java` — 新增 `countByKnowledgeBase_Id`
- `backend-java/src/main/java/com/example/agentknowledge/repository/DocumentChunkRepository.java` — 新增 `countByKnowledgeBase_Id`
- `frontend/src/api/knowledgeBases.ts` — 新增 `fetchKnowledgeBaseById`

## 变更要点
1. `GET /api/knowledge-bases/{id}` 返回知识库详情，包含 `documentCount` 和 `chunkCount`
2. `GET /api/knowledge-bases` 列表也补充了统计字段
3. `POST /api/knowledge-bases` 创建时返回 `documentCount=0, chunkCount=0`
4. 404 时返回标准 `ResourceNotFoundException`

## 验证结果
- ✅ Java `mvn compile` 通过
- ✅ Java `mvn test` 通过
- ✅ 前端 `npm run build` 通过

## 重点 review
- `KnowledgeBaseService` 注入 `KnowledgeDocumentRepository` + `DocumentChunkRepository` 是否合理
- `toResponse` 签名变更是否影响已有的 `create`/`list` 调用
- Spring Data JPA `countByKnowledgeBase_Id` 命名是否正确
