# 2026-05-27 RAG 实验删除接口与 HTTP smoke 过程记录

## 背景

本次任务是新增 `DELETE /api/rag/experiments/{id}`，并启动 PostgreSQL + Spring Boot 后端，把已完成的 RAG 实验接口链路通过真实 HTTP 调用跑通。

## 当前状态

`DELETE /api/rag/experiments/{id}` 已完成代码实现，并通过 Java 后端最小编译验证。数据库 + HTTP smoke 已按多条路径尝试，但当前环境无法提供可用 PostgreSQL，因此没有完成真实 HTTP 调用。

## 已知风险

- Docker Desktop 可能未启动，导致 PostgreSQL 无法启动。
- 8080 端口可能被占用。
- 当前本地 Maven jar 访问拒绝提示已多次出现，但此前 `mvn test` 最终成功。

## 问题 1：`mvn test` 成功但 javac 关闭本地依赖 jar 时打印访问拒绝

- 现象：`mvn test` 最终返回 `BUILD SUCCESS`，但编译阶段继续输出 `java.nio.file.AccessDeniedException`。
- 触发场景：在 `backend-java/` 下运行 `mvn test`。
- 报错摘要：访问被拒绝路径为 `backend-java/maven-repo/jakarta/transaction/jakarta.transaction-api/2.0.1/jakarta.transaction-api-2.0.1.jar`。
- 根因分析：这是前几轮已持续出现的本地 Maven 依赖 jar 占用或权限问题。当前编译和测试生命周期最终成功，未阻塞业务代码验证。
- 解决方案：本轮不做破坏性清理，只继续记录该本地环境问题。
- 后续避免方式：如需处理，应只清理该单个依赖目录并重新下载，避免删除整个本地仓库。
- 是否补充自动化测试：不涉及业务逻辑，无需新增自动化测试。

## 问题 2：Docker daemon 未运行，无法启动项目 PostgreSQL 容器

- 现象：`docker compose up -d postgres` 不可用，`docker-compose up -d postgres` 也无法连接 Docker API。
- 触发场景：尝试启动 `docker-compose.yml` 中的 `postgres` 服务。
- 报错摘要：
  - `docker compose`：当前 Docker 命令不支持 compose 子命令。
  - `docker-compose`：`failed to connect to the docker API ... docker_engine ... The system cannot find the file specified`。
  - 同时出现 `C:\Users\admin\.docker\config.json: Access is denied`。
- 根因分析：本机 Docker daemon 没有运行，且 Docker 配置文件存在访问限制。
- 解决方案：本轮不启动 Docker Desktop，也不修改用户 Docker 配置。记录为 HTTP smoke 阻塞原因。
- 后续避免方式：做容器联调前先确认 Docker Desktop 已运行，且当前用户可读取 Docker 配置。
- 是否补充自动化测试：不涉及业务逻辑，无需新增自动化测试。

## 问题 3：系统 PostgreSQL 可达但项目默认凭据不匹配

- 现象：本机存在正在运行的 `postgresql-x64-18` 服务，5432 端口可响应，但项目默认账号连接失败。
- 触发场景：使用 `psql` 尝试连接 `agent/agent_local_password` 和 `postgres/postgres`。
- 报错摘要：`用户 "agent" Password 认证失败`，`用户 "postgres" Password 认证失败`。
- 根因分析：本机系统 PostgreSQL 不是项目 docker-compose 初始化出来的数据库，账号密码与 `.env.example` 不一致；真实密码不应写入仓库或猜测。
- 解决方案：本轮不修改系统 PostgreSQL 账号，也不写入真实密码。
- 后续避免方式：需要用户提供本机 PostgreSQL 的临时连接信息，或启动项目专用 Docker PostgreSQL。
- 是否补充自动化测试：不涉及业务逻辑，无需新增自动化测试。

## 问题 4：临时 PostgreSQL 数据目录初始化被 Windows 沙箱限制

- 现象：尝试使用本机 PostgreSQL 18 的 `initdb` 在工作区 `.tmp/pg-smoke` 初始化临时测试库失败。
- 触发场景：运行 `initdb -D .tmp/pg-smoke -A trust -U agent`。
- 报错摘要：`could not create restricted token: error code 87`，`could not re-execute with restricted token`。
- 根因分析：当前 Windows 沙箱环境限制了 PostgreSQL `initdb` 的 restricted token 创建流程。
- 解决方案：本轮无法用临时本地 PostgreSQL 替代 Docker。
- 后续避免方式：优先使用项目 Docker PostgreSQL；若必须使用本机 PostgreSQL，需要在非受限环境中初始化数据目录。
- 是否补充自动化测试：不涉及业务逻辑，无需新增自动化测试。

## 已执行验证

- `mvn test`：通过，当前项目没有 Java 测试源码，因此主要验证编译、资源复制和 Spring Boot 构建链路。
- Docker PostgreSQL：尝试启动失败，Docker daemon 未运行。
- 系统 PostgreSQL：服务存在且端口可达，但项目默认凭据认证失败。
- 临时 PostgreSQL：`initdb` 被沙箱限制，未能创建测试库。
- HTTP smoke：未完成，因为没有可用数据库启动 Spring Boot 后端。
