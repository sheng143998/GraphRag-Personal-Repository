# 2026-06-08 Advanced RAG 评估

## 评估范围

本实验记录 `advanced-rag-evaluation` 相关的 RAG / Advanced RAG / GraphRAG 评估思路。实验目标是用固定问题、固定引用或离线样例观察检索质量、引用命中和回答 grounded 程度。

## 覆盖内容

- 对比 `basic-rag`、`advanced-rag` 或 `graph-rag` 在固定样例上的表现。
- 关注 recall@k、precision@k、MRR、citation hit、grounded score 与 retrieval score。
- 离线样例不依赖真实 LLM、embedding、reranker 或数据库。
- HTTP smoke 样例通过 Spring Boot `/api/*` 进入系统，不从浏览器直接调用 FastAPI。

## 结果记录

- 评估结果用于指导后续检索策略、query rewrite、multi-query、rerank、Parent-Child 和 GraphRAG 优化。
- 若结果不稳定，应优先固定评估集、引用 id 和期望引用 chunk，再扩大样例数量。

## 后续优化

- 增加基础 RAG 与 Advanced RAG 在同一问题集上的对比。
- 增加 GraphRAG 关系证据、扩展词命中和实体覆盖相关样例。
- 将评估输出沉淀到 `docs/experiments/eval-questions.md` 或后端实验历史表。
