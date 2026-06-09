# Spring Boot 接口调用日志计划

## 目标

为 Spring Boot `/api/*` 调用补齐统一日志，使前端请求是否进入后端、接口返回状态和耗时能够在 Java 控制台直接观察。

## 实施范围

- 在 `TraceIdFilter` 中记录接口调用完成日志。
- 日志字段包含 method、path、status、durationMs 与 traceId。
- 在 `KnowledgeBaseService` 中补充知识库创建、更新、删除成功日志。
- 不记录请求体，避免上传内容、用户答案或敏感字段进入日志。

## 验证

- `mvn.cmd -q -DskipTests compile`
