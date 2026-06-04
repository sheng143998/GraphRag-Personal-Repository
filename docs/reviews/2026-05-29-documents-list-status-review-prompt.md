# 2026-05-29 文档列表状态接口 review 提示

## 本次 review 目标

请 review `GET /api/documents` 是否能展示文档入库后的关键状态，包括知识库名称、解析器、chunk 数量和前端可读状态。

## 本次接口范围

- `GET /api/documents`
  - 入口：`backend-java/src/main/java/com/example/agentknowledge/controller/DocumentController.java`
  - 作用：返回文档列表，可按 `knowledgeBaseId` 过滤。

## 重点 review 顺序

1. 后端 DTO
   - `backend-java/src/main/java/com/example/agentknowledge/dto/document/DocumentResponse.java`
   - 检查新增字段是否满足列表页展示，不影响上传接口复用。

2. 后端 Service 与 Repository
   - `backend-java/src/main/java/com/example/agentknowledge/service/DocumentService.java`
   - `backend-java/src/main/java/com/example/agentknowledge/repository/DocumentChunkRepository.java`
   - 检查 chunk 计数逻辑、状态映射和知识库过滤是否稳定。

3. 前端列表展示
   - `frontend/src/pages/documents/DocumentsPage.vue`
   - `frontend/src/types/index.ts`
   - 检查字段名称是否与后端一致，状态展示是否兼容 `INDEXED`、`UPLOADED`、`FAILED` 等后端状态。

## 当前占位实现

- chunk 数量通过 repository 逐文档统计，后续大数据量需要优化成聚合查询。
- 不展示解析失败原因。
- 不展示逐 chunk 详情。

## 已执行验证结果

- Java 构建：`mvn.cmd test` 通过，结果为 `BUILD SUCCESS`。编译结束阶段仍出现历史 Maven 本地 jar 访问拒绝日志，但未阻塞构建。
- 前端构建：`npm.cmd run build` 通过，类型检查和生产构建成功。
- AI 服务语法验证：`python -m compileall app tests` 通过。
- HTTP smoke：未执行，本轮没有启动 PostgreSQL、Spring Boot 和 FastAPI。

## Review 时特别注意

- 前端不应继续依赖旧的 `name` 和 `knowledgeBaseName` 占位字段。
- 后端返回的 `status` 应保持业务状态，同时由前端统一转成展示标签。
- 本轮不能顺手实现详情、删除或重试接口。
