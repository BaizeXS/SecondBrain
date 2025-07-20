# Second Brain API 文档

## 概述

Second Brain 后端API基于FastAPI构建，提供RESTful接口支持知识管理、AI对话和文档处理功能。

- **基础URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT Bearer Token
- **API文档**: `http://localhost:8000/api/v1/docs` (Swagger UI)

## 认证

### 获取认证令牌
```bash
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=demo_user&password=Demo123456!
```

### 使用令牌
```bash
Authorization: Bearer <your-token>
```

## 核心API端点

### 1. 认证管理 (Auth)
- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- `POST /auth/refresh` - 刷新令牌
- `POST /auth/logout` - 退出登录
- `POST /auth/change-password` - 修改密码
- `POST /auth/forgot-password` - 忘记密码
- `POST /auth/reset-password` - 重置密码
- `POST /auth/verify-email/{token}` - 验证邮箱

### 2. 用户管理 (Users)
- `GET /users/me` - 获取当前用户信息 *
- `PUT /users/me` - 更新用户信息 *
- `DELETE /users/me` - 删除账号 *
- `GET /users/{user_id}` - 获取指定用户信息 * (管理员)
- `GET /users` - 获取用户列表 * (管理员)

### 3. 知识空间 (Spaces)
- `POST /spaces` - 创建空间 *
- `GET /spaces` - 获取空间列表 *
- `GET /spaces/{space_id}` - 获取空间详情 *
- `PUT /spaces/{space_id}` - 更新空间信息 *
- `DELETE /spaces/{space_id}` - 删除空间 *

### 4. 文档管理 (Documents)
- `POST /documents/upload` - 上传文档 *
- `GET /documents` - 获取文档列表 *
- `GET /documents/{document_id}` - 获取文档详情 *
- `GET /documents/{document_id}/content` - 获取文档内容 *
- `DELETE /documents/{document_id}` - 删除文档 *
- `POST /documents/web-import` - 导入网页内容 *
- `POST /documents/{document_id}/process` - 处理文档 *
- `GET /documents/{document_id}/download` - 下载文档 *

### 5. AI对话 (Chat)
- `POST /chat/messages` - 发送消息 *
- `GET /chat/messages` - 获取消息历史 *
- `GET /chat/conversations` - 获取会话列表 *
- `POST /chat/conversations` - 创建新会话 *
- `DELETE /chat/conversations/{conversation_id}` - 删除会话 *
- `GET /chat/models` - 获取可用模型列表 *
- `POST /chat/search` - AI搜索 *

### 6. 笔记管理 (Notes)
- `POST /notes` - 创建笔记 *
- `GET /notes` - 获取笔记列表 *
- `GET /notes/{note_id}` - 获取笔记详情 *
- `PUT /notes/{note_id}` - 更新笔记 *
- `DELETE /notes/{note_id}` - 删除笔记 *
- `GET /notes/{note_id}/versions` - 获取笔记版本历史 *

### 7. AI代理 (Agents)
- `POST /agents/deep-research` - 启动深度研究 *
- `GET /agents/tasks` - 获取任务列表 *
- `GET /agents/tasks/{task_id}` - 获取任务状态 *

### 8. 导出功能 (Export)
- `POST /export/markdown` - 导出为Markdown *
- `POST /export/pdf` - 导出为PDF *
- `POST /export/docx` - 导出为Word *

### 9. 其他功能
- `GET /health` - 健康检查
- `GET /annotations` - 获取标注列表 *
- `POST /annotations` - 创建标注 *
- `GET /citations` - 获取引用列表 *
- `POST /citations` - 创建引用 *

注: * 表示需要认证

## 请求格式示例

### 创建空间
```json
POST /spaces
{
  "title": "机器学习研究",
  "description": "深度学习相关论文和笔记",
  "type": "normal"
}
```

### 发送AI消息
```json
POST /chat/messages
{
  "conversation_id": "uuid",
  "content": "请解释什么是深度学习",
  "model": "openrouter/openai/gpt-4",
  "mode": "chat"
}
```

## 响应格式

### 成功响应
```json
{
  "id": "uuid",
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z",
  ...
}
```

### 错误响应
```json
{
  "detail": "错误描述"
}
```

## 状态码
- 200: 成功
- 201: 创建成功
- 401: 未授权
- 403: 禁止访问
- 404: 资源不存在
- 422: 请求参数错误
- 500: 服务器错误