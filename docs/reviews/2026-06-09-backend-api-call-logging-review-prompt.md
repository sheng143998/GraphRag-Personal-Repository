# Spring Boot 接口调用日志 Review 提示

请重点审查本次 Spring Boot 日志改动：

- `TraceIdFilter` 是否能覆盖所有正常和异常请求，并在 `TraceContext.clear()` 前记录 traceId。
- 统一接口日志是否只记录 method、path、status、durationMs、traceId，避免泄露请求体或敏感字段。
- `KnowledgeBaseService` 的创建 / 更新 / 删除日志是否位于业务操作成功之后，字段是否足够排查前端调用链路。
- 日志是否会产生过量噪声，后续是否需要按环境配置日志级别。
- 编译验证：`mvn.cmd -q -DskipTests compile`。
