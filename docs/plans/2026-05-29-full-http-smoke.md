# 2026-05-29 全链路 HTTP Smoke 验证

## 背景
完成知识库 CRUD + 文档删除后，启动三端服务做全链路 HTTP smoke。

## 已验证接口
| # | 接口 | 结果 |
|---|---|---|
| 1 | `POST /api/knowledge-bases` | ✅ 200 |
| 2 | `GET /api/knowledge-bases/{id}` | ✅ 200, docs=0 |
| 3 | `PUT /api/knowledge-bases/{id}` | ✅ 200, name updated |
| 4 | `POST /api/documents/upload` | ✅ 200, status=INDEXED, chunks=1 |
| 5 | `GET /api/documents/{id}` | ✅ 200, chunkCount=1, chunks=[1] |
| 6 | `GET /api/documents?knowledgeBaseId=` | ✅ 200, count=1 |
| 7 | KB detail (stats) | ✅ docs=1, chunks=1 |
| 8 | `DELETE /api/documents/{id}` | ✅ 200 → 404 |
| 9 | `DELETE /api/knowledge-bases/{id}` | ✅ 200 → 404 |

## 修复的问题
- AI 服务端口：8001 → 8000
- documentType 枚举大小写：自动 `.toLowerCase()`
- DB 凭据注入：batch 脚本传 `DB_USERNAME`/`DB_PASSWORD`
- chunks=[] bug：AI 服务 `config.py` 从 `DB_URL` 构造连接
