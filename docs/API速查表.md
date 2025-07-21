# 🚀 SecondBrain API 速查表

## 基础配置
```javascript
const API_BASE = 'http://43.160.192.140:8000/api/v1';
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};
```

## 🔐 认证
```javascript
// 登录
POST /auth/login
FormData: username, password

// 刷新Token  
POST /auth/refresh
Body: { refresh_token }

// 注册
POST /auth/register
Body: { username, email, password, full_name }
```

## 📁 空间管理
```javascript
// 创建空间
POST /spaces/
Body: { name, description, color }

// 获取空间列表
GET /spaces/

// 获取空间详情
GET /spaces/{space_id}

// 更新空间
PUT /spaces/{space_id}

// 删除空间
DELETE /spaces/{space_id}?force=true
```

## 📝 笔记管理
```javascript
// 创建笔记
POST /notes/
Body: { title, content, space_id, tags }

// 获取笔记列表
GET /notes/?space_id={id}

// 搜索笔记
POST /notes/search
Body: { query, space_id?, tags? }

// 获取最近笔记
GET /notes/recent?limit=10

// 更新笔记
PUT /notes/{note_id}

// 删除笔记
DELETE /notes/{note_id}

// AI生成笔记
POST /notes/ai/generate
Body: { prompt, space_id }
```

## 💬 AI对话
```javascript
// 获取模型列表
GET /chat/models

// 创建对话
POST /chat/conversations
Body: { title, space_id?, mode, model? }

// 发送消息
POST /chat/conversations/{id}/messages
Body: { content, attachments? }

// 获取对话历史
GET /chat/conversations/{id}

// 重新生成回复
POST /chat/conversations/{id}/messages/{msg_id}/regenerate
```

## 📄 文档管理
```javascript
// 上传文档
POST /documents/upload
FormData: file, space_id, description

// 获取文档列表
GET /documents/?space_id={id}

// 下载文档
POST /documents/{id}/download

// 搜索文档
POST /documents/search
Body: { query, space_id? }

// 导入网页
POST /documents/import-url
Body: { url, space_id }
```

## 🔬 深度研究
```javascript
// 执行深度研究
POST /agents/deep-research
Body: { query, mode: "general"|"academic", space_id? }
```

## 📤 导出功能
```javascript
// 导出笔记
POST /export/notes
Body: { note_ids, format: "pdf"|"docx"|"markdown" }

// 导出空间
POST /export/space
Body: { space_id, format, include_documents, include_notes }

// 导出对话
POST /export/conversations
Body: { conversation_ids, format }
```

## 🏷️ 标签管理
```javascript
// 获取所有标签
GET /notes/tags/all

// 添加标签
POST /notes/{note_id}/tags
Body: { tags: ["tag1", "tag2"] }
```

## 📌 快速示例

### 完整的创建笔记流程
```javascript
async function createNote(title, content, spaceId) {
  const response = await fetch(`${API_BASE}/notes/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      title,
      content,
      space_id: spaceId,
      tags: ["重要"]
    })
  });
  return await response.json();
}
```

### AI对话流程
```javascript
// 1. 创建对话
const conversation = await createConversation("技术讨论");

// 2. 发送消息
const message = await sendMessage(conversation.id, "解释一下React Hooks");

// 3. 获取回复
console.log(message.content);
```

## ⚡ 常用组合

### 项目初始化
1. `POST /spaces/` - 创建项目空间
2. `POST /notes/` - 创建第一个笔记
3. `POST /chat/conversations` - 创建AI助手

### 内容搜索
1. `POST /notes/search` - 搜索笔记
2. `POST /documents/search` - 搜索文档
3. `GET /notes/tags/all` - 获取标签云

### 知识导出
1. `POST /export/space` - 导出整个项目
2. `POST /export/notes` - 导出选中笔记
3. `POST /export/conversations` - 导出对话记录