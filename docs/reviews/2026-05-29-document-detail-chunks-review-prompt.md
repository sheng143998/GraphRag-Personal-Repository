# 2026-05-29 文档详情与 Chunk 摘要接口 review 提示

## 本次 review 目标

请 review `GET /api/documents/{id}` 是否能用于检查文档入库结果，尤其是 chunk 顺序、内容预览、解析 metadata 和文档基础状态是否清晰。

## 本次接口范围

- `GET /api/documents/{id}`
  - 入口：`backend-java/src/main/java/com/example/agentknowledge/controller/DocumentController.java`
  - 作用：返回单篇文档详情和 chunk 摘要列表。

## 重点 review 顺序

1. DTO 结构
   - `backend-java/src/main/java/com/example/agentknowledge/dto/document/DocumentResponse.java`
   - `backend-java/src/main/java/com/example/agentknowledge/dto/document/DocumentChunkResponse.java`
   - 检查列表接口和详情接口复用响应结构是否清楚，chunk 字段是否足够 review 入库结果。

2. Service 与 Repository
   - `backend-java/src/main/java/com/example/agentknowledge/service/DocumentService.java`
   - `backend-java/src/main/java/com/example/agentknowledge/repository/DocumentChunkRepository.java`
   - 检查详情接口是否按 `chunkIndex` 排序、404 行为是否保持不变、chunk 内容是否只返回预览。

3. 前端类型预留
   - `frontend/src/types/index.ts`
   - 检查类型定义是否能支撑后续文档详情页。

## 当前占位实现

- 暂不实现前端详情页。
- 暂不分页返回 chunk。
- 暂不返回 embedding 向量。

## 已执行验证结果

- Java 构建：`mvn.cmd test` 通过，结果为 `BUILD SUCCESS`。编译结束阶段仍出现历史 Maven 本地 jar 访问拒绝日志，但未阻塞构建。
- 前端构建：`npm.cmd run build` 通过，类型检查和生产构建成功。
- AI 服务语法验证：`python -m compileall app tests` 通过。
- HTTP smoke：未执行，本轮没有启动 PostgreSQL、Spring Boot 和 FastAPI。

## Review 时特别注意

- 列表接口不应返回完整 chunks，避免文档页变重。
- 详情接口不应泄漏 embedding 向量。
- chunk 顺序必须稳定，方便人工 review 切分结果。
