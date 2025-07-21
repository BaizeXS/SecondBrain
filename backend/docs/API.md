# SecondBrain 后端 API 完整文档

**生成时间**: 2025-07-21 23:00:00  
**API版本**: v1  
**基础路径**: `/api/v1`  
**认证方式**: JWT Bearer Token  
**总端点数**: 104个

---

## 📑 目录

- [认证模块](#认证模块)
- [用户管理模块](#用户管理模块)
- [聊天模块](#聊天模块)
- [AI代理模块](#ai代理模块)
- [空间管理模块](#空间管理模块)
- [文档管理模块](#文档管理模块)
- [笔记管理模块](#笔记管理模块)
- [标注管理模块](#标注管理模块)
- [引用管理模块](#引用管理模块)
- [导出模块](#导出模块)
- [Ollama模型管理模块](#ollama模型管理模块)
- [健康检查模块](#健康检查模块)

---

## 1. 认证模块

**路径前缀**: `/auth`  
**文件**: `app/api/v1/endpoints/auth.py`

| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/auth/register` | 用户注册，包含密码强度验证 | ❌ |
| POST | `/auth/login` | 表单数据格式登录，返回JWT令牌 | ❌ |
| POST | `/auth/login/json` | JSON格式登录 | ❌ |
| POST | `/auth/refresh` | 使用refresh token获取新access token | ❌ |
| POST | `/auth/logout` | 用户登出（客户端删除令牌） | ❌ |
| POST | `/auth/change-password` | 修改当前用户密码 | ✅ |
| POST | `/auth/reset-password` | 发送密码重置邮件 | ❌ |
| POST | `/auth/reset-password/confirm` | 使用重置令牌设置新密码 | ❌ |

**特性**:
- 密码强度验证（8位+大小写+数字）
- JWT访问令牌和刷新令牌机制
- 登录日志记录
- 密码重置功能

---

## 2. 用户管理模块

**路径前缀**: `/users`  
**文件**: `app/api/v1/endpoints/users.py`

| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| GET | `/users/me` | 获取当前登录用户的详细信息 | ✅ |
| PUT | `/users/me` | 更新当前用户的个人信息 | ✅ |
| POST | `/users/me/change-password` | 修改当前用户密码 | ✅ |
| GET | `/users/me/stats` | 获取用户的使用统计信息 | ✅ |
| DELETE | `/users/me` | 删除当前用户账户（需密码确认） | ✅ |

**特性**:
- 用户统计信息（空间、文档、对话、笔记数量等）
- 使用限制和存储统计
- 账户删除功能

---

## 3. 聊天模块

**路径前缀**: `/chat`  
**文件**: `app/api/v1/endpoints/chat.py`

### 3.1 模型管理
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| GET | `/chat/models` | 获取所有可用的AI模型列表 | ✅ |

### 3.2 OpenAI兼容接口
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/chat/completions` | OpenAI兼容的聊天完成接口，支持流式响应 | ✅ |

### 3.3 对话管理
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/chat/conversations` | 创建新的对话会话 | ✅ |
| GET | `/chat/conversations` | 获取用户的对话列表，支持筛选 | ✅ |
| GET | `/chat/conversations/{conversation_id}` | 获取对话详情及消息历史 | ✅ |
| PUT | `/chat/conversations/{conversation_id}` | 更新对话信息 | ✅ |
| DELETE | `/chat/conversations/{conversation_id}` | 删除对话 | ✅ |

### 3.4 消息管理
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/chat/conversations/{conversation_id}/messages` | 统一消息发送接口，支持文本和多模态 | ✅ |
| POST | `/chat/conversations/{conversation_id}/messages/{message_id}/regenerate` | 重新生成指定消息 | ✅ |

### 3.5 附件分析
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/chat/analyze-attachments` | 分析上传附件，判断是否需要视觉模型 | ✅ |

### 3.6 分支管理
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/chat/conversations/{conversation_id}/branches` | 在对话中创建新分支 | ✅ |
| GET | `/chat/conversations/{conversation_id}/branches` | 获取对话的所有分支 | ✅ |
| POST | `/chat/conversations/{conversation_id}/branches/switch` | 切换到指定分支 | ✅ |
| GET | `/chat/conversations/{conversation_id}/branches/history` | 获取分支历史树 | ✅ |
| POST | `/chat/conversations/{conversation_id}/branches/merge` | 合并分支 | ✅ |
| DELETE | `/chat/conversations/{conversation_id}/branches/{branch_name}` | 删除指定分支 | ✅ |

**特性**:
- 多模态消息支持（文本+文件）
- 流式响应支持
- 完整的分支管理系统
- OpenRouter、Perplexity、Ollama等多提供商支持
- 文档上下文集成

---

## 4. AI代理模块

**路径前缀**: `/agents`  
**文件**: `app/api/v1/endpoints/agents.py`

| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| GET | `/agents/` | 获取可用的AI代理列表 | ✅ |
| GET | `/agents/{agent_id}` | 获取特定代理的详细信息 | ✅ |
| POST | `/agents/{agent_id}/execute` | 执行AI代理任务 | ✅ |
| POST | `/agents/` | 创建自定义AI代理（高级用户） | ✅ |
| POST | `/agents/deep-research` | 专用的深度研究代理端点 | ✅ |

**预定义代理**:
- **Deep Research**: 基于Perplexity的深度研究代理
- **写作助手**: 文本创作和优化
- **分析专家**: 数据分析和可视化

**特性**:
- 流式响应支持
- 自定义代理创建（高级用户）
- 深度研究功能

---

## 5. 空间管理模块

**路径前缀**: `/spaces`  
**文件**: `app/api/v1/endpoints/spaces.py`

| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/spaces/` | 创建新的知识空间 | ✅ |
| GET | `/spaces/` | 获取用户的空间列表，支持筛选 | ✅ |
| GET | `/spaces/{space_id}` | 获取空间的详细信息 | ✅ |
| PUT | `/spaces/{space_id}` | 更新空间信息 | ✅ |
| DELETE | `/spaces/{space_id}` | 删除空间（支持强制删除） | ✅ |

**特性**:
- 空间数量限制（免费5个，高级10个）
- 支持公开/私有空间
- 协作权限管理
- 标签和搜索支持

---

## 6. 文档管理模块

**路径前缀**: `/documents`  
**文件**: `app/api/v1/endpoints/documents.py`

### 6.1 文档CRUD操作
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/documents/upload` | 上传文档到知识空间 | ✅ |
| GET | `/documents/` | 获取文档列表，支持筛选 | ✅ |
| GET | `/documents/{document_id}` | 获取文档的详细信息 | ✅ |
| PUT | `/documents/{document_id}` | 更新文档信息 | ✅ |
| DELETE | `/documents/{document_id}` | 删除文档 | ✅ |

### 6.2 文档内容访问
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/documents/{document_id}/download` | 下载文档原始文件 | ✅ |
| GET | `/documents/{document_id}/preview` | 获取文档预览内容 | ✅ |
| GET | `/documents/{document_id}/content` | 获取文档文本内容（分页） | ✅ |

### 6.3 网页导入功能
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/documents/import-url` | 从URL导入网页内容 | ✅ |
| POST | `/documents/batch-import-urls` | 批量从URL导入 | ✅ |
| GET | `/documents/{document_id}/snapshot` | 获取网页文档的快照 | ✅ |
| POST | `/documents/analyze-url` | 分析URL内容（不保存） | ✅ |

### 6.4 文档搜索
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/documents/search` | 搜索文档内容 | ✅ |

**特性**:
- 多种文件格式支持（PDF、图片、文本等）
- 文件大小限制和类型验证
- 网页内容抓取和快照保存
- 全文搜索功能
- PDF预览和分页支持

---

## 7. 笔记管理模块

**路径前缀**: `/notes`  
**文件**: `app/api/v1/endpoints/notes.py`

### 7.1 笔记CRUD操作
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| GET | `/notes/` | 获取笔记列表，支持筛选和排序 | ✅ |
| GET | `/notes/recent` | 获取最近创建/修改的笔记 | ✅ |
| POST | `/notes/search` | 搜索笔记内容 | ✅ |
| GET | `/notes/{note_id}` | 获取笔记详细信息 | ✅ |
| POST | `/notes/` | 创建新笔记 | ✅ |
| PUT | `/notes/{note_id}` | 更新笔记内容 | ✅ |
| DELETE | `/notes/{note_id}` | 删除笔记 | ✅ |

### 7.2 AI功能
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/notes/ai/generate` | 使用AI生成笔记内容 | ✅ |
| POST | `/notes/ai/summary` | 创建文档的AI摘要笔记 | ✅ |

### 7.3 笔记关联和标签
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| GET | `/notes/{note_id}/linked` | 获取与笔记相关联的其他笔记 | ✅ |
| POST | `/notes/{note_id}/tags` | 为笔记添加标签 | ✅ |
| DELETE | `/notes/{note_id}/tags` | 从笔记移除标签 | ✅ |
| GET | `/notes/tags/all` | 获取用户的所有标签及使用次数 | ✅ |

### 7.4 批量操作
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/notes/batch` | 批量删除、移动、标签操作 | ✅ |

### 7.5 版本管理
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| GET | `/notes/{note_id}/versions` | 获取笔记的版本历史 | ✅ |
| GET | `/notes/{note_id}/versions/{version_number}` | 获取笔记的特定版本内容 | ✅ |
| POST | `/notes/{note_id}/versions/restore` | 恢复笔记到指定版本 | ✅ |
| POST | `/notes/{note_id}/versions/compare` | 比较两个版本的差异 | ✅ |
| DELETE | `/notes/{note_id}/versions/cleanup` | 清理旧版本，保留最近N个 | ✅ |

**特性**:
- 完整的版本控制系统
- AI辅助生成和摘要功能
- 笔记关联和链接系统
- 丰富的搜索和筛选选项
- 批量操作支持

---

## 8. 标注管理模块

**路径前缀**: `/annotations`  
**文件**: `app/api/v1/endpoints/annotations.py`

### 8.1 标注查询
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| GET | `/annotations/document/{document_id}` | 获取指定文档的标注列表 | ✅ |
| GET | `/annotations/document/{document_id}/pages` | 获取文档指定页码范围的标注 | ✅ |
| GET | `/annotations/document/{document_id}/pdf/{page_number}` | 获取PDF指定页的标注数据 | ✅ |
| GET | `/annotations/my` | 获取当前用户的所有标注 | ✅ |
| GET | `/annotations/{annotation_id}` | 获取标注的详细信息 | ✅ |

### 8.2 标注创建和编辑
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/annotations/` | 创建新的标注 | ✅ |
| POST | `/annotations/batch` | 批量创建标注 | ✅ |
| POST | `/annotations/pdf/batch` | 批量创建PDF标注 | ✅ |
| PUT | `/annotations/{annotation_id}` | 更新标注内容 | ✅ |
| DELETE | `/annotations/{annotation_id}` | 删除标注 | ✅ |

### 8.3 标注统计和导出
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| GET | `/annotations/statistics` | 获取标注的统计信息 | ✅ |
| POST | `/annotations/export` | 导出标注数据 | ✅ |
| POST | `/annotations/copy` | 将标注复制到另一个文档 | ✅ |

**特性**:
- 支持多种标注类型（高亮、笔记、书签等）
- PDF专用标注功能
- 批量创建和管理
- 统计分析功能
- 导出支持（Markdown等格式）

---

## 9. 引用管理模块

**路径前缀**: `/citations`  
**文件**: `app/api/v1/endpoints/citations.py`

### 9.1 引用CRUD操作
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| GET | `/citations/` | 获取引用列表，支持按空间/文档筛选 | ✅ |
| GET | `/citations/{citation_id}` | 获取引用的详细信息 | ✅ |
| POST | `/citations/` | 创建新的引用条目 | ✅ |
| PUT | `/citations/{citation_id}` | 更新引用信息 | ✅ |
| DELETE | `/citations/{citation_id}` | 删除引用 | ✅ |

### 9.2 BibTeX支持
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/citations/import-bibtex` | 导入BibTeX格式的引用 | ✅ |
| POST | `/citations/export` | 导出引用为多种格式 | ✅ |

### 9.3 引用搜索和格式化
| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/citations/search` | 搜索引用条目 | ✅ |
| POST | `/citations/format` | 按指定格式（APA、MLA等）格式化引用 | ✅ |

**特性**:
- 完整的BibTeX支持
- 多种导出格式（BibTeX、JSON、CSV）
- 学术引用格式化（APA、MLA等）
- 按作者、年份、类型搜索

---

## 10. 导出模块

**路径前缀**: `/export`  
**文件**: `app/api/v1/endpoints/export.py`

| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| POST | `/export/notes` | 导出笔记为PDF/DOCX | ✅ |
| POST | `/export/documents` | 导出文档合集 | ✅ |
| POST | `/export/space` | 导出整个空间的内容 | ✅ |
| POST | `/export/conversations` | 导出对话记录 | ✅ |

**支持格式**:
- **笔记**: PDF、DOCX
- **文档**: PDF
- **空间**: PDF
- **对话**: JSON、Markdown

**特性**:
- 支持合并导出和单独导出
- 版本历史包含
- 元数据和标注包含选项
- Unicode文件名支持

---

## 11. Ollama模型管理模块

**路径前缀**: `/ollama`  
**文件**: `app/api/v1/endpoints/ollama.py`

| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| GET | `/ollama/models` | 列出所有可用的Ollama模型 | ✅ |
| GET | `/ollama/models/{model_name}` | 获取特定模型的详细信息 | ✅ |
| POST | `/ollama/pull` | 拉取新的Ollama模型（管理员） | ✅ |
| DELETE | `/ollama/models/{model_name}` | 删除模型（管理员） | ✅ |
| GET | `/ollama/status` | 获取Ollama服务运行状态 | ✅ |
| GET | `/ollama/recommended-models` | 获取推荐的模型列表 | ✅ |

**推荐模型**:
- llama2:7b, mistral:7b, deepseek-coder:6.7b
- nomic-embed-text, qwen:7b, gemma:2b

**特性**:
- 本地模型管理
- 模型状态监控
- 管理员权限控制

---

## 12. 健康检查模块

**路径前缀**: `/health`  
**文件**: `app/api/v1/endpoints/health.py`

| HTTP方法 | 端点路径 | 功能描述 | 需要认证 |
|----------|----------|----------|----------|
| GET | `/health` | 系统健康状态检查 | ❌ |

---

## 📊 API 统计总览

| 统计项 | 数值 |
|--------|------|
| **总端点数** | **104** |
| **模块数量** | 12个 |
| **需要认证的端点** | 96个 |
| **免认证端点** | 8个 |
| **CRUD操作端点** | 45个 |
| **搜索相关端点** | 4个 |
| **导出相关端点** | 4个 |
| **AI功能端点** | 8个 |

---

## 🔒 认证说明

### 免认证端点
- `/health` - 健康检查
- `/auth/*` - 认证相关操作（除change-password外）

### 认证方式
```
Authorization: Bearer <access_token>
```

### 权限等级
- **普通用户**: 基本功能访问
- **高级用户**: 额外功能（自定义代理、更多空间等）
- **管理员**: 系统管理功能（模型管理等）

---

## 📝 通用响应格式

### 成功响应
```json
{
    "data": {...},
    "message": "操作成功",
    "code": 200
}
```

### 错误响应
```json
{
    "detail": "错误描述",
    "code": 400,
    "type": "validation_error"
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

---

## 🚀 主要特性

1. **完整的JWT认证体系**
2. **多模态AI聊天支持**
3. **知识管理系统**（空间、文档、笔记）
4. **版本控制系统**
5. **标注和引用管理**
6. **多格式导出支持**
7. **本地和云端AI模型支持**
8. **分支对话管理**
9. **批量操作支持**
10. **全文搜索功能**

---

## 🏗️ 技术架构特点

- **框架**: 基于FastAPI构建
- **数据库**: 异步PostgreSQL操作
- **架构**: 分层架构（Router → Service → CRUD）
- **响应**: 支持流式响应
- **权限**: 完整的权限控制系统
- **文件**: 多文件格式支持
- **设计**: RESTful API设计

---

**最后更新**: 2025-07-21 23:00:00  
**版本**: v1.0  
**维护者**: SecondBrain开发团队