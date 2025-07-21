# SecondBrain Backend API 端点完整列表

生成时间: 2025-07-21

## API 端点总览

- **总端点数**: 85 个
- **基础路径**: `/api/v1`

## 端点分类统计

| 模块 | 端点数量 | 说明 |
|------|---------|------|
| 认证 (auth) | 7 | 用户注册、登录、密码管理等 |
| 用户 (users) | 5 | 用户信息管理、统计数据等 |
| 空间 (spaces) | 5 | 知识空间的创建、管理等 |
| 文档 (documents) | 11 | 文档上传、管理、搜索等 |
| 笔记 (notes) | 17 | 笔记创建、版本管理、标签等 |
| 聊天 (chat) | 6 | AI对话、会话管理等 |
| 代理 (agents) | 5 | AI代理创建和执行 |
| 标注 (annotations) | 9 | 文档标注管理 |
| 引用 (citations) | 9 | 文献引用管理 |
| 导出 (export) | 4 | 数据导出功能 |
| Ollama | 6 | Ollama模型管理 |
| 健康检查 (health) | 1 | 系统健康状态 |

## 详细端点列表

### 1. 认证模块 (/api/v1/auth)

| HTTP方法 | 路径 | 功能描述 | 路由装饰器 |
|---------|------|---------|-----------|
| POST | `/auth/register` | 用户注册 | `@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)` |
| POST | `/auth/login` | 用户登录（表单格式） | `@router.post("/login", response_model=Token)` |
| POST | `/auth/login/json` | 用户登录（JSON格式） | `@router.post("/login/json", response_model=Token)` |
| POST | `/auth/refresh` | 刷新访问令牌 | `@router.post("/refresh", response_model=Token)` |
| POST | `/auth/logout` | 用户登出 | `@router.post("/logout")` |
| POST | `/auth/change-password` | 修改密码 | `@router.post("/change-password")` |
| POST | `/auth/reset-password` | 重置密码请求 | `@router.post("/reset-password")` |
| POST | `/auth/reset-password/confirm` | 确认重置密码 | `@router.post("/reset-password/confirm")` |

### 2. 用户模块 (/api/v1/users)

| HTTP方法 | 路径 | 功能描述 | 路由装饰器 |
|---------|------|---------|-----------|
| GET | `/users/me` | 获取当前用户信息 | `@router.get("/me", response_model=UserResponse)` |
| PUT | `/users/me` | 更新当前用户信息 | `@router.put("/me", response_model=UserResponse)` |
| POST | `/users/me/change-password` | 修改密码 | `@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)` |
| GET | `/users/me/stats` | 获取用户统计信息 | `@router.get("/me/stats", response_model=UserStats)` |
| DELETE | `/users/me` | 删除账户（需要密码确认） | `@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)` |

### 3. 空间模块 (/api/v1/spaces)

| HTTP方法 | 路径 | 功能描述 | 路由装饰器 |
|---------|------|---------|-----------|
| POST | `/spaces/` | 创建新的知识空间 | `@router.post("/", response_model=SpaceResponse, status_code=status.HTTP_201_CREATED)` |
| GET | `/spaces/` | 获取用户的知识空间列表 | `@router.get("/", response_model=SpaceListResponse)` |
| GET | `/spaces/{space_id}` | 获取知识空间详情 | `@router.get("/{space_id}", response_model=SpaceDetail)` |
| PUT | `/spaces/{space_id}` | 更新知识空间信息 | `@router.put("/{space_id}", response_model=SpaceResponse)` |
| DELETE | `/spaces/{space_id}` | 删除知识空间 | `@router.delete("/{space_id}", status_code=status.HTTP_204_NO_CONTENT)` |

### 4. 文档模块 (/api/v1/documents)

