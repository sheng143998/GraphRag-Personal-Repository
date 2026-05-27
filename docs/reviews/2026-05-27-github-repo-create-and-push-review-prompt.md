# GitHub 仓库创建与远程推送 Review 提示

更新时间：2026-05-27

## 本轮目标

创建 GitHub 私有仓库，配置本地 `origin`，并将当前 `main` 分支推送到远程。

## 重点 Review 顺序

1. GitHub 仓库
   - 仓库名是否符合预期。
   - 仓库可见性是否为私有。
   - 远程 `main` 分支是否存在。

2. 本地 Git 配置
   - `origin` 是否指向正确 GitHub 仓库。
   - `main` 是否已设置 upstream。
   - 工作区是否干净。

3. 隐私与忽略规则
   - `.env` 是否仍未被提交。
   - `.git-store/` 与 `.git-blocked-by-sandbox/` 是否未进入提交。
   - 本地依赖缓存和构建产物是否未进入远程仓库。

4. 项目文档
   - `PROJECT_CONTEXT.md` 是否将“配置远程 Git 仓库并推送 `main` 分支”标记为真实状态。
   - `docs/handoff/CURRENT_STATE.md` 是否记录远程地址和验证结果。

## 当前占位或待补

- 如果 GitHub CLI 未登录，需要用户完成授权后继续。
- 如果网络被当前环境拦截，需要用户在本机终端执行我给出的命令，或在 GitHub 网页上先创建空仓库。
