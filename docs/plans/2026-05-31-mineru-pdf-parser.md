# 2026-05-31 MinerU PDF 解析器 — 接入 MinerU API

## 背景
AI 服务 `MinerUPdfParser` 目前为 reserved stub（仅返回适配器占位信息，不执行真实 PDF 解析）。
需接入 MinerU 官方 API 实现真正的 PDF 文档文本提取。

## 待调研（浏览器阅读 https://mineru.net/apiManage/docs）
1. API 认证方式（API Key / Token）
2. PDF 上传接口（endpoint、请求格式、base64 vs multipart）
3. 解析结果获取接口
4. 响应格式（Markdown / JSON / 纯文本）
5. 速率限制与配额
6. 需要配置的环境变量

## 实现方案（待确定）
- 读取 MinerU API 文档
- 实现 `MinerUPdfParser.parse()` 调用 MinerU API
- 敏感信息（API Key）通过 `.env` 配置，不硬编码
- 需用户提供 MinerU API Token 时主动提示

## 涉及文件
- `ai-service/app/rag/parsers/base.py` — MinerUPdfParser 重写
- `ai-service/app/core/config.py` — 新增 MinerU 相关配置项
- `.env` — 新增 MinerU API Key（用户手动配置）
- `ai-service/pyproject.toml` — 如需新增依赖
