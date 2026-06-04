# 前端模块

## 模块职责

前端模块负责提供本地知识库和检索增强生成能力的用户界面，包括知识库管理、文档上传入口、聊天问答、引用来源展示、策略选择和后续实验结果展示。

前端默认只调用 Java 后端对外接口，不直接访问 Python 人工智能服务。

## 技术栈

- Vue 3。
- TypeScript。
- Vite。
- Pinia，用于状态管理。

## 目录结构说明

```text
frontend/
├─ src/
│  ├─ api/              # 统一接口调用入口
│  ├─ components/       # 通用组件
│  ├─ layouts/          # 页面布局
│  ├─ pages/            # 页面级组件
│  ├─ router/           # 路由配置
│  ├─ stores/           # 状态管理
│  ├─ types/            # 类型定义
│  └─ utils/            # 通用工具
├─ scripts/             # 前端辅助脚本
├─ index.html
├─ package.json
└─ vite.config.ts
```

## 本地启动方式

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

## 常用命令

```powershell
npm.cmd run dev
npm.cmd run build
npm.cmd run type-check
```

## 环境变量说明

前端请求后端接口时，应通过统一接口客户端读取基础地址配置。不要在页面组件中直接拼接后端地址。

常见配置项：

- `VITE_API_BASE_URL`：Java 后端接口基础地址。

## 关键代码入口

- `src/main.ts`：前端应用入口。
- `src/router/`：路由入口。
- `src/api/`：后端接口调用入口。
- `src/stores/`：全局状态入口。
- `src/pages/chat/`：聊天问答页面。
- `src/pages/knowledge-base/`：知识库页面。
- `src/pages/documents/`：文档页面。

## 重点审查文件

- `src/api/`
- `src/stores/`
- `src/pages/chat/`
- `src/components/SourceList.vue`
- `src/components/StrategySelector.vue`
- `src/components/UploadEntry.vue`

## 与其他模块的调用关系

```text
前端页面
-> frontend/src/api/
-> Java 后端对外接口
-> Python 人工智能服务
-> PostgreSQL 与 pgvector
```

## 当前已实现能力

- 前端工程基础结构。
- 工作台页面基础结构。
- 与后端接口对接的预留位置。
- 文档列表已展示后端返回的文档状态、解析器和 chunk 数量。

## 当前占位实现

- 文档上传入口已接入 `POST /api/documents/upload` 单篇 JSON Demo 与 multipart 文本文件上传，批量上传、进度展示和真实二进制解析仍待补充。
- 检索增强生成结果展示仍需继续对齐后端返回结构。
- 策略选择、实验对比和评估页面仍需继续完善。

## 后续待补能力

- 完整聊天流程。
- 引用来源列表。
- 文档上传进度与解析状态。
- 检索过程可视化。
- 策略配置与实验结果展示。

## 常见问题

- 如果依赖安装失败，先确认 Node.js 版本和本地缓存目录权限。
- 如果页面无法访问后端，先确认 Java 后端已启动，并检查 `VITE_API_BASE_URL`。
- 如果类型检查失败，优先检查接口类型是否与后端响应结构一致。