| HTTP方法 | 路径 | 功能描述 | 路由装饰器 |
|---------|------|---------|-----------|
| POST | `/documents/upload` | 上传文档 | `@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)` |
| GET | `/documents/` | 获取文档列表 | `@router.get("/", response_model=DocumentListResponse)` |
| GET | `/documents/{document_id}` | 获取文档详情 | `@router.get("/{document_id}", response_model=DocumentResponse)` |
| PUT | `/documents/{document_id}` | 更新文档信息 | `@router.put("/{document_id}", response_model=DocumentResponse)` |
| DELETE | `/documents/{document_id}` | 删除文档 | `@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)` |
| POST | `/documents/{document_id}/download` | 下载文档 | `@router.post("/{document_id}/download")` |
| GET | `/documents/{document_id}/preview` | 预览文档 | `@router.get("/{document_id}/preview")` |
| GET | `/documents/{document_id}/content` | 获取文档内容 | `@router.get("/{document_id}/content")` |
| POST | `/documents/import-url` | 从URL导入文档 | `@router.post("/import-url", response_model=URLImportResponse, status_code=status.HTTP_201_CREATED)` |
| POST | `/documents/batch-import-urls` | 批量从URL导入文档 | `@router.post("/batch-import-urls", response_model=list[URLImportResponse])` |
| GET | `/documents/{document_id}/snapshot` | 获取网页快照 | `@router.get("/{document_id}/snapshot", response_model=WebSnapshotResponse)` |
| POST | `/documents/analyze-url` | 分析URL内容（不保存） | `@router.post("/analyze-url", response_model=URLAnalysisResponse)` |
| POST | `/documents/search` | 搜索文档 | `@router.post("/search", response_model=SearchResponse)` |

### 5. 笔记模块 (/api/v1/notes)

| HTTP方法 | 路径 | 功能描述 | 路由装饰器 |
|---------|------|---------|-----------|
| GET | `/notes/` | 获取笔记列表 | `@router.get("/", response_model=NoteListResponse)` |
| GET | `/notes/recent` | 获取最近的笔记 | `@router.get("/recent", response_model=list[NoteResponse])` |
| POST | `/notes/search` | 搜索笔记 | `@router.post("/search", response_model=NoteListResponse)` |
| GET | `/notes/{note_id}` | 获取笔记详情 | `@router.get("/{note_id}", response_model=NoteDetail)` |
| POST | `/notes/` | 创建新笔记 | `@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)` |
| PUT | `/notes/{note_id}` | 更新笔记 | `@router.put("/{note_id}", response_model=NoteResponse)` |
| DELETE | `/notes/{note_id}` | 删除笔记 | `@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)` |
| POST | `/notes/batch` | 批量操作笔记 | `@router.post("/batch", response_model=BatchOperationResponse)` |
| GET | `/notes/{note_id}/linked` | 获取关联笔记 | `@router.get("/{note_id}/linked", response_model=list[NoteResponse])` |
| POST | `/notes/{note_id}/tags` | 添加标签 | `@router.post("/{note_id}/tags", response_model=NoteResponse)` |
| DELETE | `/notes/{note_id}/tags` | 删除标签 | `@router.delete("/{note_id}/tags", response_model=NoteResponse)` |
| GET | `/notes/tags/all` | 获取所有标签 | `@router.get("/tags/all", response_model=TagListResponse)` |
| GET | `/notes/{note_id}/versions` | 获取笔记版本历史 | `@router.get("/{note_id}/versions", response_model=NoteVersionListResponse)` |
| GET | `/notes/{note_id}/versions/{version_number}` | 获取特定版本内容 | `@router.get("/{note_id}/versions/{version_number}", response_model=NoteVersionDetail)` |
| POST | `/notes/{note_id}/versions/restore` | 恢复笔记版本 | `@router.post("/{note_id}/versions/restore", response_model=NoteResponse)` |
| POST | `/notes/{note_id}/versions/compare` | 比较笔记版本 | `@router.post("/{note_id}/versions/compare", response_model=VersionComparisonResponse)` |
| DELETE | `/notes/{note_id}/versions/cleanup` | 清理旧版本 | `@router.delete("/{note_id}/versions/cleanup", status_code=status.HTTP_204_NO_CONTENT)` |

### 6. 聊天模块 (/api/v1/chat)

