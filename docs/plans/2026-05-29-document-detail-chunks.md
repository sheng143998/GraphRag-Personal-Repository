# 2026-05-29 文档详情与 Chunk 摘要接口

## 背景

上一轮已增强 `GET /api/documents`，列表能看到文档状态、解析器和 chunk 数量。当前 `GET /api/documents/{id}` 仍只返回文档基础字段，无法查看入库后的 chunk 摘要，不利于 review 文档解析、切分和 embedding 入库结果。

## 当前目标

本轮只完成一个接口：`GET /api/documents/{id}` 文档详情增强。

状态：已完成，等待用户 review。

## 接口边界

- Spring Boot 对外接口仍为 `GET /api/documents/{id}`。
- 返回文档基础信息、知识库名称、chunk 数量和按 `chunkIndex` 排序的 chunk 摘要列表。
- chunk 摘要包含 chunk ID、标题、序号、内容预览、切分策略、页码、sheet 名称、行范围和 metadata。

## 涉及模块

- Spring Boot 文档 Service / Repository / DTO
- 前端类型定义，为后续详情页预留结构
- 项目过程文档

## 预计修改文件

- `backend-java/src/main/java/com/example/agentknowledge/repository/DocumentChunkRepository.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/DocumentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/document/DocumentResponse.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/document/DocumentChunkResponse.java`
- `frontend/src/types/index.ts`
- `backend-java/README.md`
- `docs/reviews/2026-05-29-document-detail-chunks-review-prompt.md`
- `docs/testing/failures/2026-05-29-document-detail-chunks-notes.md`
- `docs/handoff/CURRENT_STATE.md`
- `PROJECT_CONTEXT.md`

## 非范围

- 不实现前端详情页面。
- 不返回完整 embedding 向量。
- 不新增 chunk 删除、重切分、重试或编辑接口。
- 不改变数据库结构。

## 验证方式

- 运行 Java 后端构建，确认 DTO、Repository 和 Service 映射可编译。
- 运行前端构建，确认类型定义未破坏现有页面。
- 运行 AI 服务语法验证，确认 Python 侧未受影响。

## 实际验证结果

- Java 后端：`mvn.cmd test` 通过，结果为 `BUILD SUCCESS`。
- 前端：`npm.cmd run build` 通过，类型检查和生产构建成功。
- AI 服务：`python -m compileall app tests` 通过。
- HTTP smoke：本轮未启动 PostgreSQL、Spring Boot 和 FastAPI，未执行真实 HTTP smoke。

## 当前风险

- 当前详情接口直接返回 chunk 内容预览，后续如内容较长或数量较多，需要增加分页或限制。
- metadata 仍以 JSON 字符串形式透出，后续可再统一成结构化对象。
