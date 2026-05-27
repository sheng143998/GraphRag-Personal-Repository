# 第一版数据库设计文档 Review 提示

更新时间：2026-05-27

## 本轮目标

请 review `docs/architecture/database-design.md` 是否准确反映当前 PostgreSQL + pgvector schema，并能支撑后续 RAG、实验平台和文档入库开发。

## 重点 Review 顺序

1. 表结构分组
   - 知识库与文档表是否解释清楚。
   - chunk、embedding、RAG run、retrieval result、feedback、experiment 的职责是否明确。

2. 服务写入边界
   - Spring Boot 负责业务表、会话、反馈、实验配置是否合理。
   - FastAPI AI 服务负责 chunk、embedding、RAG 派生数据是否合理。
   - 是否避免多个服务随意改同一类业务状态。

3. 查询与索引
   - pgvector HNSW 索引、metadata GIN 索引和常用外键索引是否说明清楚。
   - RAG trace 和实验分析是否有足够字段支撑。

4. 当前限制
   - embedding 维度固定为 1536 是否已标注。
   - GraphRAG 表尚未创建是否已标注。
   - 多格式解析和真实文件上传仍是后续任务是否已标注。

5. 后续演进
   - 文档是否明确后续新增迁移只能追加，不改历史迁移。
   - 是否给出评估指标表、GraphRAG 表、权限审计等方向。

## 验证关注点

- 文档不应包含真实数据库密码、真实 `.env` 值或本地路径隐私。
- 文档中的表名、字段名和索引名应尽量与 Flyway 迁移一致。
- 本轮不是接口开发，不触发接口级暂停规则。
