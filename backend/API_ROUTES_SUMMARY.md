# Second Brain Backend API Routes Summary

本文档列出了Second Brain后端所有的API端点，用于健康检查和接口测试。

## 基础路由 (main.py)

- `GET /` - 根路由，返回欢迎信息和API版本
- `GET /health` - 健康检查端点
- `GET /metrics` - Prometheus指标端点（已注释）

## API v1 路由前缀: `/api/v1`

### 认证路由 (auth.py) - `/api/v1/auth`

- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录（Form格式）
- `POST /api/v1/auth/login/json` - 用户登录（JSON格式）
- `POST /api/v1/auth/refresh` - 刷新访问令牌
- `POST /api/v1/auth/logout` - 用户登出
- `POST /api/v1/auth/change-password` - 修改密码
- `POST /api/v1/auth/reset-password` - 重置密码请求
- `POST /api/v1/auth/reset-password/confirm` - 确认重置密码

### 用户路由 (users.py) - `/api/v1/users`

- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新当前用户信息
- `POST /api/v1/users/me/change-password` - 修改密码
- `GET /api/v1/users/me/stats` - 获取用户统计信息
- `DELETE /api/v1/users/me` - 删除账户

### 聊天路由 (chat.py) - `/api/v1/chat`

#### 模型管理
- `GET /api/v1/chat/models` - 获取可用的AI模型列表

#### OpenAI兼容接口
- `POST /api/v1/chat/completions` - 创建聊天完成（兼容OpenAI API）

#### 对话管理
- `POST /api/v1/chat/conversations` - 创建新对话
- `GET /api/v1/chat/conversations` - 获取对话列表
- `GET /api/v1/chat/conversations/{conversation_id}` - 获取对话详情及消息
- `PUT /api/v1/chat/conversations/{conversation_id}` - 更新对话信息
- `DELETE /api/v1/chat/conversations/{conversation_id}` - 删除对话

#### 消息管理
- `POST /api/v1/chat/conversations/{conversation_id}/messages` - 发送消息（支持文本和多模态）
- `POST /api/v1/chat/analyze-attachments` - 分析附件
- `POST /api/v1/chat/conversations/{conversation_id}/messages/{message_id}/regenerate` - 重新生成消息

#### 分支管理
- `POST /api/v1/chat/conversations/{conversation_id}/branches` - 创建新分支
- `GET /api/v1/chat/conversations/{conversation_id}/branches` - 列出对话的所有分支
- `POST /api/v1/chat/conversations/{conversation_id}/branches/switch` - 切换到指定分支
- `GET /api/v1/chat/conversations/{conversation_id}/branches/history` - 获取分支历史树
- `POST /api/v1/chat/conversations/{conversation_id}/branches/merge` - 合并分支
- `DELETE /api/v1/chat/conversations/{conversation_id}/branches/{branch_name}` - 删除分支

### 代理路由 (agents.py) - `/api/v1/agents`

- `GET /api/v1/agents/` - 获取AI代理列表
- `GET /api/v1/agents/{agent_id}` - 获取AI代理详情
- `POST /api/v1/agents/{agent_id}/execute` - 执行AI代理
- `POST /api/v1/agents/` - 创建自定义AI代理（高级用户功能）
- `POST /api/v1/agents/deep-research` - 创建Deep Research任务

### 空间路由 (spaces.py) - `/api/v1/spaces`

- `POST /api/v1/spaces/` - 创建新的知识空间
- `GET /api/v1/spaces/` - 获取知识空间列表
- `GET /api/v1/spaces/{space_id}` - 获取知识空间详情
- `PUT /api/v1/spaces/{space_id}` - 更新知识空间信息
- `DELETE /api/v1/spaces/{space_id}` - 删除知识空间

### 文档路由 (documents.py) - `/api/v1/documents`

#### 文档管理
- `POST /api/v1/documents/upload` - 上传文档
- `GET /api/v1/documents/` - 获取文档列表
- `GET /api/v1/documents/{document_id}` - 获取文档详情
- `PUT /api/v1/documents/{document_id}` - 更新文档信息
- `DELETE /api/v1/documents/{document_id}` - 删除文档
- `POST /api/v1/documents/{document_id}/download` - 下载文档文件

#### 文档预览和内容
- `GET /api/v1/documents/{document_id}/preview` - 获取文档预览
- `GET /api/v1/documents/{document_id}/content` - 获取文档文本内容（支持分页）

#### URL导入
- `POST /api/v1/documents/import-url` - 从URL导入网页内容
- `POST /api/v1/documents/batch-import-urls` - 批量从URL导入
- `GET /api/v1/documents/{document_id}/snapshot` - 获取网页文档的快照
- `POST /api/v1/documents/analyze-url` - 分析URL内容

#### 搜索
- `POST /api/v1/documents/search` - 搜索文档

### 笔记路由 (notes.py) - `/api/v1/notes`

#### 笔记管理
- `GET /api/v1/notes/` - 获取笔记列表
- `GET /api/v1/notes/recent` - 获取最近的笔记
- `POST /api/v1/notes/search` - 搜索笔记
- `GET /api/v1/notes/{note_id}` - 获取笔记详情
- `POST /api/v1/notes/` - 创建笔记
- `PUT /api/v1/notes/{note_id}` - 更新笔记
- `DELETE /api/v1/notes/{note_id}` - 删除笔记