| HTTP方法 | 路径 | 功能描述 | 路由装饰器 |
|---------|------|---------|-----------|
| POST | `/chat/completions` | 创建聊天会话 | `@router.post("/completions")` |
| GET | `/chat/conversations` | 获取会话列表 | `@router.get("/conversations", response_model=ConversationListResponse)` |
| GET | `/chat/conversations/{conversation_id}` | 获取会话详情 | `@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)` |
| PUT | `/chat/conversations/{conversation_id}` | 更新会话信息 | `@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)` |
| DELETE | `/chat/conversations/{conversation_id}` | 删除会话 | `@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)` |
| GET | `/chat/models` | 获取可用的AI模型列表 | `@router.get("/models", response_model=ModelListResponse)` |
| POST | `/chat/analyze-attachments` | 分析附件，返回是否需要视觉模型等信息 | `@router.post("/analyze-attachments", response_model=AttachmentAnalysisResponse)` |

### 7. 代理模块 (/api/v1/agents)

| HTTP方法 | 路径 | 功能描述 | 路由装饰器 |
|---------|------|---------|-----------|
| GET | `/agents/` | 获取代理列表 | `@router.get("/", response_model=list[AgentResponse])` |
| POST | `/agents/` | 创建新代理 | `@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)` |
| GET | `/agents/{agent_id}` | 获取代理详情 | `@router.get("/{agent_id}", response_model=AgentResponse)` |
| POST | `/agents/{agent_id}/execute` | 执行代理 | `@router.post("/{agent_id}/execute")` |
| POST | `/agents/deep-research` | 创建深度研究任务 | `@router.post("/deep-research")` |

### 8. 标注模块 (/api/v1/annotations)

| HTTP方法 | 路径 | 功能描述 | 路由装饰器 |
|---------|------|---------|-----------|
| GET | `/annotations/my` | 获取我的标注 | `@router.get("/my", response_model=AnnotationListResponse)` |
| GET | `/annotations/document/{document_id}` | 获取文档的标注 | `@router.get("/document/{document_id}", response_model=AnnotationListResponse)` |
| GET | `/annotations/document/{document_id}/pages` | 按页面获取标注 | `@router.get("/document/{document_id}/pages", response_model=dict[int, list[AnnotationResponse]])` |
| GET | `/annotations/{annotation_id}` | 获取标注详情 | `@router.get("/{annotation_id}", response_model=AnnotationResponse)` |
| POST | `/annotations/` | 创建标注 | `@router.post("/", response_model=AnnotationResponse, status_code=status.HTTP_201_CREATED)` |
| PUT | `/annotations/{annotation_id}` | 更新标注 | `@router.put("/{annotation_id}", response_model=AnnotationResponse)` |
| DELETE | `/annotations/{annotation_id}` | 删除标注 | `@router.delete("/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)` |
| POST | `/annotations/copy` | 复制标注 | `@router.post("/copy", response_model=list[AnnotationResponse])` |
| POST | `/annotations/export` | 导出标注 | `@router.post("/export")` |
| GET | `/annotations/statistics` | 获取标注统计 | `@router.get("/statistics", response_model=AnnotationStatistics)` |

### 9. 引用模块 (/api/v1/citations)

| HTTP方法 | 路径 | 功能描述 | 路由装饰器 |
|---------|------|---------|-----------|
| GET | `/citations/` | 获取引用列表 | `@router.get("/", response_model=CitationListResponse)` |
| POST | `/citations/` | 创建引用 | `@router.post("/", response_model=CitationResponse, status_code=status.HTTP_201_CREATED)` |
| GET | `/citations/{citation_id}` | 获取引用详情 | `@router.get("/{citation_id}", response_model=CitationResponse)` |
| PUT | `/citations/{citation_id}` | 更新引用 | `@router.put("/{citation_id}", response_model=CitationResponse)` |
| DELETE | `/citations/{citation_id}` | 删除引用 | `@router.delete("/{citation_id}", status_code=status.HTTP_204_NO_CONTENT)` |
| POST | `/citations/search` | 搜索引用 | `@router.post("/search", response_model=CitationListResponse)` |
| POST | `/citations/import-bibtex` | 导入BibTeX格式引用 | `@router.post("/import-bibtex", response_model=list[CitationResponse])` |
| POST | `/citations/export` | 导出引用 | `@router.post("/export")` |
| POST | `/citations/format` | 格式化引用 | `@router.post("/format", response_model=CitationFormatResponse)` |

