# 2026-05-27 PROJECT_CONTEXT 变更记录精简

## 背景

当前 `PROJECT_CONTEXT.md` 的 2026-05-27 变更记录已经包含大量接口级流水账。用户决定采用“方案 1 + 方案 5”：`PROJECT_CONTEXT.md` 只保留阶段级摘要和文档索引，接口细节继续放在 `docs/plans/`、`docs/reviews/`、`docs/testing/failures/` 和 `docs/handoff/`。

## 当前目标

- 压缩 `PROJECT_CONTEXT.md` 的 2026-05-27 变更记录。
- 保留关键阶段成果、当前待办和文档索引。
- 明确后续维护规则：接口级细节不再写入 `PROJECT_CONTEXT.md`。

## 涉及模块

- 项目总上下文文档
- 交接文档
- review 与过程记录

## 预计修改文件

- `PROJECT_CONTEXT.md`
- `docs/reviews/2026-05-27-project-context-changelog-compaction-review-prompt.md`
- `docs/testing/failures/2026-05-27-project-context-changelog-compaction-notes.md`
- `docs/handoff/CURRENT_STATE.md`

## 非范围

- 不删除已有 plans/reviews/failures 细节文档。
- 不改变代码。
- 不改变接口行为。

## 验证方式

- 人工检查 2026-05-27 变更记录不再逐接口展开。
- 确认仍可通过文档索引找到接口级计划、review 和失败复盘。
- 确认当前待办和 API 规划不丢失。

## 当前风险

- 过度压缩可能让后续 Agent 找不到细节，因此需要保留索引入口。