#### AI功能
- `POST /api/v1/notes/ai/generate` - 使用AI生成笔记
- `POST /api/v1/notes/ai/summary` - 创建AI文档总结

#### 标签和关联
- `GET /api/v1/notes/{note_id}/linked` - 获取关联的笔记
- `POST /api/v1/notes/{note_id}/tags` - 添加标签
- `DELETE /api/v1/notes/{note_id}/tags` - 移除标签
- `GET /api/v1/notes/tags/all` - 获取所有标签及使用次数

#### 批量操作
- `POST /api/v1/notes/batch` - 批量操作笔记

#### 版本管理
- `GET /api/v1/notes/{note_id}/versions` - 获取笔记的版本历史
- `GET /api/v1/notes/{note_id}/versions/{version_number}` - 获取特定版本
- `POST /api/v1/notes/{note_id}/versions/restore` - 恢复到指定版本
- `POST /api/v1/notes/{note_id}/versions/compare` - 比较两个版本
- `DELETE /api/v1/notes/{note_id}/versions/cleanup` - 清理旧版本

### 标注路由 (annotations.py) - `/api/v1/annotations`

#### 标注管理
- `GET /api/v1/annotations/document/{document_id}` - 获取文档的标注列表
- `GET /api/v1/annotations/document/{document_id}/pages` - 获取指定页码范围的标注
- `GET /api/v1/annotations/document/{document_id}/pdf/{page_number}` - 获取PDF指定页的标注
- `GET /api/v1/annotations/my` - 获取我的所有标注
- `GET /api/v1/annotations/statistics` - 获取标注统计信息
- `GET /api/v1/annotations/{annotation_id}` - 获取标注详情
- `POST /api/v1/annotations/` - 创建标注
- `PUT /api/v1/annotations/{annotation_id}` - 更新标注
- `DELETE /api/v1/annotations/{annotation_id}` - 删除标注

#### 批量操作
- `POST /api/v1/annotations/batch` - 批量创建标注
- `POST /api/v1/annotations/pdf/batch` - 批量创建PDF标注
- `POST /api/v1/annotations/export` - 导出标注
- `POST /api/v1/annotations/copy` - 复制标注到另一个文档

### 引用路由 (citations.py) - `/api/v1/citations`

- `POST /api/v1/citations/import-bibtex` - 导入BibTeX格式的引用
- `GET /api/v1/citations/` - 获取引用列表
- `GET /api/v1/citations/{citation_id}` - 获取引用详情
- `POST /api/v1/citations/` - 创建新引用
- `PUT /api/v1/citations/{citation_id}` - 更新引用信息
- `DELETE /api/v1/citations/{citation_id}` - 删除引用
- `POST /api/v1/citations/search` - 搜索引用
- `POST /api/v1/citations/export` - 导出引用
- `POST /api/v1/citations/format` - 格式化引用（APA、MLA等）

### 导出路由 (export.py) - `/api/v1/export`

- `POST /api/v1/export/notes` - 导出笔记（PDF/DOCX）
- `POST /api/v1/export/documents` - 导出文档（PDF）
- `POST /api/v1/export/space` - 导出空间（PDF）
- `POST /api/v1/export/conversations` - 导出对话（JSON/Markdown）

### Ollama路由 (ollama.py) - `/api/v1/ollama`

- `GET /api/v1/ollama/models` - 列出所有可用的Ollama模型
- `GET /api/v1/ollama/models/{model_name}` - 获取特定模型的详细信息
- `POST /api/v1/ollama/pull` - 拉取新的Ollama模型（管理员）
- `DELETE /api/v1/ollama/models/{model_name}` - 删除Ollama模型（管理员）
- `GET /api/v1/ollama/status` - 获取Ollama服务状态
- `GET /api/v1/ollama/recommended-models` - 获取推荐的模型列表

### 健康检查路由 (health.py) - `/api/v1/health`

- `GET /api/v1/health` - 健康检查端点

## 认证要求

除了以下端点外，所有API端点都需要认证（Bearer Token）：
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/login/json`
- `GET /`
- `GET /health`
- `GET /api/v1/health`

## 权限控制

- 大多数端点只允许用户访问自己的资源
- 空间协作功能允许用户访问被授权的其他用户空间
- 公开空间允许所有认证用户只读访问
- 管理员功能（如Ollama模型管理）需要特殊权限

## 分页参数

大多数列表端点支持以下分页参数：
- `skip`: 跳过的记录数（默认0）
- `limit`: 返回的记录数（默认20，最大100）

## 响应格式

- 成功响应：返回相应的数据模型
- 错误响应：返回包含 `detail` 字段的错误信息
- 列表响应通常包含：`items/data`, `total`, `page`, `page_size`, `has_next`

## 流式响应

以下端点支持流式响应：
- `POST /api/v1/chat/completions` (当 stream=true)
- `POST /api/v1/agents/{agent_id}/execute` (当 stream=true)
- `POST /api/v1/agents/deep-research` (当 stream=true)