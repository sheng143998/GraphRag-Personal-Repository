# 2026-06-27 Agent 记忆模块三层架构重构

## 目标

将当前分散的 Agent 记忆模块重构为**三层分层记忆架构**（短期 / 中期 / 长期），使 Agent 在多轮对话、长会话、跨会话场景下具备一致且可扩展的记忆能力。

## 背景与现状问题

当前记忆模块的不足：

1. **Python 侧（运行时）**：`ai-service/app/agents/memory/` 仅为进程内硬编码种子数据 + 规则打分检索器，`MemoryWriter` 产生 `not_persisted=True` 候选但不入库，与 Java 持久层未打通。
2. **Java 侧（持久化）**：`agent_memories` / `agent_memory_events` 表已建并有 REST CRUD API，但 Python 运行时不感知，全靠前端管理面板手动维护。
3. **无层级概念**：上下文窗口满了就截断、没有中期缓存层、没有长期语义检索。
4. **缺少结构化任务追踪**：多步推理时 Agent 不知道当前执行到哪一步、"全局目标是什么"。

## 新架构总览：三层记忆模型

```
┌──────────────────────────────────────────────────────────────┐
│                      Agent 运行时                             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 1: 短期记忆（LLM 上下文窗口）                    │   │
│  │  · 摘要压缩 + Token Buffer 动态管理                    │   │
│  │  · 结构化 current_task 字段追踪多步推理进度            │   │
│  │  · 容量：~8K-128K tokens（取决于模型）                 │   │
│  └──────────────────────┬───────────────────────────────┘   │
│        上下文窗口溢出时 ↓ 回填 / 补充                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 2: 中期记忆（Redis）                            │   │
│  │  · 完整会话历史（当前会话）                             │   │
│  │  · 过去 3 天高频记忆（跨会话）                         │   │
│  │  · 时间倒序排序                                       │   │
│  │  · 容量：可配（默认每会话保留最近 N 轮）               │   │
│  └──────────────────────┬───────────────────────────────┘   │
│        周期归并 / 降冷 ↓                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 3: 长期记忆（PostgreSQL + pgvector）            │   │
│  │  · 用户画像（support_customers + user_profiles）       │   │
│  │  · 向量语义检索（pgvector embedding + RAG）            │   │
│  │  · 结构化经验库（agent_memories 表复用升级）           │   │
│  │  · 容量：持久化，无上限                                │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## 架构决策

1. **三层之间是"溢写 + 回填"关系而非替代关系**：
   - L1 优先承载对话上下文，满时向 L2 溢写并压缩。
   - L2 承载完整会话 + 近期高频记忆，Agent 发起检索时 L1 不足则从 L2 补充。
   - L3 承载持久化长期记忆，L2 中超过 3 天或经过归并的记忆下沉到 L3。
2. **复用现有基础设施**：
   - `docker-compose.yml` 已有 `redis:7-alpine`，L2 基础设施现成。
   - `pgvector/pgvector:pg16` 已在运行，L3 向量检索基础设施现成。
   - `agent_memories` / `agent_memory_events` / `support_customers` 表已建，L3 结构化部分已有基础。
3. **不改 Java ↔ Python 职责边界**：
   - Python 负责记忆的读写逻辑、压缩、检索和归并策略。
   - Java 负责 L3 的 REST 管理 API、用户画像 CURD、前端视图。
   - Redis（L2）同时被 Python 和 Java 访问：Python 运行时读写，Java 提供管理/调试接口。
4. **替换而非增量改造旧模块**：
   - 旧 `ai-service/app/agents/memory/` 中的 `MemoryRetriever` / `MemoryWriter` / `MemoryPolicy` / `MemoryEvaluator` 将被替换为新的三层 MemoryManager。
   - 旧 `MemoryRetrievalEvent` / `MemoryWriteCandidate` 等数据结构升级为支持三层来源追踪的新模型。

## 各层详细设计

### Layer 1：短期记忆（LLM 上下文窗口管理）

**目标**：在有限的 token 预算内，让 LLM 拿到最相关的对话信息 + 当前任务状态。

**核心组件**：

#### 1.1 ContextWindowManager

```text
ai-service/app/agents/memory/context_window.py（新建）
```

职责：
- 维护一个 token 预算（可配，默认 8192）
- 接收每轮对话的 `user_message`、`assistant_message`、`system_prompt`
- 当总 token 数接近预算时，自动触发**摘要压缩**

#### 1.2 摘要压缩策略

采用二级压缩：

- **轻量压缩**（token 使用量 < 80% 预算时）：保留最近 N 轮原文，早期轮次替换为一句摘要。摘要调用 LLM（小 prompt、低温度）生成，格式为固定模板：`[前文摘要] 用户问了关于 X 的问题，助手回答涉及 Y 和 Z。`
- **激进压缩**（token 使用量 >= 80% 预算时）：只保留当前任务的 `current_task` 结构 + 最近 3 轮原文 + 早期全局摘要（一句话）。

#### 1.3 Token Buffer 策略

不等到预算耗尽再压缩，而是设置两级水位：

```
token 使用率 < 60% → 正常追加，不压缩
token 使用率 60%-80% → 轻量压缩旧轮次
token 使用率 > 80% → 激进压缩，触发 L2 补充
```

#### 1.4 结构化 current_task 字段

在发送给 LLM 的消息列表中，始终在最前面维护一个结构化字段：

```json
{
  "current_task": {
    "task_id": "support-session-abc123",
    "phase": "diagnosis",
    "phase_step": "check_gateway_logs",
    "total_steps": 7,
    "completed_steps": ["clarify_symptom", "check_error_codes"],
    "next_step": "analyze_log_patterns",
    "goal": "排查 ERR_E1024 登录故障",
    "constraints": ["不能重启生产环境", "需保留审计日志"]
  }
}
```

- 每次工作流进入新 phase / step 时更新此字段。
- LLM 看到的上下文中最前面就是这个结构，解决"模型忘记自己做到哪了"的问题。
- 从 `SupportAgentState` 中的 `IncidentContext` + workflow gate status 自动派生。

### Layer 2：中期记忆（Redis）

**目标**：当 L1 不够用时提供快速补充，同时承担跨会话短期记忆共享。

**基础设施**：已有 `redis:7-alpine` 在 docker-compose.yml。

**核心组件**：

#### 2.1 RedisSessionMemory

```text
ai-service/app/agents/memory/redis_memory.py（新建）
```

数据结构设计（Redis key 规范）：

| Key Pattern | 类型 | TTL | 内容 |
|-------------|------|-----|------|
| `session:{session_id}:messages` | LIST | 3 天 | 完整对话历史，每条为 JSON：`{role, content, timestamp, token_count}` |
| `session:{session_id}:current_task` | STRING | 会话期间 | `current_task` JSON，L1 每次更新同步写一份到 Redis |
| `session:{session_id}:summary` | STRING | 3 天 | 会话级摘要（每 5 轮由 LLM 生成一次） |
| `user:{user_id}:recent_memories` | ZSET | 3 天 | 高频使用记忆，score=使用次数或最后使用时间戳，member=记忆 JSON |
| `memory:index:{memory_id}` | STRING | 3 天 | 单条记忆详情 |

**L2 → L1 补充逻辑**：

当 L1 触发激进压缩（token > 80%）时，从 Redis 拉取：
1. `session:{session_id}:summary` — 会话摘要
2. `session:{session_id}:messages` 最后 N 条 — 最近对话原文
3. `user:{user_id}:recent_memories` Top 5 — 近期高频记忆

补充进 L1 的 system prompt 区域。

**时间排序**：ZSET 的 score 使用 Unix 时间戳，天然支持时间倒序。

#### 2.2 记忆访问频率追踪

每次 L2 中的记忆被 L1 引用时，对应 ZSET 的 score 递增（或更新为当前时间戳）。过去 3 天被频繁引用的记忆自然保持在 ZSET 前列。

#### 2.3 L2 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `REDIS_MEMORY_TTL_SECONDS` | 259200（3天） | Redis key 过期时间 |
| `REDIS_SESSION_MAX_MESSAGES` | 100 | 每会话保留最大消息数 |
| `REDIS_USER_RECENT_MEMORY_COUNT` | 20 | 用户近期记忆保留条数 |
| `REDIS_CONTEXT_FALLBACK_TOP_K` | 5 | L1 不足时从 L2 补充几条 |

### Layer 3：长期记忆（PostgreSQL + pgvector）

**目标**：持久化用户画像 + 语义检索经验库 + 关系型记忆管理。

**基础设施**：已有 `pgvector/pgvector:pg16` + 已有 `agent_memories` / `support_customers` 等表。

**核心组件**：

#### 3.1 记忆语义向量化与 RAG 检索

```text
ai-service/app/agents/memory/long_term.py（新建）
ai-service/app/db/memory_repository.py（新建或扩展 repositories.py）
```

**写入路径**：
1. L2 中超过 3 天的记忆 → 触发下沉到 L3
2. 对记忆文本调用 embedding adapter 生成 1536 维向量
3. 写入 `agent_memories` 表（复用现有表，新增 `embedding vector(1536)` 列）
4. 建立 pgvector IVFFlat 索引

**检索路径**：
1. Agent 发起长期记忆查询
2. 查询向量化 → pgvector 余弦相似度 Top-K
3. 结合结构化过滤（customer_id、product、version、error_code）缩小范围
4. 返回最相关记忆作为 L1 上下文补充

**数据库迁移**：

```sql
-- 在 agent_memories 表新增向量列和索引
ALTER TABLE agent_memories ADD COLUMN embedding vector(1536);
CREATE INDEX idx_agent_memories_embedding ON agent_memories 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

