# OpenAI-compatible 模型 Adapter Review 提示

## 本次目标

将 AI 服务中的 LLM、Embedding、Rerank 从固定 stub registry 升级为可通过 `.env` 切换的 OpenAI-compatible adapter。当前按阿里百炼 DashScope 文档实现：

- LLM：`/chat/completions`
- Embedding：`/embeddings`，`text-embedding-v4`，`dimensions=1536`
- Rerank：`https://dashscope.aliyuncs.com/compatible-api/v1/reranks`，推荐 `qwen3-rerank`

## 重点 Review 文件

1. `ai-service/app/core/config.py`
2. `ai-service/app/services/adapters/openai_compatible.py`
3. `ai-service/app/services/adapters/registry.py`
4. `.env.example`
5. `ai-service/README.md`

## 重点检查点

- `.env` 自动加载是否只在本地生效，且不会覆盖已存在的系统环境变量。
- API Key 是否没有写入 `.env.example`、README 或其他提交文档。
- Embedding 是否向 OpenAI-compatible 接口传 `dimensions=1536`。
- Embedding 返回维度不一致时是否会明确报错，避免写入 pgvector 失败时难排查。
- Rerank 是否使用 `/reranks` 而不是 `/rerank`，base URL 是否为 `compatible-api/v1`。
- Rerank 返回结果是否能按原始 documents 顺序还原 score 列表。
- registry 是否在配置不完整时 fallback 到 stub adapter。
- trace 中 model name 是否能显示真实模型名。

## 已验证命令

```powershell
python -m compileall ai-service/app
mvn compile -q -f backend-java/pom.xml
cd frontend; npm run build
```

## 真实 adapter smoke

已执行真实小流量 smoke：

- Embedding 返回 1 条 1536 维向量。
- Rerank 返回 2 个分数，相关文档分数更高。
- LLM 返回内容；由于 smoke prompt 未提供 RAG 上下文，模型按系统约束拒绝无依据回答，符合当前 RAG 助手约束。

## 当前风险

- 用户当前 `.env` 中真实 API Key 已出现，`.env` 被 `.gitignore` 忽略，但不应出现在提交内容、日志或文档中。
- LLM 模型名 `qwen3.7-max` 是否长期有效需要以百炼模型列表为准。
- 已有轻量重试；当前还没有限流、熔断和成本统计。