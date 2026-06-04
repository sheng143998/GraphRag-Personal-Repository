# 2026-05-29 文档列表状态接口

## 背景

上一轮已完成 `POST /api/documents/upload` 单篇 JSON 文档入库 Demo。入库后，用户需要通过文档列表看到文档状态、解析器和 chunk 数量，但当前 `GET /api/documents` 只返回基础文档字段，前端也仍使用旧的占位字段展示。

## 当前目标

本轮只完成一个接口：`GET /api/documents` 文档列表状态增强。

状态：已完成，等待用户 review。

## 接口边界

- Spring Boot 对外接口仍为 `GET /api/documents`。
- 支持现有可选参数 `knowledgeBaseId`。
- 返回每篇文档的基础字段、知识库名称、规范化前端展示状态、解析器信息和 chunk 数量。
- 前端文档页使用真实返回结构展示列表。

## 涉及模块

- Spring Boot 文档 Service / Repository / DTO
- 前端文档列表类型、状态展示与 API 对齐
- 项目过程文档

## 预计修改文件

- `backend-java/src/main/java/com/example/agentknowledge/repository/DocumentChunkRepository.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/document/DocumentResponse.java`
- `frontend/src/types/index.ts`
- `frontend/src/pages/documents/DocumentsPage.vue`
- `frontend/src/utils/mock-data.ts`
- `docs/reviews/2026-05-29-documents-list-status-review-prompt.md`
- `docs/testing/failures/2026-05-29-documents-list-status-notes.md`
- `docs/handoff/CURRENT_STATE.md`
- `PROJECT_CONTEXT.md`

## 非范围

- 不实现 `GET /api/documents/{id}` 详情增强。
- 不新增文档删除、重试、状态轮询或后台任务。
- 不做真实 HTTP smoke，除非本地数据库和服务已可用。

## 验证方式

- 运行 Java 后端构建，确认 repository 查询和 DTO 映射可编译。
- 运行前端构建，确认列表字段与类型定义一致。
- 运行 AI 服务语法验证，确认上一轮入库链路未被破坏。

## 实际验证结果

- Java 后端：`mvn.cmd test` 通过，结果为 `BUILD SUCCESS`。
- 前端：`npm.cmd run build` 通过，类型检查和生产构建成功。
- AI 服务：`python -m compileall app tests` 通过。
- HTTP smoke：本轮未启动 PostgreSQL、Spring Boot 和 FastAPI，未执行真实 HTTP smoke。

## 当前风险

- 列表 chunk 计数如果逐条查询，后续文档量变大时需要优化为聚合查询。
- 当前前端知识库名称依赖后端文档关联对象，后续若加入权限隔离需要避免泄漏不可见知识库信息。
