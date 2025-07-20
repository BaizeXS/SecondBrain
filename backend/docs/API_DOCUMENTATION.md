# Second Brain 后端API完整文档

## 基础信息
- **基础URL**: `http://localhost:8000/api/v1`
- **认证方式**: Bearer Token (JWT)
- **Content-Type**: `application/json` (除文件上传外)

## API功能分组

### 1. 认证系统 (Authentication)

#### 1.1 用户注册
- **端点**: `POST /auth/register`
- **功能**: 创建新用户账号
- **请求体**:
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "Test123456!",
  "full_name": "测试用户"
}
```
- **响应**: 201 Created
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "full_name": "测试用户",
  "is_active": true,
  "is_premium": false,
  "created_at": "2025-01-20T10:00:00Z"
}
```

#### 1.2 用户登录
- **端点**: `POST /auth/login`
- **功能**: 获取访问令牌
- **请求**: Form-data
```
username=testuser
password=Test123456!
```
- **响应**: 200 OK
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 1.3 刷新令牌
- **端点**: `POST /auth/refresh`
- **功能**: 使用刷新令牌获取新的访问令牌
- **请求体**:
```json
{
  "refresh_token": "eyJ..."
}
```

#### 1.4 修改密码
- **端点**: `POST /auth/change-password`
- **功能**: 修改当前用户密码
- **需要认证**: ✅
- **请求体**:
```json
{
  "old_password": "Test123456!",
  "new_password": "NewPass123456!"
}
```

#### 1.5 退出登录
- **端点**: `POST /auth/logout`
- **功能**: 注销当前会话
- **需要认证**: ✅

### 2. 用户管理 (User Management)

