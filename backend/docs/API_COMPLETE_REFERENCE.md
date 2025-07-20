# API完整参考文档

## 概述

SecondBrain提供RESTful API，支持完整的AI驱动知识管理功能。

## API基础信息

- **基础URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json` (除文件上传外)
- **文件上传**: `multipart/form-data`

## API端点分组

### 🔐 认证系统 (Auth) - 8个端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/login` | 用户登录 (FormData) |
| POST | `/auth/login/json` | 用户登录 (JSON) |
| POST | `/auth/refresh` | 刷新Token |
| POST | `/auth/logout` | 用户登出 |
| POST | `/auth/change-password` | 修改密码 |
| POST | `/auth/reset-password` | 重置密码请求 |
| POST | `/auth/reset-password/confirm` | 确认重置密码 |

### 👤 用户管理 (Users) - 5个端点

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/users/me` | 获取当前用户信息 |
| PUT | `/users/me` | 更新用户信息 |
| GET | `/users/me/stats` | 获取用户统计数据 |
| POST | `/users/me/change-password` | 修改密码 |
| DELETE | `/users/me` | 删除账户 |

### 💬 AI对话 (Chat) - 16个端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/chat/conversations` | 创建对话 |
| GET | `/chat/conversations` | 获取对话列表 |
| GET | `/chat/conversations/{id}` | 获取对话详情 |
| PUT | `/chat/conversations/{id}` | 更新对话 |
| DELETE | `/chat/conversations/{id}` | 删除对话 |
| POST | `/chat/completions` | AI聊天完成（OpenAI兼容） |
| POST | `/chat/conversations/{id}/messages` | 添加消息 |
| POST | `/chat/conversations/{id}/messages/{msg_id}/regenerate` | 重新生成消息 |
| POST | `/chat/analyze-attachments` | 分析附件 |
| GET | `/chat/conversations/{id}/branches` | 获取对话分支 |
| POST | `/chat/conversations/{id}/branches` | 创建对话分支 |
| POST | `/chat/conversations/{id}/branches/switch` | 切换分支 |
| POST | `/chat/conversations/{id}/branches/merge` | 合并分支 |
| GET | `/chat/conversations/{id}/branches/history` | 分支历史 |
| DELETE | `/chat/conversations/{id}/branches/{name}` | 删除分支 |

### 🤖 AI代理 (Agents) - 5个端点

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/agents/` | 获取代理列表 |
| GET | `/agents/{agent_id}` | 获取代理详情 |
| POST | `/agents/` | 创建自定义代理 |
| POST | `/agents/{agent_id}/execute` | 执行代理 |
| POST | `/agents/deep-research` | Deep Research专用接口 |

### 📁 知识空间 (Spaces) - 5个端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/spaces/` | 创建空间 |
| GET | `/spaces/` | 获取空间列表 |
| GET | `/spaces/{space_id}` | 获取空间详情 |
| PUT | `/spaces/{space_id}` | 更新空间 |
| DELETE | `/spaces/{space_id}` | 删除空间 |

### 📄 文档管理 (Documents) - 13个端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/documents/upload` | 上传文档 |
| GET | `/documents/` | 获取文档列表 |
| GET | `/documents/{document_id}` | 获取文档详情 |
| PUT | `/documents/{document_id}` | 更新文档 |
| DELETE | `/documents/{document_id}` | 删除文档 |
| GET | `/documents/{document_id}/content` | 获取文档内容 |
| GET | `/documents/{document_id}/preview` | 预览文档 |
| GET | `/documents/{document_id}/snapshot` | 获取文档快照 |
| POST | `/documents/{document_id}/download` | 下载文档 |
| POST | `/documents/search` | 搜索文档 |
| POST | `/documents/import-url` | 从URL导入 |
| POST | `/documents/analyze-url` | 分析URL内容 |
| POST | `/documents/batch-import-urls` | 批量导入URL |

### 📝 笔记管理 (Notes) - 19个端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/notes/` | 创建笔记 |
| GET | `/notes/` | 获取笔记列表 |
| GET | `/notes/recent` | 获取最近笔记 |
| GET | `/notes/{note_id}` | 获取笔记详情 |
| PUT | `/notes/{note_id}` | 更新笔记 |
| DELETE | `/notes/{note_id}` | 删除笔记 |
| GET | `/notes/{note_id}/linked` | 获取关联笔记 |
| POST | `/notes/{note_id}/tags` | 添加标签 |
| DELETE | `/notes/{note_id}/tags` | 删除标签 |
| GET | `/notes/tags/all` | 获取所有标签 |
| POST | `/notes/search` | 搜索笔记 |
| POST | `/notes/batch` | 批量创建笔记 |
| POST | `/notes/ai/generate` | AI生成笔记 |
| POST | `/notes/ai/summary` | AI总结内容 |
| GET | `/notes/{note_id}/versions` | 获取版本历史 |
| GET | `/notes/{note_id}/versions/{version}` | 获取特定版本 |
| POST | `/notes/{note_id}/versions/compare` | 比较版本 |
| POST | `/notes/{note_id}/versions/restore` | 恢复版本 |
| DELETE | `/notes/{note_id}/versions/cleanup` | 清理版本 |

