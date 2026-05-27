# GitHub 仓库创建与远程推送计划

更新时间：2026-05-27

## 当前目标

在 GitHub 上创建当前项目的远程仓库，配置本地 Git `origin`，并将 `main` 分支推送到远程仓库。

## 默认决策

- 仓库名默认使用当前目录名：`agent-vue-java-springboot-fastapi-ai`。
- 仓库可见性默认使用私有仓库，避免误公开本地学习项目和阶段性代码。
- 远程配置默认使用 GitHub CLI 返回的仓库地址，不手写伪造远程地址。

## 涉及范围

- GitHub CLI 登录态检查。
- GitHub 仓库创建。
- 本地 Git `origin` 配置。
- `main` 分支推送。
- `PROJECT_CONTEXT.md` 当前待办与阶段级变更摘要。
- `docs/handoff/CURRENT_STATE.md` 最新交接状态。

## 预计修改文件

- `PROJECT_CONTEXT.md`
- `docs/plans/2026-05-27-github-repo-create-and-push.md`
- `docs/reviews/2026-05-27-github-repo-create-and-push-review-prompt.md`
- `docs/testing/failures/2026-05-27-github-repo-create-and-push-notes.md`
- `docs/handoff/CURRENT_STATE.md`

## 执行步骤

1. 检查本机是否安装 GitHub CLI。
2. 检查 GitHub CLI 是否已登录。
3. 确认本地 Git 工作区干净、当前分支为 `main`。
4. 创建 GitHub 私有仓库并配置 `origin`。
5. 推送 `main` 分支并设置 upstream。
6. 验证远程地址、远程分支和本地状态。

## 验证方式

- 查看 GitHub CLI 登录态。
- 查看 `git remote -v`。
- 查看 `git status --short`。
- 查看 `git branch -vv`。
- 查看 `git ls-remote --heads origin main`。

## 当前风险

- 当前环境网络受限，GitHub 创建仓库或推送可能失败。
- 如果本机 GitHub CLI 未登录，需要用户完成授权。
- 如果 GitHub 上已存在同名仓库，需要改用已有仓库或选择新仓库名。
