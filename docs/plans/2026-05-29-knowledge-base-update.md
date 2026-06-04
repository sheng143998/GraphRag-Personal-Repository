# 2026-05-29 PUT /api/knowledge-bases/{id} 知识库更新

## 背景
知识库当前只有创建、列表、详情，缺少更新接口。

## 实现方案
1. 新建 `UpdateKnowledgeBaseRequest` record，全部字段可选
2. Controller 新增 `@PutMapping("/{id}")`
3. Service 新增 `update(UUID id, UpdateKnowledgeBaseRequest)`，只更新非 null 字段
4. 404 时返回 `ResourceNotFoundException`

## 涉及文件
- `backend-java/src/main/java/com/example/agentknowledge/dto/knowledge/UpdateKnowledgeBaseRequest.java`（新增）
- `backend-java/src/main/java/com/example/agentknowledge/controller/KnowledgeBaseController.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/KnowledgeBaseService.java`

## 验证方式
- Java `mvn compile` + `mvn test`
