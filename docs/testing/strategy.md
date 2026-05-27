# Testing Strategy

测试分为四类：

- 单元测试：隔离模块，不依赖外部服务。
- 外部依赖单元测试：依赖 PostgreSQL、Redis、模型服务等，但不跑完整应用。
- 集成测试：运行在真实部署环境上，不做 mock。
- Playwright E2E 测试：覆盖前后端完整交互。

## 第一阶段测试重点

- Python：chunker、parser、prompt builder、retriever adapter、trace schema。
- Java：service 规则、controller contract、AI client 错误处理、Flyway migration。
- 前端：API client、上传表单、聊天页面、引用来源展示。
- 数据库：pgvector extension、向量索引、metadata filter。

## 测试失败复盘

非显而易见或跨模块问题需要在 `docs/testing/failures/` 下记录：

- 问题现象
- 复现步骤
- 根因
- 修复方案
- 补充的回归测试
- 下次排查建议
