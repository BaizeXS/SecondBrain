# 🚀 SecondBrain 后端API测试完整指南

## 📋 概述

本指南为前端开发人员提供完整的后端API测试方案，包括功能清单、测试方法和实现建议。

## 🔧 测试环境配置

### 服务器信息
- **测试服务器**: http://43.160.192.140:8000
- **API基础路径**: /api/v1
- **完整基础URL**: http://43.160.192.140:8000/api/v1
- **本地开发**: http://localhost:8000/api/v1

### 测试账号
- **用户名**: demo_user
- **密码**: Demo123456!
- **注意**: 密码中的感叹号在URL编码时需要写成 `%21`

### 测试工具选择
1. **Postman** (推荐) - 已有完整测试集合
2. **Thunder Client** (VSCode扩展)
3. **cURL** (命令行)
4. **HTTPie** (命令行)
5. **前端调试工具** (浏览器开发者工具)

## 🎯 核心功能与API对应表

### 1. 用户认证流程

| 前端功能 | 使用的API | 请求方法 | 端点 | 说明 |
|---------|----------|---------|------|------|
| 用户注册 | 创建账号 | POST | `/auth/register` | 包含用户名、邮箱、密码验证 |
| 用户登录 | 获取Token | POST | `/auth/login` | 支持Form-data和JSON两种格式 |
| 保持登录 | 刷新Token | POST | `/auth/refresh` | 使用refresh_token换取新token |
| 退出登录 | 注销会话 | POST | `/auth/logout` | 清除客户端token |
| 忘记密码 | 重置密码 | POST | `/auth/reset-password` | 发送重置邮件 |

### 2. 知识空间管理

| 前端功能 | 使用的API | 请求方法 | 端点 | 说明 |
|---------|----------|---------|------|------|
| 创建项目/空间 | 创建空间 | POST | `/spaces/` | 创建知识管理空间 |
| 项目列表 | 获取空间列表 | GET | `/spaces/` | 支持搜索和分页 |
| 进入项目 | 获取空间详情 | GET | `/spaces/{space_id}` | 获取空间及内容统计 |
| 编辑项目 | 更新空间 | PUT | `/spaces/{space_id}` | 修改名称、描述等 |
| 删除项目 | 删除空间 | DELETE | `/spaces/{space_id}?force=true` | force=true删除所有内容 |

### 3. 笔记功能

| 前端功能 | 使用的API | 请求方法 | 端点 | 说明 |
|---------|----------|---------|------|------|
| 新建笔记 | 创建笔记 | POST | `/notes/` | 需指定space_id |
| 笔记列表 | 获取笔记 | GET | `/notes/?space_id={id}` | 按空间筛选 |
| 最近笔记 | 获取最近笔记 | GET | `/notes/recent` | 默认返回10条 |
| 搜索笔记 | 搜索内容 | POST | `/notes/search` | 全文搜索 |
| 编辑笔记 | 更新笔记 | PUT | `/notes/{note_id}` | 自动保存版本 |
| 删除笔记 | 删除 | DELETE | `/notes/{note_id}` | 软删除 |
| 版本历史 | 获取版本 | GET | `/notes/{note_id}/versions` | 查看历史版本 |
| AI生成 | AI创建笔记 | POST | `/notes/ai/generate` | 根据prompt生成 |

### 4. AI对话功能

| 前端功能 | 使用的API | 请求方法 | 端点 | 说明 |
|---------|----------|---------|------|------|
| 新建对话 | 创建会话 | POST | `/chat/conversations` | 可选择AI模型 |
| 发送消息 | 发送消息 | POST | `/chat/conversations/{id}/messages` | 支持流式响应 |
| 对话历史 | 获取对话 | GET | `/chat/conversations/{id}` | 包含所有消息 |
| 切换模型 | 获取模型列表 | GET | `/chat/models` | 获取可用模型 |
| 重新生成 | 重新生成回复 | POST | `/chat/conversations/{id}/messages/{msg_id}/regenerate` | 重新生成AI回复 |

### 5. 文档管理

| 前端功能 | 使用的API | 请求方法 | 端点 | 说明 |
|---------|----------|---------|------|------|
| 上传文件 | 上传文档 | POST | `/documents/upload` | multipart/form-data |
| 文档列表 | 获取文档 | GET | `/documents/?space_id={id}` | 按空间筛选 |
| 下载文件 | 下载文档 | POST | `/documents/{id}/download` | 返回文件流 |
| 预览文档 | 获取预览 | GET | `/documents/{id}/preview` | 文本预览 |
| 导入网页 | 导入URL | POST | `/documents/import-url` | 抓取网页内容 |
| 搜索文档 | 搜索 | POST | `/documents/search` | 在文档中搜索 |

### 6. 深度研究

