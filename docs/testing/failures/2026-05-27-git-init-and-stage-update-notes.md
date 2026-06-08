# 2026-05-27 Git 初始化与阶段暂存更新

更新时间：2026-05-27

## 本轮观察

- 当前任务开始时，项目根目录还不是 Git 仓库。
- `.env` 已存在并由用户补全了本地数据库连接信息，因此必须依赖 `.gitignore` 保护。
- 用户尚未提供远程 Git 仓库 URL，因此远程推送无法在本轮直接完成。
- Codex 沙箱用户与项目目录所有者不同，常规 `.git` 目录会触发 Git 的目录所有权保护。
- 常规 `.git` 元数据目录在当前沙箱下会被反复加上拒绝写入 ACL，导致无法创建 `HEAD.lock` 和 `index.lock`。

## 风险与处理

### `.env` 泄露风险

- 现象：根目录存在真实本地 `.env`。
- 处理：保留 `.gitignore` 中 `.env` 与 `.env.*` 规则，并在提交前验证忽略规则。
- 后续避免：只提交 `.env.example`，真实本地配置只放 `.env`。

### 远程仓库缺失

- 现象：没有可用远程仓库地址。
- 处理：先完成本地 Git 初始化和首个提交；等待用户提供远程 URL 后再添加 `origin` 并推送。
- 后续避免：创建远程仓库后，将 URL 写入交接状态或由用户直接提供。

### 本地残留文件

- 现象：根目录存在 `Docker Desktop Installer.exe.part` 下载残留文件。
- 处理：通过 `.gitignore` 排除 `*.part`，避免误提交本地下载残留。
- 后续避免：下载器残留、临时压缩包、安装包不进入版本库。

### 沙箱 Git 元数据写入限制

- 现象：`git branch -M main` 报告无法创建 `HEAD.lock`，`git add` 报告无法创建 `index.lock`。
- 根因：当前 Codex 沙箱用户不是目录所有者，且普通 `.git` 目录被加上拒绝写入 ACL。
- 处理：将不可写的 `.git` 目录隔离为 `.git-blocked-by-sandbox/`，改用 Git 支持的独立元数据目录 `.git-store/`，根目录 `.git` 文件指向 `.git-store`。
- 后续避免：在当前沙箱内继续使用现有 `.git` 文件和 `.git-store/`；如果用户在自己 Windows 用户下重建仓库，可删除隔离目录后改回普通 `.git` 目录。

### 本地依赖缓存误入库风险

- 现象：首次 `git status` 中出现 `backend-java/.mvn/repository/` 与 `ai-service/ai_service.egg-info/`。
- 处理：补充 `.gitignore`，忽略 `backend-java/.mvn/repository/` 与 `*.egg-info/`。
- 后续避免：依赖缓存、构建产物和打包元数据不进入版本库。

## 自动化验证

- 已验证 `.env` 被 `.gitignore` 忽略。
- 已验证 `backend-java/.mvn/repository/` 被 `.gitignore` 忽略。
- 已验证 `ai-service/ai_service.egg-info/` 被 `.gitignore` 忽略。
- 已验证本地首个提交创建成功。
- 已验证工作区无未提交变更。
- 已确认当前没有配置远程仓库。
