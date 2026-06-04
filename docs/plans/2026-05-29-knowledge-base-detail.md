# 2026-05-29 GET /api/knowledge-bases/{id} 知识库详情

## 背景
当前知识库只有 `POST /api/knowledge-bases`（创建）和 `GET /api/knowledge-bases`（列表），缺少详情接口。

## 实现方案
1. Controller 新增 `@GetMapping("/{id}")`
2. Service 新增 `getById(UUID id)` 方法，复用已有 `getReference`
3. Response 增强：新增 `documentCount`、`chunkCount` 统计

## 涉及文件
- `backend-java/src/main/java/com/example/agentknowledge/controller/KnowledgeBaseController.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/KnowledgeBaseService.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/knowledge/KnowledgeBaseResponse.java`

## 验证方式
- Java `mvn test`
- HTTP smoke：`curl http://127.0.0.1:8080/api/knowledge-bases/{id}`