### 10. 导出模块 (/api/v1/export)

| HTTP方法 | 路径 | 功能描述 | 路由装饰器 |
|---------|------|---------|-----------|
| POST | `/export/notes` | 导出笔记 | `@router.post("/notes")` |
| POST | `/export/documents` | 导出文档 | `@router.post("/documents")` |
| POST | `/export/conversations` | 导出对话 | `@router.post("/conversations")` |
| POST | `/export/space` | 导出整个空间 | `@router.post("/space")` |

### 11. Ollama模块 (/api/v1/ollama)

| HTTP方法 | 路径 | 功能描述 | 路由装饰器 |
|---------|------|---------|-----------|
| GET | `/ollama/models` | 列出所有可用的Ollama模型 | `@router.get("/models", response_model=OllamaModelListResponse)` |
| GET | `/ollama/models/{model_name}` | 获取特定模型的详细信息 | `@router.get("/models/{model_name}", response_model=OllamaModelInfo)` |
| POST | `/ollama/pull` | 拉取新的Ollama模型 | `@router.post("/pull", response_model=OllamaPullResponse)` |
| DELETE | `/ollama/models/{model_name}` | 删除Ollama模型 | `@router.delete("/models/{model_name}")` |
| GET | `/ollama/status` | 获取Ollama服务状态 | `@router.get("/status")` |
| GET | `/ollama/recommended-models` | 获取推荐的模型列表 | `@router.get("/recommended-models")` |

### 12. 健康检查模块 (/api/v1/health)

| HTTP方法 | 路径 | 功能描述 | 路由装饰器 |
|---------|------|---------|-----------|
| GET | `/health` | 健康检查端点 | `@router.get("")` |

## 认证说明

除了以下公开端点外，其他所有端点都需要认证：
- POST `/auth/register` - 用户注册
- POST `/auth/login` - 用户登录
- POST `/auth/login/json` - JSON格式登录
- POST `/auth/refresh` - 刷新令牌
- POST `/auth/reset-password` - 重置密码请求
- POST `/auth/reset-password/confirm` - 确认重置密码
- GET `/health` - 健康检查

认证方式：
- 使用 Bearer Token 在 Authorization 头中传递
- 格式：`Authorization: Bearer <access_token>`

## 通用响应格式

成功响应：
```json
{
    "data": {...},      // 响应数据
    "message": "...",   // 成功消息（可选）
    "code": 200         // 状态码
}
```

错误响应：
```json
{
    "detail": "错误描述",
    "code": 400,        // HTTP状态码
    "type": "error"     // 错误类型
}
```

## 分页参数

支持分页的端点通常接受以下查询参数：
- `skip`: 跳过的记录数（默认: 0）
- `limit`: 返回的记录数（默认: 20，最大: 100）
- `search`: 搜索关键词（可选）

分页响应格式：
```json
{
    "items": [...],     // 数据列表
    "total": 100,       // 总记录数
    "page": 1,          // 当前页码
    "page_size": 20,    // 每页大小
    "has_next": true    // 是否有下一页
}
```

## 文件上传

文件上传端点使用 `multipart/form-data` 格式：
- 文件字段名：`file`
- 支持的文件类型：PDF, TXT, MD, DOCX, PNG, JPG, JPEG
- 最大文件大小：50MB（可在配置中调整）

## 版本信息

- API版本：v1
- 后端框架：FastAPI
- Python版本：3.11+
- 数据库：PostgreSQL + pgvector

## 备注

1. 所有时间戳使用 ISO 8601 格式
2. 所有 ID 使用整数类型
3. 标签和分类使用字符串数组
4. 中文错误消息用于提升用户体验
5. 支持 WebSocket 用于实时聊天功能（在 `/chat/completions` 端点）