#### 3.2 客户运维画像（Customer Ops Profile）

```text
ai-service/app/agents/memory/customer_profile.py（新建）
后端 Java 侧：扩展 SupportCustomerService + 新建 SupportCustomerOpsProfileResponse
```

**定位**：本项目是**企业技术售后 Ops 平台**，用户画像不是面向个人消费者，而是面向**企业客户**。客户运维画像复用和扩展已有的 `support_customers` / `agent_memories` / `agent_runs` 表，不新建 `user_profiles` 表。

**数据来源**（全部基于现有表扩展）：

| 现有表 | 扩展方式 | 说明 |
|--------|----------|------|
| `support_customers` | `metadata` JSONB 中新增 `ops_profile` 子对象 | 客户运维画像聚合数据 |
| `support_environments` | 无需扩展（已完整） | 部署资产清单 |
| `agent_memories` | 新增 `embedding` 列（向量语义检索） | 历史案例语义检索 |
| `agent_runs` | 无需扩展（已有 trace） | 工单执行历史 |

**ops_profile JSONB 内容设计**（存在 `support_customers.metadata` 中）：

```json
{
  "ops_profile": {
    "product_matrix": [
      {"product": "Support Console", "version": "2.3.1", "env_count": 3}
    ],
    "incident_summary": {
      "total_incidents": 47,
      "resolved_24h": 38,
      "avg_resolution_hours": 6.2,
      "top_error_codes": [
        {"code": "ERR_E1024", "count": 12, "last_at": "2026-06-25"}
      ],
      "severity_distribution": {"critical": 3, "high": 15, "medium": 22, "low": 7}
    },
    "environment_health": {
      "production_env_count": 2,
      "staging_env_count": 1,
      "last_deployment": "2026-06-20",
      "known_constraints": ["禁止重启生产环境", "需走变更审批流程"]
    },
    "support_tier": "premium",
    "sla_policy": "4小时响应，24小时解决",
    "preferred_contact": {"name": "张三", "role": "运维经理", "channel": "email"}
  }
}
```