| 前端功能 | 使用的API | 请求方法 | 端点 | 说明 |
|---------|----------|---------|------|------|
| 发起研究 | 深度研究 | POST | `/agents/deep-research` | 自动收集分析信息 |
| 研究模式 | 选择模式 | - | - | general或academic |

### 7. 导出功能

| 前端功能 | 使用的API | 请求方法 | 端点 | 说明 |
|---------|----------|---------|------|------|
| 导出笔记 | 导出笔记 | POST | `/export/notes` | 支持PDF/DOCX/Markdown |
| 导出空间 | 导出空间 | POST | `/export/space` | 导出整个项目 |
| 导出对话 | 导出对话 | POST | `/export/conversations` | 导出聊天记录 |

## 🧪 Postman测试步骤

### 1. 导入测试集合
```bash
# 文件位置
backend/tests/postman/SecondBrain_Complete_Collection.json
```

### 2. 配置环境变量
在Postman中创建环境，设置以下变量：
- `base_url`: http://43.160.192.140:8000/api/v1
- `access_token`: (登录后自动填充)
- `refresh_token`: (登录后自动填充)
- `space_id`: (创建空间后填充)
- `note_id`: (创建笔记后填充)

### 3. 测试流程

#### 基础认证流程
```
1. Health Check (GET /health) - 确认服务正常
2. Login (POST /auth/login) - 获取访问令牌
3. Get Current User (GET /users/me) - 验证认证成功
```

#### 完整功能测试流程
```
1. 登录获取Token
2. 创建知识空间
3. 在空间中创建笔记
4. 上传文档到空间
5. 创建AI对话
6. 发送消息进行对话
7. 执行深度研究
8. 导出内容
```

## 📝 API调用示例

### 1. 用户登录
```javascript
// 使用fetch API
const login = async () => {
  const formData = new FormData();
  formData.append('username', 'demo_user');
  formData.append('password', 'Demo123456!');
  
  const response = await fetch('http://43.160.192.140:8000/api/v1/auth/login', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  // 保存 access_token 和 refresh_token
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
};
```

### 2. 创建笔记
```javascript
const createNote = async () => {
  const response = await fetch('http://43.160.192.140:8000/api/v1/notes/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      title: "我的笔记",
      content: "笔记内容...",
      space_id: 1,
      tags: ["学习", "技术"]
    })
  });
  
  const note = await response.json();
  return note;
};
```

### 3. AI对话
```javascript
const sendMessage = async (conversationId, message) => {
  const response = await fetch(
    `http://43.160.192.140:8000/api/v1/chat/conversations/${conversationId}/messages`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content: message
      })
    }
  );
  
  const reply = await response.json();
  return reply;
};
```

## 🐛 已知问题和解决方案

### 1. 文档下载问题
- **问题**: 二进制文件（PDF等）下载可能失败
- **解决**: 使用文档ID 4进行测试，或上传文本文件

### 2. URL导入功能
- **问题**: URL导入功能可能存在bug
- **解决**: 暂时使用文件上传替代

### 3. 笔记搜索
- **问题**: content_types参数使用["markdown"]而非["manual"]
- **解决**: 搜索时使用正确的content_type值

### 4. Token过期
- **问题**: Access token 30分钟过期
- **解决**: 使用refresh_token自动刷新

## 📊 性能测试建议

### 响应时间期望值
- 认证API: < 200ms
- CRUD操作: < 500ms
- 搜索功能: < 1s
- AI对话: < 5s (首次响应)
- 深度研究: < 30s
- 文件上传: 取决于文件大小

### 并发测试
- 同时创建多个笔记
- 并发搜索请求
- 多用户同时访问

## 🔒 安全注意事项

1. **Token管理**
   - 使用HTTPS传输
   - Token存储在httpOnly cookie或secure storage
   - 实现自动刷新机制

2. **文件上传**
   - 限制文件大小（建议<50MB）
   - 验证文件类型
   - 扫描恶意内容

3. **API调用**
   - 实现请求限流
   - 添加CORS配置
   - 输入验证和消毒

## 📱 前端集成建议

### 1. API客户端封装
```javascript
class SecondBrainAPI {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }
  
  async request(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    const defaultHeaders = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers
      }
    });
    
    if (response.status === 401) {
      // 自动刷新token
      await this.refreshToken();
      // 重试请求
    }
    
    return response.json();
  }
}
```

### 2. 错误处理
- 统一的错误提示
- 网络错误重试机制
- 友好的用户反馈

### 3. 状态管理
- 缓存常用数据（空间列表、最近笔记）
- 实时同步状态
- 离线功能支持

## 📞 获取帮助

如有问题，请参考：
- API文档：`backend/docs/API_DOCUMENTATION.md`
- Postman测试指南：`backend/tests/postman/POSTMAN_TEST_GUIDE.md`
- 后端README：`backend/README.md`

祝测试顺利！ 🎉