### 🖍️ 标注管理 (Annotations) - 13个端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/annotations/` | 创建标注 |
| GET | `/annotations/my` | 获取我的标注 |
| GET | `/annotations/{annotation_id}` | 获取标注详情 |
| PUT | `/annotations/{annotation_id}` | 更新标注 |
| DELETE | `/annotations/{annotation_id}` | 删除标注 |
| GET | `/annotations/document/{document_id}` | 获取文档标注 |
| GET | `/annotations/document/{document_id}/pages` | 获取文档页面标注 |
| GET | `/annotations/document/{document_id}/pdf/{page}` | 获取PDF页标注 |
| POST | `/annotations/batch` | 批量创建标注 |
| POST | `/annotations/copy` | 复制标注 |
| POST | `/annotations/export` | 导出标注 |
| POST | `/annotations/pdf/batch` | 批量PDF标注 |
| GET | `/annotations/statistics` | 标注统计 |

### 📚 引用管理 (Citations) - 9个端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/citations/` | 创建引用 |
| GET | `/citations/` | 获取引用列表 |
| GET | `/citations/{citation_id}` | 获取引用详情 |
| PUT | `/citations/{citation_id}` | 更新引用 |
| DELETE | `/citations/{citation_id}` | 删除引用 |
| POST | `/citations/search` | 搜索引用 |
| POST | `/citations/import-bibtex` | 导入BibTeX |
| POST | `/citations/format` | 格式化引用 |
| POST | `/citations/export` | 导出引用 |

### 🦙 Ollama集成 (Ollama) - 6个端点

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/ollama/status` | 获取Ollama状态 |
| GET | `/ollama/models` | 获取模型列表 |
| GET | `/ollama/models/{model_name}` | 获取模型详情 |
| POST | `/ollama/pull` | 拉取模型 |
| DELETE | `/ollama/models/{model_name}` | 删除模型 |
| GET | `/ollama/recommended-models` | 推荐模型列表 |

### 📤 导出功能 (Export) - 4个端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/export/space` | 导出空间 |
| POST | `/export/conversations` | 导出对话 |
| POST | `/export/documents` | 导出文档 |
| POST | `/export/notes` | 导出笔记 |

### 🏥 系统端点 - 2个端点

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/` | API根路径 |
| GET | `/health` | 健康检查 |

## 请求示例

### 认证登录
```bash
# FormData方式
curl -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=demo_user" \
  -F "password=Demo123456!"

# JSON方式
curl -X POST http://localhost:8000/api/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"username": "demo_user", "password": "Demo123456!"}'
```

### AI对话（流式响应）
```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "model": "openrouter/auto",
    "stream": true
  }'
```

### Deep Research
```bash
curl -X POST http://localhost:8000/api/v1/agents/deep-research \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "人工智能的最新进展",
    "mode": "general",
    "space_id": null
  }'
```

### 文档上传
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer {token}" \
  -F "file=@document.pdf" \
  -F "space_id=1"
```

## 响应格式

### 成功响应
```json
{
  "id": 1,
  "created_at": "2025-01-19T10:00:00",
  "data": "..."
}
```

### 错误响应
```json
{
  "detail": "错误描述"
}
```

### 分页响应
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "has_next": true
}
```

## 支持的AI模型

通过OpenRouter统一接入，支持：
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3)
- Google (Gemini)
- DeepSeek
- Meta (Llama)
- 以及其他100+模型

## 文件格式支持

- **文档**: PDF, DOCX, PPTX, XLSX, TXT, MD
- **图片**: JPG, PNG, GIF, BMP, WEBP
- **代码**: PY, JS, TS, JAVA, CPP, GO等
- **其他**: JSON, XML, CSV, HTML

## 速率限制

- 认证端点：5次/分钟
- AI端点：30次/分钟
- 上传端点：10次/分钟
- 其他端点：60次/分钟

## WebSocket支持

聊天完成端点支持Server-Sent Events (SSE)用于流式响应：
```
GET /api/v1/chat/completions?stream=true
```

## 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

响应：
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "ok",
    "redis": "ok",
    "minio": "ok",
    "qdrant": "ok"
  }
}
```