#### 2.1 获取当前用户信息
- **端点**: `GET /users/me`
- **功能**: 获取当前登录用户的详细信息
- **需要认证**: ✅
- **响应**:
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "full_name": "测试用户",
  "is_active": true,
  "is_premium": false,
  "created_at": "2025-01-20T10:00:00Z"
}
```

#### 2.2 更新用户信息
- **端点**: `PUT /users/me`
- **功能**: 更新当前用户的个人信息
- **需要认证**: ✅
- **请求体**:
```json
{
  "full_name": "新的名字",
  "email": "newemail@example.com"
}
```

#### 2.3 获取用户统计
- **端点**: `GET /users/me/stats`
- **功能**: 获取用户的使用统计信息
- **需要认证**: ✅
- **响应**:
```json
{
  "total_spaces": 5,
  "total_notes": 123,
  "total_documents": 45,
  "total_conversations": 67,
  "storage_used": 1234567890,
  "last_active": "2025-01-20T10:00:00Z"
}
```

### 3. 知识空间管理 (Space Management)

#### 3.1 创建空间
- **端点**: `POST /spaces/`
- **功能**: 创建新的知识空间
- **需要认证**: ✅
- **请求体**:
```json
{
  "name": "我的项目",
  "description": "项目相关的知识整理",
  "color": "#FF5733",
  "icon": "folder",
  "is_public": false,
  "tags": ["项目", "学习"],
  "meta_data": {"category": "work"}
}
```

#### 3.2 获取空间列表
- **端点**: `GET /spaces/`
- **功能**: 获取用户的所有空间
- **需要认证**: ✅
- **查询参数**:
  - `skip`: 跳过条数 (分页)
  - `limit`: 每页数量
  - `search`: 搜索关键词

#### 3.3 获取空间详情
- **端点**: `GET /spaces/{space_id}`
- **功能**: 获取特定空间的详细信息
- **需要认证**: ✅

#### 3.4 更新空间
- **端点**: `PUT /spaces/{space_id}`
- **功能**: 更新空间信息
- **需要认证**: ✅
- **请求体**:
```json
{
  "name": "更新的名称",
  "description": "更新的描述"
}
```

#### 3.5 删除空间
- **端点**: `DELETE /spaces/{space_id}?force=true`
- **功能**: 删除空间（force=true时删除所有内容）
- **需要认证**: ✅

### 4. 笔记管理 (Note Management)

#### 4.1 创建笔记
- **端点**: `POST /notes/`
- **功能**: 在指定空间创建新笔记
- **需要认证**: ✅
- **请求体**:
```json
{
  "title": "学习笔记",
  "content": "# 标题\n\n这是笔记内容...",
  "space_id": 1,
  "note_type": "manual",
  "tags": ["学习", "技术"],
  "meta_data": {"important": true}
}
```

#### 4.2 获取笔记列表
- **端点**: `GET /notes/`
- **功能**: 获取笔记列表
- **需要认证**: ✅
- **查询参数**:
  - `space_id`: 空间ID
  - `skip`: 跳过条数
  - `limit`: 每页数量
  - `tag`: 标签筛选

#### 4.3 获取最近笔记
- **端点**: `GET /notes/recent`
- **功能**: 获取最近更新的笔记
- **需要认证**: ✅
- **查询参数**:
  - `limit`: 数量限制（默认10）

#### 4.4 搜索笔记
- **端点**: `POST /notes/search`
- **功能**: 全文搜索笔记
- **需要认证**: ✅
- **请求体**:
```json
{
  "query": "搜索关键词",
  "space_id": 1,  // 可选
  "tags": ["标签1", "标签2"]  // 可选
}
```

#### 4.5 获取所有标签
- **端点**: `GET /notes/tags/all`
- **功能**: 获取用户所有使用过的标签
- **需要认证**: ✅

#### 4.6 获取笔记详情
- **端点**: `GET /notes/{note_id}`
- **功能**: 获取特定笔记的详细内容
- **需要认证**: ✅

#### 4.7 更新笔记
- **端点**: `PUT /notes/{note_id}`
- **功能**: 更新笔记内容
- **需要认证**: ✅
- **请求体**:
```json
{
  "title": "更新的标题",
  "content": "更新的内容",
  "tags": ["新标签"]
}
```

#### 4.8 删除笔记
- **端点**: `DELETE /notes/{note_id}`
- **功能**: 删除笔记
- **需要认证**: ✅

#### 4.9 获取笔记版本历史
- **端点**: `GET /notes/{note_id}/versions`
- **功能**: 获取笔记的历史版本
- **需要认证**: ✅

### 5. AI对话功能 (Chat & AI)

#### 5.1 创建对话
- **端点**: `POST /chat/conversations`
- **功能**: 创建新的AI对话
- **需要认证**: ✅
- **请求体**:
```json
{
  "title": "技术讨论",
  "space_id": 1,  // 可选，关联到空间
  "mode": "chat",  // chat或research
  "model": "gpt-4o-mini",  // 可选
  "system_prompt": "你是一个技术专家"  // 可选
}
```

#### 5.2 获取对话列表
- **端点**: `GET /chat/conversations`
- **功能**: 获取用户的所有对话
- **需要认证**: ✅
- **查询参数**:
  - `space_id`: 空间ID筛选
  - `mode`: 模式筛选
  - `skip`, `limit`: 分页

#### 5.3 发送消息
- **端点**: `POST /chat/conversations/{conversation_id}/messages`
- **功能**: 向对话发送消息并获取AI回复
- **需要认证**: ✅
- **请求体**:
```json
{
  "content": "请解释一下量子计算"
}
```
- **响应**:
```json
{
  "id": 1,
  "role": "assistant",
  "content": "量子计算是...",
  "model": "gpt-4o-mini",
  "created_at": "2025-01-20T10:00:00Z"
}
```

#### 5.4 获取可用模型
- **端点**: `GET /chat/models`
- **功能**: 获取可用的AI模型列表
- **需要认证**: ✅

### 6. 文档管理 (Document Management)

#### 6.1 上传文档
- **端点**: `POST /documents/upload`
- **功能**: 上传文档文件
- **需要认证**: ✅
- **请求**: multipart/form-data
- **参数**:
  - `file`: 文件
  - `space_id`: 空间ID
  - `description`: 描述

#### 6.2 获取文档列表
- **端点**: `GET /documents/`
- **功能**: 获取文档列表
- **需要认证**: ✅
- **查询参数**:
  - `space_id`: 空间ID
  - `file_type`: 文件类型筛选

#### 6.3 搜索文档
- **端点**: `POST /documents/search`
- **功能**: 搜索文档内容
- **需要认证**: ✅
- **请求体**:
```json
{
  "query": "搜索关键词",
  "space_id": 1  // 可选
}
```

#### 6.4 分析URL
- **端点**: `POST /documents/analyze-url`
- **功能**: 分析网页内容
- **需要认证**: ✅
- **请求体**:
```json
{
  "url": "https://example.com/article"
}
```

### 7. 深度研究功能 (Deep Research)

#### 7.1 执行深度研究
- **端点**: `POST /agents/deep-research`
- **功能**: 执行深度研究任务
- **需要认证**: ✅
- **请求体**:
```json
{
  "query": "量子计算的最新进展",
  "mode": "general",  // general或academic
  "stream": false,  // 是否流式响应
  "space_id": 1  // 可选，保存到空间
}
```

### 8. 引用管理 (Citation Management)

#### 8.1 创建引用
- **端点**: `POST /citations/?space_id={space_id}`
- **功能**: 创建文献引用
- **需要认证**: ✅
- **请求体**:
```json
{
  "title": "论文标题",
  "authors": ["作者1", "作者2"],
  "year": 2024,
  "citation_type": "article",
  "bibtex_key": "author2024title",
  "journal": "期刊名称",
  "doi": "10.1234/example"
}
```

#### 8.2 搜索引用
- **端点**: `POST /citations/search`
- **功能**: 搜索引用
- **需要认证**: ✅

#### 8.3 导出引用
- **端点**: `POST /citations/export`
- **功能**: 导出引用为BibTeX格式
- **需要认证**: ✅
- **请求体**:
```json
{
  "space_id": 1,
  "format": "bibtex"
}
```

### 9. 导出功能 (Export)

#### 9.1 导出空间
- **端点**: `POST /export/space`
- **功能**: 导出整个空间内容
- **需要认证**: ✅
- **请求体**:
```json
{
  "space_id": 1,
  "format": "pdf",  // pdf, docx, markdown
  "include_documents": true,
  "include_notes": true,
  "include_content": true,
  "include_citations": false
}
```

#### 9.2 导出笔记
- **端点**: `POST /export/notes`
- **功能**: 导出选定的笔记
- **需要认证**: ✅
- **请求体**:
```json
{
  "note_ids": [1, 2, 3],
  "format": "pdf",
  "include_metadata": true
}
```

#### 9.3 导出对话
- **端点**: `POST /export/conversations`
- **功能**: 导出AI对话记录
- **需要认证**: ✅
- **请求体**:
```json
{
  "conversation_ids": [1],
  "format": "markdown"
}
```

### 10. Ollama本地模型 (可选功能)

#### 10.1 获取Ollama模型列表
- **端点**: `GET /ollama/models`
- **功能**: 获取本地Ollama模型
- **需要认证**: ✅

#### 10.2 获取Ollama状态
- **端点**: `GET /ollama/status`
- **功能**: 检查Ollama服务状态
- **需要认证**: ✅

## 功能实现场景指南

### 场景1：用户注册并开始使用
1. 调用 `POST /auth/register` 注册账号
2. 调用 `POST /auth/login` 登录获取token
3. 调用 `POST /spaces/` 创建第一个知识空间
4. 调用 `POST /notes/` 创建第一篇笔记

### 场景2：知识管理工作流
1. 调用 `GET /spaces/` 获取空间列表
2. 选择空间后，调用 `POST /notes/` 创建笔记
3. 调用 `POST /documents/upload` 上传相关文档
4. 调用 `POST /notes/search` 搜索内容

### 场景3：AI助手使用
1. 调用 `POST /chat/conversations` 创建对话
2. 调用 `POST /chat/conversations/{id}/messages` 发送消息
3. 获取AI回复后继续对话
4. 调用 `POST /agents/deep-research` 进行深度研究

### 场景4：内容导出
1. 调用 `POST /export/space` 导出整个空间
2. 或调用 `POST /export/notes` 导出特定笔记
3. 下载生成的PDF/DOCX文件

## 错误处理

所有API在出错时会返回标准错误格式：
```json
{
  "detail": "错误描述",
  "status_code": 400,
  "timestamp": 123456.789,
  "path": "/api/v1/endpoint"
}
```

常见错误码：
- 400: 请求参数错误
- 401: 未认证
- 403: 无权限
- 404: 资源不存在
- 422: 参数验证失败
- 500: 服务器内部错误

## 认证说明

除了公开端点（健康检查、注册、登录）外，其他所有端点都需要在请求头中包含：
```
Authorization: Bearer {access_token}
```

Token过期后需要使用refresh_token刷新或重新登录。