**聚合更新策略**：

- 每次 Agent 诊断完成后**异步更新统计**（不阻塞主链路）：
  1. 增量更新 `incident_summary` 的计数和 `top_error_codes`
  2. 如果发现新的错误码模式，追加到 `top_error_codes` 并按频次排序
  3. 更新 `avg_resolution_hours`（指数移动平均）
- 当客户新增/变更部署环境时，更新 `product_matrix` 和 `environment_health`
- 每 24 小时做一次全量兜底重算

**Python 侧接口**：

```python
class CustomerOpsProfile:
    async def get_profile(self, customer_id: str) -> dict:
        """获取客户运维画像，供 Agent 诊断前加载"""
    
    async def update_stats(self, customer_id: str, run_result: dict) -> None:
        """工单结束后异步更新统计"""
    
    async def find_similar_customers(self, error_codes: list[str], product: str) -> list:
        """找到有相似问题的其他客户，用于跨客户经验迁移"""
```

**Java 侧对应接口**：

- 复用现有 `SupportCustomerService.getCustomer(id)`，返回的 `metadata` JSONB 中包含 `ops_profile`
- 新增 `GET /api/support-customers/{id}/ops-profile` 单独返回运维画像
- 新增 `POST /api/support-customers/{id}/ops-profile/refresh` 手动触发重算

#### 3.3 L3 写入流水线：感知-判断-提炼-存储

L3 的写入不是简单的“存数据库”，而是一条**四级流水线**，确保只有高质量、无冲突的记忆进入长期存储。

```text
  L1/L2 sessions
       |
       v
  [Perceive] Filter noise
    - Short replies (length < 10 chars)
    - Greetings only (LLM zero-shot classify)
    - Duplicates (embedding cosine > 0.92 vs existing)
       |
       v
  [Judge] Evaluate value (LLM scores 0-10)
    - Contains diagnosis? (0-3 pts)
    - Contains new info? (0-3 pts)
    - Has clear outcome? (0-2 pts)
    - Is reusable? (0-2 pts)
       |
       v
  [Extract] LLM structured extraction
    - Content summary (<=300 chars)
    - Key entities (customer, product, version, error_codes)
    - Root cause category (code_defect/config_error/resource/external/unknown)
       |
       v
  [Store] Conflict detection + write
    - Same customer + product + error_code? -> Merge/update
    - Semantic similarity > 0.95? -> Update instead of insert
    - Write agent_memories + embedding
```

**阶段一：感知（Perceive）— 过滤无用信息**

从 L1 上下文窗口和 L2 Redis 会话历史中，先过滤掉三类低价值内容：

| 过滤规则 | 判断方式 | 示例 |
|----------|----------|------|
| 短回复 | 文本长度 < 10 字符 | "嗯"、"好的"、"收到" |
| 纯寒暄 | LLM 零样本分类 prompt | "你好"、"谢谢"、"再见" |
| 重复内容 | 与 L3 已有记忆的 embedding 余弦相似度 > 0.92 | 同一问题的第二次提问 |

```python
class PerceptionFilter:
    async def filter(self, messages: list[dict], existing_embeddings: list) -> list[dict]:
        # 1. Remove short replies (< 10 chars)
        # 2. LLM zero-shot classify to remove greetings
        # 3. Embedding similarity dedup (> 0.92 threshold)
        return filtered
```

**阶段二：判断（Judge）— 评估记忆价值**

对过滤后的内容，由 LLM 进行价值判断并打分。评估维度：

| 评估维度 | 判断 Prompt 要点 | 分值 |
|----------|------------------|------|
| 是否包含诊断结论 | "Does this conversation contain a definitive diagnosis or solution?" | 0-3 |
| 是否包含新信息 | "Does it contain new error codes, env info, or unseen symptoms?" | 0-3 |
| 是否有明确结果 | "Is there a clear outcome (resolved/escalated/workaround)?" | 0-2 |
| 是否可复用 | "Can this experience be reused by other customers or similar issues?" | 0-2 |

**重要度总分 = 诊断结论(0-3) + 新信息(0-3) + 明确结果(0-2) + 可复用性(0-2)**，范围 0-10。总分 >= 5 的进入下一阶段。

```python
class ImportanceJudge:
    async def evaluate(self, message: str, context: dict) -> tuple[bool, int]:
        prompt = _build_judge_prompt(message, context)
        score = await llm.score(prompt)  # LLM returns 0-10
        return score >= 5, score
```

**阶段三：提炼（Extract）— LLM 结构化提取**

通过 LLM 将原始对话提炼为结构化记忆卡片，**必须包含以下 4 个字段**：

| 字段 | 说明 | 约束 |
|------|------|------|
| `content_summary` | 内容摘要 | ≤300字，包含：症状 → 诊断过程 → 根因 → 解决方案 |
| `timestamp` | 时间戳 | ISO 8601 格式，记录问题发生时间和解决时间 |
| `importance_score` | 重要度评分 | 0-10，直接复用判断阶段的分数 |
| `structured_entities` | 结构化实体 | JSON：customer_id, product, version, error_codes, root_cause_category, severity |

```python
class MemoryExtractor:
    async def extract(self, message: str, importance: int, context: dict) -> dict:
        prompt = f'''Extract structured memory from this support conversation:
Conversation: {message}
Customer: {context.get("customer")}
Product: {context.get("product")}

Output JSON only (no extra text):
{{
    "content_summary": "...",
    "root_cause_category": "code_defect|config_error|resource_shortage|external_dependency|unknown",
    "error_codes": ["ERR_..."],
    "severity": "critical|high|medium|low",
    "resolution": "...",
    "tags": ["..."]
}}'''
        return json.loads(await llm.generate(prompt))
```

