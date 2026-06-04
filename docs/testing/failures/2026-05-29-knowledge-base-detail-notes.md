# 2026-05-29 GET /api/knowledge-bases/{id} 失败复盘 / 观察记录

## 问题 1：PowerShell Out-File BOM
- 现象：Java 编译报 `\ufeff` 非法字符
- 根因：`Out-File -Encoding UTF8` 写入 UTF-8 BOM，javac 无法识别
- 处理：用 `[System.IO.File]::ReadAllBytes` + 字节级 BOM 检测移除
- 后续避免：写 Java 文件用 `-Encoding UTF8NoBOM`（PS 7+）或 `[System.Text.UTF8Encoding]::new($false)`

## 问题 2：Maven 仓库 jar 权限
- 现象：`AccessDeniedException` on `jakarta.transaction-api-2.0.1.jar`
- 根因：`maven-repo/` 中部分 jar 文件 ACL 受限
- 处理：删除损坏 jar，从 `.mvn/repository/` 恢复副本

## 问题 3：Maven 离线模式网络拒绝
- 现象：`Permission denied: getsockopt` 连接阿里云 Maven 镜像
- 根因：沙箱网络限制
- 处理：escalated 权限后 `mvn compile` 和 `mvn test` 均通过
