# 2026-05-29 文档上传入库 Demo 接口过程记录

## 背景

本次任务是推进 Phase 2 的第一个入库接口：让 `POST /api/documents/upload` 可以触发 AI 服务完成文档解析、切块和 embedding 入库 Demo。

## 当前状态

本轮接口已完成代码实现，并完成 Java 后端构建、前端构建和 AI 服务语法验证。

## 已知风险

- 本地数据库和服务状态未知，可能无法立即做完整 HTTP smoke。
- 当前文档解析和 embedding 多处仍是占位实现，需要在最终交付中明确说明。

## 问题记录

### 问题 1：Java 后端没有 Maven wrapper

- 现象：执行 `.\mvnw.cmd test` 失败，提示无法识别 `.\mvnw.cmd`。
- 触发场景：在 `backend-java/` 下按历史文档中的 wrapper 命令验证。
- 根因分析：当前目录只有 `.mvn/` 和 `pom.xml`，没有 `mvnw.cmd` 文件。
- 解决方案：改用本机已安装的 `mvn.cmd test`。
- 后续避免方式：若项目希望统一 wrapper 命令，需要补充 Maven wrapper 文件；否则文档中的验证命令应写为 `mvn.cmd test`。
- 是否补充自动化测试：不涉及业务逻辑。

### 问题 2：当前 Python 环境未安装 pytest

- 现象：执行 `python -m pytest` 失败，提示 `No module named pytest`。
- 触发场景：在 `ai-service/` 下尝试运行 AI 服务测试。
- 根因分析：当前 Python 环境只有运行基础能力，未安装 `pyproject.toml` 中的 dev 依赖。
- 解决方案：本轮改用 `python -m compileall app tests` 做语法验证。
- 后续避免方式：安装 `ai-service[dev]` 后再运行 pytest。
- 是否补充自动化测试：已有测试文件，本轮未能执行。

### 问题 3：PowerShell 拦截 npm 脚本入口

- 现象：执行 `npm run build` 失败，提示当前系统禁止运行 `npm.ps1`。
- 触发场景：在 `frontend/` 下使用 PowerShell 默认 npm 入口。
- 根因分析：本机 PowerShell 执行策略禁止加载 npm 的 ps1 包装脚本。
- 解决方案：改用 `npm.cmd run build`，构建通过。
- 后续避免方式：Windows 验证命令优先使用 `npm.cmd`。
- 是否补充自动化测试：不涉及业务逻辑。

### 问题 4：Java 编译结束阶段仍打印本地 Maven jar 访问拒绝

- 现象：`mvn.cmd test` 最终 `BUILD SUCCESS`，但 javac 关闭 jar 时打印 `AccessDeniedException`。
- 触发场景：Java 后端编译阶段。
- 报错摘要：路径为 `backend-java/maven-repo/jakarta/transaction/jakarta.transaction-api/2.0.1/jakarta.transaction-api-2.0.1.jar`。
- 根因分析：这是历史已出现的本地 Maven 依赖 jar 占用或权限问题。
- 解决方案：本轮不做破坏性清理，因为构建已成功。
- 后续避免方式：如需彻底处理，只清理该单个依赖目录并重新拉取。
- 是否补充自动化测试：不涉及业务逻辑。

## 已执行验证

- `mvn.cmd test`：通过。
- `npm.cmd run build`：通过。
- `python -m compileall app tests`：通过。
- `python -m pytest`：未通过，缺少 pytest。
- HTTP smoke：未执行，未启动本地依赖服务。