**阶段四：存储（Store）— 版本化 + 语义冲突检测 + 定期整合**

存储阶段是整个流水线的最后一关，也是设计最复杂的一关。核心目标：**不产生冗余、不丢失历史、不被矛盾信息污染**。采用三套互补机制：

##### 3.3.1 记忆版本化（Memory Versioning）

每条记忆不是孤立的静态记录，而是带有丰富元数据和版本链的动态实体。

**记忆元数据字段**（在 agent_memories 表中扩展）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | INT | 版本号，从 1 开始递增，每次更新 +1 |
| `parent_memory_id` | UUID | 指向上一个版本，形成版本链 |
| `topic_group_id` | UUID | 同一主题下所有版本共享同一个 group_id |
| `status` | VARCHAR(20) | active / archived / superseded / merged |
| `created_at` | TIMESTAMPTZ | 创建时间 |
| `last_accessed_at` | TIMESTAMPTZ | 最近一次被检索命中的时间 |
| `source_dialog_id` | VARCHAR(160) | 来源会话/工单 ID，便于追溯 |
| `confidence_score` | NUMERIC(5,4) | 写入时的置信度，随版本迭代可能变化 |
| `scope_tags` | JSONB | 适用范围标签：customer_specific / cross_customer / version_specific / deprecated |

**版本链示例**：

```text
topic_group_id: tg-ERR_E1024-acme

v1 (status=superseded)              v2 (status=superseded)           v3 (status=active)
  2026-06-01                           2026-06-15                       2026-06-25
  诊断: 连接池耗尽           诊断: 网关超时导致连接池耗尽  诊断: 网关超时 + 连接池上限过低
  方案: 扩容连接池          方案: 增加网关重试         方案: 扩容连接池到 200 + 网关超时 5s
  confidence: 0.75                     confidence: 0.82                  confidence: 0.91
  source: dialog-001                   source: dialog-045                source: dialog-045 + dialog-067
                                      parent: v1                        parent: v2
```

**版本化检索逻辑**：

当 Agent 需要使用记忆时，**不是简单取 status=active 的最新一条**，而是：

```text
  1. 通过 topic_group_id 找到同主题下所有版本
  2. 按 version DESC 排序，返回完整版本链
  3. 将版本链注入 L1 上下文，让 LLM 综合判断：
     - 最新版本是否已足够完整？
     - 旧版本是否包含被新版本遗漏的细节？
     - 时间上最新的版本是否一定最可信？（可能是错误的快速修复）
```

**对应的 Prompt 设计**：

```python
VERSION_AWARE_RETRIEVAL_PROMPT = """
You are a support memory analyst. Below are multiple versions of the same topic memory.

Version history:
{version_chain}

Current context:
- Customer: {customer_id}
- Product: {product} v{version}
- Current error: {error_codes}
- Query: {query}

Select the most appropriate version(s) for the current context. Consider:
1. Is the latest version complete enough, or does it miss details from older versions?
2. Could the latest version be a rushed hotfix that oversimplifies the root cause?
3. Is there complementary information across versions that should be merged?

Return JSON: {"selected_versions": ["v3","v1"], "reason": "..."}
"""
```

##### 3.3.2 语义冲突检测（Semantic Conflict Detection）

当一条新记忆准备写入时，不仅检查精确匹配（同 customer+product+version+error_code），还要做**语义级冲突检测**。

**全流程**：

```text
  New memory ready to write
       |
       v
  Step 1: Vector recall
    pgvector cosine_similarity -> Top-K semantically similar old memories (K=10)
       |
       v
  Step 2: LLM conflict analysis
    Input: new_memory + old_memories[0..K] (with full metadata)
    LLM judges three things:
      (a) Relationship: contradict / supplement / duplicate / unrelated
      (b) If contradict: which to trust? (time-first? keep both?)
      (c) Recommended action: update_old / insert_new / merge_both / ignore_new
       |
       v
  Step 3: Execute action
    update_old  -> bump version, set parent_memory_id
    insert_new  -> new topic_group_id, version=1
    merge_both  -> LLM merge + insert as new version, archive old versions
    ignore_new  -> log event, discard
```

**冲突判断 Prompt 设计**（核心）：

```python
CONFLICT_DETECTION_PROMPT = """
You are a memory conflict detector for an enterprise support knowledge base.
Analyze the relationship between a NEW memory and EXISTING memories.

## NEW MEMORY
Content: {new_content}
Source: {new_source_dialog_id}
Timestamp: {new_created_at}
Customer: {new_customer_id}
Product: {new_product} v{new_version}
Error codes: {new_error_codes}
Severity: {new_severity}
Importance: {new_importance}/10

## EXISTING MEMORIES (semantically similar)
{existing_memories_json}

## JUDGMENT CRITERIA
- CONTRADICT: The memories propose conflicting root causes or mutually exclusive solutions.
  Example: v1 says "connection pool exhausted" but v2 says "DNS resolution failure".
- SUPPLEMENT: The new memory adds additional details, symptoms, or constraints.
  Example: v1 says "connection pool at 100%", new says "also observed gateway 504".
- DUPLICATE: Same root cause, same solution, same customer/product context.
  Example: v1 and new describe the exact same incident from different dialog sessions.
- UNRELATED: Different issues despite semantic similarity.
  Example: Both mention "timeout" but one is DB timeout, other is API timeout.

## OUTPUT FORMAT (JSON only, no extra text)
{
    "relationships": [
        {
            "existing_memory_id": "uuid",
            "relationship": "contradict|supplement|duplicate|unrelated",
            "confidence": 0.0-1.0,
            "explanation": "Brief reason for the judgment"
        }
    ],
    "global_recommendation": {
        "action": "update_old|insert_new|merge_both|ignore_new",
        "target_memory_id": "uuid or null",
        "reasoning": "Why this action is recommended",
        "merge_instructions": "If merge_both: how to combine the content"
    }
}
"""
```

