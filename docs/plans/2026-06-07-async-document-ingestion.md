# 文档解析异步任务模型计划

日期：2026-06-07

## 要解决的问题

当前文档上传流程完全同步：前端上传 → Spring Boot 阻塞等待 FastAPI 完成解析/切块/embedding → 返回。这导致：
- 大文件上传响应超时
- 用户体验差（上传后长时间无响应）
- PROCESSING/FAILED 状态在前端已定义但后端从未使用

## 当前背景

- `documents.status` 字段支持 `UPLOADED`（默认）、`INDEXED` 及前端预留的 `PROCESSING`、`FAILED`
- `DocumentService.create()` 同步调用 `aiServiceGateway.ingestDocument()`，完成后设置 `status=INDEXED`
- Spring Boot 项目未启用 `@EnableAsync`
- FastAPI `/ai/ingest/document` 是同步接口，无需修改
- 前端 `DocumentsPage.vue` 已定义 `PROCESSING` 状态样式但从未触发

## 实现策略

采用 **Spring Boot @Async 后台处理** 方案，改动最小：

1. **Spring Boot 启用异步**：`@EnableAsync` + 配置线程池
2. **DocumentService 改造**：
   - `create()` 方法：创建文档记录（status=PROCESSING）→ 立即返回
   - 新增 `@Async processDocumentAsync()`：后台调用 FastAPI ingest → 更新 status 为 INDEXED 或 FAILED
3. **前端改造**：上传后轮询 `GET /api/documents/{id}` 直到 status 变为 INDEXED 或 FAILED
4. **FastAPI**：无需修改（仍同步处理，只是调用方变为后台线程）

## 涉及模块

- `backend-java/`：DocumentService、异步配置、DocumentController（无需改）
- `frontend/`：UploadEntry.vue、DocumentsPage.vue、documents.ts API
- `ai-service/`：无需修改

## 重点 review 文件

1. `backend-java/src/main/java/.../service/DocumentService.java` — 核心逻辑
2. `backend-java/src/main/java/.../config/AsyncConfig.java` — 新增异步配置
3. `frontend/src/components/UploadEntry.vue` — 上传后轮询
4. `frontend/src/pages/documents/DocumentsPage.vue` — PROCESSING 状态 UI

## 测试计划

- Java 单元测试：DocumentService 异步方法
- HTTP smoke：上传文档 → 检查立即返回 PROCESSING → 等待后变为 INDEXED
- 前端验证：上传后显示"处理中"状态，完成后自动刷新

## 已知风险

- 后台任务失败后需正确设置 FAILED 状态和错误信息
- 轮询频率需控制避免对后端造成过大压力
- 需要配置线程池防止后台任务积压
