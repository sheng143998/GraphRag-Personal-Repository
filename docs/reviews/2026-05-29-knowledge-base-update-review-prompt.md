# 2026-05-29 PUT /api/knowledge-bases/{id} 知识库更新 review 提示

## 涉及文件
- `backend-java/.../dto/knowledge/UpdateKnowledgeBaseRequest.java`（新增）— 全部字段可选
- `backend-java/.../controller/KnowledgeBaseController.java` — 新增 `@PutMapping("/{id}")`
- `backend-java/.../service/KnowledgeBaseService.java` — 新增 `update()`，仅更新非 null 字段
- `frontend/src/api/knowledgeBases.ts` — 新增 `updateKnowledgeBase`

## 变更要点
1. 请求体所有字段可选，只更新传入的非 null 字段（部分更新语义）
2. 支持更新 `status` 字段（如 ACTIVE → ARCHIVED）
3. 404 返回 `ResourceNotFoundException`
4. 响应包含最新的 `documentCount` 和 `chunkCount`

## 验证结果
- ✅ `mvn compile` 通过
- ✅ `mvn test` 通过

## 重点 review
- UpdateKnowledgeBaseRequest 使用 `@Size` 而非 `@NotBlank`，是否正确表达"可选但有长度限制"
- `update()` 中 null 检查是否遗漏需要区分"不传"和"传空字符串"的场景