##### 3.3.2.1 基于 mem0 框架实现语义冲突检测

语义冲突检测整体引入 [mem0](https://github.com/mem0ai/mem0) 框架实现。mem0 在记忆冲突检测方面有成熟的内置能力，包括：

| mem0 内置能力 | 对应本项目场景 |
|-----------|------------------|
| `Memory.add()` 内置去重 | 写入时自动检测重复/相似记忆，返回冲突信息 |
| `Memory.search()` 语义检索 | 替代手动 pgvector 查询，内置结构化过滤支持 |
| 内置版本管理 | 记忆更新时自动维护版本链，无需手动管理 parent_memory_id |
| 结构化输出约束 | 确保 LLM 冲突判断结果始终符合预期 JSON Schema |
| 可插拔存储后端 | 支持对接 PostgreSQL + pgvector，与现有架构兼容 |

**架构层次**：

```text
  本项目冲突检测层
  +------------------------------------------+
  | CONFLICT_DETECTION_PROMPT (自定义)        |
  |  定义冲突判断标准、关系分类、处理动作  |
  +--------------------+---------------------+
                       | 调用
                       v
  +------------------------------------------+
  | mem0 框架层 (引入)                    |
  |  Memory.add()  -> 内置去重 + 冲突检测  |
  |  Memory.search() -> 语义检索 + 结构化过滤 |
  |  结构化输出约束 + 版本管理          |
  +--------------------+---------------------+
                       | 存储
                       v
  +------------------------------------------+
  | PostgreSQL + pgvector (现有)            |
  |  agent_memories 表                      |
  +------------------------------------------+
```

**实现代码**：

```python
from mem0 import Memory

class ConflictDetector:
    """
    基于 mem0 框架的语义冲突检测器。
    mem0 提供内置的去重、版本管理和结构化输出约束，
    我们只需注入自定义的 CONFLICT_DETECTION_PROMPT 作为判断逻辑。
    """

    def __init__(self, db_url: str, llm_config: dict):
        self.mem0 = Memory.from_config({
            "vector_store": {
                "provider": "pgvector",
                "config": {
                    "connection_string": db_url,
                    "collection_name": "agent_memories",
                    "embedding_model_dims": 1536,
                }
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": llm_config["model"],
                    "api_key": llm_config["api_key"],
                    "base_url": llm_config["base_url"],
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "text-embedding-v4",
                    "api_key": llm_config["api_key"],
                    "base_url": llm_config["base_url"],
                }
            },
            "custom_fact_extraction_prompt": CONFLICT_DETECTION_PROMPT,
        })

    async def detect_and_store(self, new_memory: dict) -> dict:
        """
        写入新记忆并自动检测冲突。
        mem0.add() 内部会：
        1. 向量化新记忆
        2. 检索相似已有记忆
        3. 调用 CONFLICT_DETECTION_PROMPT 做冲突判断
        4. 根据判断结果自动执行 update/insert/merge/ignore
        5. 维护版本链
        """
        result = self.mem0.add(
            messages=[{
                "role": "user",
                "content": json.dumps({
                    "memory_type": new_memory["memory_type"],
                    "content_summary": new_memory["content_summary"],
                    "customer_id": new_memory["customer_id"],
                    "product": new_memory["product"],
                    "version": new_memory["version"],
                    "error_codes": new_memory["error_codes"],
                    "severity": new_memory["severity"],
                    "importance_score": new_memory["importance_score"],
                    "source_dialog_id": new_memory.get("source_dialog_id"),
                    "timestamp": new_memory["timestamp"],
                }, ensure_ascii=False),
            }],
            user_id=new_memory["customer_id"],
            metadata={
                "product": new_memory["product"],
                "version": new_memory["version"],
                "error_codes": new_memory["error_codes"],
            },
        )
        # mem0 returns conflict info + action taken + version info
        return result

    async def search_with_version_awareness(self, query: str, customer_id: str, top_k: int = 5) -> list[dict]:
        """
        版本感知检索。
        mem0.search() 内部会返回同主题下的完整版本链。
        """
        results = self.mem0.search(
            query=query,
            user_id=customer_id,
            top_k=top_k,
            filters={"status": {"in": ["active", "superseded"]}},
        )
        return results
```

**mem0 与现有架构的关系**：

| 原有组件 | mem0 替代后 | 说明 |
|----------|-----------|------|
| 手动 pgvector 查询 | mem0 `Memory.search()` | 内置结构化过滤 + 版本链返回 |
| 手动 embedding + INSERT | mem0 `Memory.add()` | 内置去重 + 冲突检测 + 版本管理 + 写入 |
| `parent_memory_id` 手动管理 | mem0 内置版本链 | 更新时自动维护版本关系 |
| JSON Schema 手动检验 | mem0 `output_format` | 结构化输出自动约束 |
| `agent_memories` 直接操作 | mem0 抽象层 | 可配置对接 PostgreSQL + pgvector，保留现有表结构 |

> 本项目仍保留自定义的 CONFLICT_DETECTION_PROMPT 作为冲突判断逻辑，因为售后技术支持场景的冲突判断标准（矛盾/补充/重复/无关 + 建议动作）是业务特定的，通用框架无法完全覆盖。mem0 提供的是去重、版本管理、结构化输出等基础能力，判断逻辑仍由我们的 Prompt 驱动。

##### 3.3.3 定期记忆整合（Periodic Memory Consolidation）

版本化会导致同一主题下积累大量版本链。定期整合用 LLM 对同一主题下的多个记忆版本做审查和合并：

```text
  Trigger: cron job (daily, 2 AM) or manual trigger via API
       |
       v
  Step 1: Find topics with >= 3 versions
    SELECT topic_group_id, COUNT(*) as version_count
    FROM agent_memories
    WHERE topic_group_id IS NOT NULL
    GROUP BY topic_group_id HAVING COUNT(*) >= 3
       |
       v
  Step 2: LLM consolidation per topic
    Input: version_chain (all versions with full metadata)
    Tasks:
      (a) Identify obsolete versions -> mark status=archived
      (b) Identify complementary versions -> merge into a new vN+1
      (c) Validate consolidated content: no hallucination, citations preserved
       |
       v
  Step 3: Execute
    - INSERT new consolidated version (version=N+1, parent=N)
    - UPDATE old versions: status=archived
    - Write audit event: CONSOLIDATED
```

**整合 Prompt 设计**：

```python
CONSOLIDATION_PROMPT = """
You are consolidating multiple versions of a support knowledge memory.

Topic: {topic_summary}
Customer: {customer_id}
Product: {product}
Total versions: {version_count}

## VERSION HISTORY
{version_chain_json}

## YOUR TASKS
1. Identify which versions are OBSOLETE (superseded by later versions, no unique info).
   -> Mark them as "status": "archived"
2. Identify which versions contain COMPLEMENTARY info that should be merged.
   -> Extract unique insights from each and combine into a single accurate summary.
3. Produce a consolidated memory entry.
   -> Must preserve ALL unique diagnostic details, error codes, and solutions.
   -> Must NOT hallucinate or add information not present in the source versions.
   -> If contradictory info exists between versions, note it as "known_ambiguity".

## OUTPUT FORMAT (JSON only)
{
    "archived_version_ids": ["v1","v2"],
    "consolidated_content": {
        "content_summary": "...",
        "root_cause_category": "...",
        "error_codes": ["..."],
        "severity": "...",
        "resolution": "...",
        "known_ambiguities": ["if any contradictions found"],
        "confidence": 0.0-1.0
    },
    "consolidation_notes": "What changed and why"
}
"""
```

**整合的触发条件**：

| 触发方式 | 说明 |
|----------|------|
| 定时任务 | 每天凌晨 2:00 执行，扫描所有 version_count >= 3 的主题 |
| 事件驱动 | 某个主题新增第 5 个版本时触发即时整合 |
| 手动触发 | `POST /api/agent-memories/consolidate` 端点 |

#### 3.4 L3 检索模型：三维评分 + 两阶段检索

L3 检索不依赖单一维度排序，而是采用**三维加权评分模型**，并对召回过程做**两阶段级联**以平衡效率与精度。

**三维评分公式**：

```text
final_score = α x recency_score + β x relevance_score + γ x importance_score
```

| 维度 | 含义 | 计算方式 | 范围 |
|------|------|----------|------|
| **relevance_score** (相关性) | 与当前查询的语义相似度 | pgvector cosine_similarity(query_embedding, memory.embedding) | 0.0-1.0 |
| **recency_score** (时近性) | 记忆的新鲜程度 | 指数衰减函数：e^(-λ x days_since_created)，λ 控制衰减速度 | 0.0-1.0 |
| **importance_score** (重要性) | 记忆本身的质量权重 | 写入时的 importance_score / 10，归一化到 0.0-1.0 | 0.0-1.0 |

**权重可配（按业务场景调整）**：

| 业务场景 | α (recency) | β (relevance) | γ (importance) | 理由 |
|----------|------------|---------------|----------------|------|
| 售后技术支持（默认） | 0.30 | 0.50 | 0.20 | 平衡：语义匹配优先，最近经验加权 |
| 在线客服 | 0.45 | 0.40 | 0.15 | 用户最近说的最重要 |
| 知识问答 | 0.10 | 0.70 | 0.20 | 语义准确性压倒一切 |
| 工单复盘 | 0.20 | 0.40 | 0.40 | 高价值历史案例权重最高 |

**时近性衰减函数**：

```python
import math
from datetime import datetime, timezone

def recency_score(created_at: datetime, half_life_days: int = 30) -> float:
    days = (datetime.now(timezone.utc) - created_at).days
    decay_rate = math.log(2) / half_life_days  # 30-day half-life
    return math.exp(-decay_rate * max(days, 0))

# Examples: 7 days ago -> 0.85, 30 days ago -> 0.50, 90 days ago -> 0.125
```

**策略一：元数据预过滤（Metadata Pre-Filter）**

在做向量检索之前，先用结构化字段筛掉大批不相关条目，缩小搜索空间：

```text
  Full search space: 100,000+ memories
    |
    +-- Filter by customer_id      -> 2,000 (same customer)
    +-- Filter by product            -> 500 (same product)
    +-- Filter by memory_type        -> 200 (historical_incident + expert_experience only)
    +-- Filter by time_range         -> 120 (last 6 months)
    +-- Filter by enabled = true     -> 100
    |
    v
  Reduced search space: 100 -> Enter vector retrieval
```

如果预过滤后结果仍不足，逐步放宽过滤条件（先去掉时间限制，再放宽到同产品线的其他客户经验）。

**策略二：两阶段检索（Two-Stage Retrieval）**

```text
  Stage 1 - Coarse Recall (Bi-Encoder)
  +--------------------------------------------+
  | pgvector cosine_similarity Top-50            |
  | Fast, suitable for full scan                |
  | Recall-first (better to over-recall)        |
  +-------------------+------------------------+
                      | Top-50 candidates
                      v
  Stage 2 - Fine Ranking (Cross-Encoder)
  +--------------------------------------------+
  | Cross-Encoder pairwise scoring              |
  | Input: (query, memory[i]) text pair         |
  | Output: precise relevance score             |
  | Precision-first, only scores 50 items       |
  +-------------------+------------------------+
                      |
                      v
  3D weighted ranking (alpha*recency + beta*cross_score + gamma*importance)
                      |
                      v
  Top-5 injected into L1 context
```

Cross-Encoder 模型选择：

| 模型 | 适用场景 | 说明 |
|------|----------|------|
| `gte-rerank-v2` | 通用中文/英文 | 阿里通义实验室，性能优秀 |
| `bge-reranker-v2-m3` | 多语言 | BAAI，支持中英文混合检索 |
| 线上 `qwen3-rerank` | 降级方案 | 已有 OpenAI-compatible 接入，无需额外部署 |

**降级策略**：如果 Cross-Encoder 不可用（未部署 / 超时），降级为纯三维加权排序（relevance 直接使用 pgvector cosine_similarity），确保服务可用性。

#### 3.5 L3 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `L3_EMBEDDING_MODEL` | `text-embedding-v4` | 长期记忆向量化模型 |
| `L3_VECTOR_TOP_K` | 10 | 最终返回条数 |
| `L3_STAGE1_TOP_K` | 50 | 粗召回候选数 |
| `L3_SINK_THRESHOLD_DAYS` | 3 | L2 -> L3 下沉天数 |
| `L3_RECENCY_HALF_LIFE_DAYS` | 30 | 时近性半衰期 |
| `L3_SCORE_ALPHA` | 0.30 | recency 权重 |
| `L3_SCORE_BETA` | 0.50 | relevance 权重 |
| `L3_SCORE_GAMMA` | 0.20 | importance 权重 |
| `L3_IMPORTANCE_THRESHOLD` | 5 | 记忆价值的通过阈值 |
| `L3_DEDUP_SIMILARITY_THRESHOLD` | 0.92 | 重复内容过滤的相似度阈值 |
| `L3_CONFLICT_SIMILARITY_THRESHOLD` | 0.95 | 冲突检测的语义相似度阈值 |
| `L3_CROSS_ENCODER_MODEL` | `gte-rerank-v2` | 精排模型 |

## 三层之间的协作流程

### 场景 A：正常多轮对话（L1 够用）

```
用户提问
  → L1 ContextWindowManager 计算 token 用量
  → 用量 < 60%，正常追加到对话历史
  → 更新 current_task（如有阶段切换）
  → LLM 基于完整 L1 上下文回答
  → 异步写一份到 L2 Redis（完整对话 + current_task 快照）
```

### 场景 B：长对话，L1 不够用

```
用户提问
  → L1 ContextWindowManager 计算 token 用量
  → 用量 > 80%，触发激进压缩
  → 旧轮次压缩为一句话摘要
  → 从 L2 Redis 拉取 session summary + 最近 N 条消息
  → 从 L2 Redis 拉取 user recent_memories Top 5
  → 拼入 system prompt 区域
  → LLM 基于 L1+L2 补充后的上下文回答
```

### 场景 C：跨会话，需要历史经验

```
新会话开始
  → Agent 从 IncidentContext 提取 customer_id / product / version / error_codes
  → L3 长期记忆查询：
      ① pgvector 语义相似度 → 相关历史案例
      ② 结构化过滤 → 同客户/同产品/同错误码案例
  → L2 Redis 查询 session recent context → 当前会话内存
  → 合并结果注入 L1 system prompt
  → LLM 基于 L1+L2+L3 综合上下文回答
```

### 场景 D：会话结束，记忆归并

```
会话结束
  → 生成会话级摘要（LLM）
  → L2 Redis：设置 3 天 TTL
  → 标记重要记忆（根据 user feedback / 问题解决情况）
  → 超过 3 天后，Redis key 自动过期
  → 但在此之前，异步归并到 L3：
      ① 向量化高价值记忆 → 写入 agent_memories + embedding
      ② 更新客户运维画像统计（ops_profile.incident_summary）
```

## 模块文件清单（新建 / 修改）

### Python（ai-service）

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/agents/memory/context_window.py` | **新建** | L1 ContextWindowManager、摘要压缩、Token Buffer、current_task |
| `app/agents/memory/redis_memory.py` | **新建** | L2 RedisSessionMemory、记忆访问频率追踪、L2→L1补充逻辑 |
| `app/agents/memory/long_term.py` | **新建** | L3 长期记忆语义检索、跨客户经验迁移 |
| `app/agents/memory/memory_manager.py` | **新建** | 三层统一协调入口 MemoryManager |
| `app/agents/memory/models.py` | **修改** | 升级数据模型，支持三层来源标记 |
| `app/agents/memory/__init__.py` | **修改** | 导出新模块 |
| `app/agents/states/support_state.py` | **修改** | 新增 current_task 字段、三层记忆追踪字段 |
| `app/agents/graphs/support_supervisor.py` | **修改** | 集成 MemoryManager，替换旧的 MemoryRetriever/Writer/Evaluator |
| `app/core/config.py` | **修改** | 新增 Redis 连接配置、L2/L3 参数 |
| `app/db/repositories.py` | **修改** | 新增 pgvector 记忆检索方法 |
| `app/agents/memory/retriever.py` | **删除/标记废弃** | 被 MemoryManager 替代 |
| `app/agents/memory/writer.py` | **删除/标记废弃** | 被 MemoryManager 替代 |
| `app/agents/memory/policy.py` | **迁移** | 写入策略逻辑迁移到 MemoryManager |
| `app/agents/memory/evaluator.py` | **迁移** | 评估逻辑迁移到 MemoryManager |

### Java（backend-java）

| 文件 | 操作 | 说明 |
|------|------|------|
| `domain/AgentMemory.java` | **修改** | 新增 embedding 字段映射 |
| `domain/SupportCustomerStats.java` | **新建** | 客户统计视图（基于 agent_memories + agent_runs 聚合） |
| `service/SupportCustomerService.java` | **修改** | 新增 getOpsProfile / refreshOpsProfile 方法 |
| `controller/SupportCustomerController.java` | **修改** | 新增 ops-profile 端点 |
| `dto/agentops/SupportCustomerOpsProfileResponse.java` | **新建** | 客户运维画像响应 DTO |
| `resources/db/migration/V20260627__add_memory_embedding.sql` | **新建** | agent_memories 加 embedding 列迁移 |
| (无需新建 user_profiles 表) | — | 客户画像复用现有表（support_customers.metadata JSONB） |

### 配置文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `.env.example` | **修改** | 新增 Redis 连接串、L2/L3 参数 |
| `.env` | **修改** | 本地配置 Redis 连接信息 |

### Redis（已有 docker-compose，无需新建 infra）

已有 `redis:7-alpine` 服务，确保 `.env` 中有：
```env
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
```

## 实施步骤

### Phase 1：基础设施准备

1. 确认 Redis 可连接（`docker compose up -d redis`）
2. `.env` 补 Redis 连接配置
3. `ai-service/app/core/config.py` 加 Redis 配置读取
4. `requirements.txt` / `pyproject.toml` 加 `redis[hiredis]>=5.0.0` 依赖

### Phase 2：L1 短期记忆

1. 新建 `context_window.py`：ContextWindowManager
2. 实现 Token Buffer 两级水位
3. 实现摘要压缩（轻量 + 激进）
4. 实现 current_task 结构化字段的读写（从 SupportAgentState 派生）
5. 在 `SupportSupervisorWorkflow` 中集成

### Phase 3：L2 中期记忆

1. 新建 `redis_memory.py`：RedisSessionMemory
2. 实现 session messages 的 LIST 写入/读取
3. 实现 recent_memories 的 ZSET 写入/读取
4. 实现 L2→L1 补充逻辑
5. 在 ContextWindowManager 中接入 L2 补充

### Phase 4：L3 长期记忆

1. 数据库迁移：agent_memories 加 embedding 列
2. Java 侧：SupportCustomerService 新增 getOpsProfile / refreshOpsProfile 方法
3. Java 侧：新建 SupportCustomerOpsProfileResponse DTO
4. 新建 `long_term.py`：语义检索（pgvector） + 结构化过滤
5. 新建 `customer_profile.py`：客户运维画像读写（操作 support_customers.metadata JSONB）
6. 新建 `memory_manager.py`：三层协调入口

### Phase 5：替换旧模块

1. 在 SupportAgentState 中新增三层记忆追踪字段
2. 在 SupportSupervisorWorkflow 中用 MemoryManager 替换旧的 MemoryRetriever/Writer/Evaluator
3. 旧文件标记废弃（不立即删除，保留引用兼容）
4. 前端 MemoryCenterPage 对接新的 L3 API

### Phase 6：验证与文档

1. 单元测试：ContextWindowManager token 计算、压缩逻辑、Redis 读写
2. 集成测试：三层协作的完整场景
3. 更新 `PROJECT_CONTEXT.md`、`docs/handoff/CURRENT_STATE.md`
4. 更新 `ai-service/README.md`、`backend-java/README.md`

## 验证方式

- `python -m pytest ai-service/tests -q -k memory`
- `redis-cli KEYS "session:*"` 验证 L2 数据写入
- `SELECT * FROM agent_memories WHERE embedding IS NOT NULL;` 验证 L3 向量写入
- `mvn compile -q -f backend-java/pom.xml`
- `npm run build` (前端)
- 全链路 smoke：启动服务后发送多轮对话，检查 current_task 更新 + L2 Redis 数据 + L3 向量写入

## 与旧模块的迁移策略

| 旧组件 | 新位置 | 迁移方式 |
|--------|--------|----------|
| `MemoryRetriever`（规则打分检索） | `MemoryManager.retrieve()` | L3 升级为 pgvector 语义检索 + 结构化过滤 |
| `MemoryWriter`（候选不持久化） | `MemoryManager.write()` | 统一写入 L2 Redis + L3 PostgreSQL |
| `MemoryPolicy`（四条件门禁） | `MemoryManager.write()` 内部 | 保留门禁逻辑，增加置信度阈值 |
| `MemoryEvaluator`（召回率/使用率） | `MemoryManager.evaluate()` | 升级为三层来源的召回率/命中率统计 |
| `MemoryRetrievalEvent` | 新 models | 增加 `source_layer` 字段标记 L1/L2/L3 |
| `MemoryWriteCandidate` | 新 models | 增加 `target_layer`、`persisted` 字段 |
| `_default_memories()` | 删除 | L2/L3 替代硬编码种子数据 |

## 备注

- Redis 已在 `docker-compose.yml` 中就绪（`redis:7-alpine`），无需新建基础设施。
- pgvector 已在 PostgreSQL 中可用（`pgvector/pgvector:pg16`），L3 向量检索可立即对接。
- 本计划不涉及前端 MemoryCenterPage 的 UI 重构（将在后续单独计划）。
- L3 的客户运维画像不新建 user_profiles 表，而是复用和扩展已有的 support_customers / agent_memories / agent_runs 表。因为本项目定位为企业售后 Ops 平台，“用户”是企业客户，不是个人消费者。
- L3 的客户运维画像与现有的 `learning-weak-points`（薄弱点学习）模块互补：客户画像侧重"这个客户有什么资产、出过什么问题、环境怎么配"，薄弱点侧重"当前工单哪些知识域需要补强"。
