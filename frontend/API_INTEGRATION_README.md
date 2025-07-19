# 前后端API集成说明

## 概述

本项目已完成前后端API集成，前端使用React，后端使用FastAPI。所有API调用都通过统一的API服务层进行管理。

## 配置

### 1. API基础URL配置

API基础URL在 `src/config/api.js` 中配置：

```javascript
// 开发环境
development: {
  BASE_URL: 'http://localhost:8000/api/v1',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
},
```

### 2. 环境变量

可以通过环境变量覆盖默认配置：

```bash
# .env 文件
REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
```

## API服务结构

### 主要API模块

1. **认证API** (`authAPI`)
   - 用户注册、登录、登出
   - Token刷新、密码修改、重置

2. **用户API** (`userAPI`)
   - 获取用户信息、更新用户资料

3. **空间API** (`spaceAPI`)
   - 创建、获取、更新、删除知识空间

4. **文档API** (`documentAPI`)
   - 文档上传、下载、预览、搜索
   - URL导入、批量导入

5. **聊天API** (`chatAPI`)
   - 对话管理、消息发送
   - 分支管理、消息重新生成

6. **笔记API** (`noteAPI`)
   - 笔记创建、更新、删除

7. **代理API** (`agentAPI`)
   - AI代理管理

8. **标注API** (`annotationAPI`)
   - 文档标注功能

9. **引用API** (`citationAPI`)
   - 引用管理

10. **导出API** (`exportAPI`)
    - 对话和空间导出

11. **Ollama API** (`ollamaAPI`)
    - 本地模型管理

## 使用示例

### 认证

```javascript
import { authAPI } from '../services/apiService';

// 登录
const loginResult = await authAPI.login({
  username: 'user@example.com',
  password: 'password123'
});

// 注册
const registerResult = await authAPI.register({
  username: 'newuser',
  email: 'newuser@example.com',
  password: 'password123',
  full_name: 'New User'
});
```

### 空间管理

```javascript
import { spaceAPI } from '../services/apiService';

// 获取空间列表
const spaces = await spaceAPI.getSpaces({
  limit: 20,
  search: '关键词'
});

// 创建空间
const newSpace = await spaceAPI.createSpace({
  name: '我的知识空间',
  description: '用于存储重要文档',
  is_public: false,
  tags: ['工作', '学习']
});
```

### 文档管理

```javascript
import { documentAPI } from '../services/apiService';

// 上传文档
const formData = new FormData();
formData.append('file', fileObject);
formData.append('space_id', spaceId);
formData.append('title', '文档标题');

const document = await documentAPI.uploadDocument(spaceId, fileObject, '文档标题');

// 获取文档列表
const documents = await documentAPI.getDocuments({
  space_id: spaceId,
  search: '关键词'
});
```

### 聊天功能

```javascript
import { chatAPI } from '../services/apiService';

// 创建对话
const conversation = await chatAPI.createConversation({
  title: '新对话',
  space_id: spaceId
});

// 发送消息
const message = await chatAPI.sendMessage(
  conversationId,
  { content: '你好，请帮我分析这个文档' },
  [fileObject] // 可选的文件附件
);
```

## 上下文管理

### AuthContext

管理用户认证状态：

```javascript
import { useAuth } from '../contexts/AuthContext';

const { isAuthenticated, user, login, logout } = useAuth();
```

### ProjectContext

管理知识空间（项目）：

```javascript
import { useProjects } from '../contexts/ProjectContext';

const { 
  projects, 
  addProject, 
  deleteProject, 
  loadProjectDocuments 
} = useProjects();
```

### ChatContext

管理聊天功能：

```javascript
import { useChat } from '../contexts/ChatContext';

const { 
  currentConversation, 
  sendMessage, 
  createConversation 
} = useChat();
```

## 错误处理

所有API调用都包含错误处理：

```javascript
try {
  const result = await apiFunction();
  // 处理成功结果
} catch (error) {
  console.error('API调用失败:', error.message);
  // 处理错误
}
```

## 认证流程

1. **登录**: 用户输入凭据，调用登录API
2. **Token存储**: 登录成功后，access_token和refresh_token存储在localStorage
3. **自动认证**: 应用启动时检查token有效性
4. **Token刷新**: 当access_token过期时，自动使用refresh_token刷新
5. **登出**: 清除本地token并调用登出API

## 文件上传

支持多种文件类型上传：

- PDF文档
- Word、Excel、PowerPoint文档
- 文本文件
- 图片文件

文件大小限制：100MB

## 开发注意事项

1. **CORS配置**: 确保后端已正确配置CORS
2. **Token管理**: 所有API请求自动包含Authorization头
3. **错误处理**: 统一的错误处理机制
4. **加载状态**: 提供加载状态管理
5. **缓存策略**: 根据需要实现适当的缓存策略

## 测试

运行前端测试：

```bash
cd frontend
npm test
```

## 部署

### 开发环境

```bash
# 启动后端
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动前端
cd frontend
npm start
```

### 生产环境

确保设置正确的环境变量：

```bash
REACT_APP_API_BASE_URL=https://your-api-domain.com/api/v1
```

## 故障排除

### 常见问题

1. **CORS错误**: 检查后端CORS配置
2. **认证失败**: 检查token是否有效
3. **文件上传失败**: 检查文件大小和类型
4. **API超时**: 检查网络连接和服务器状态

### 调试

启用详细日志：

```javascript
// 在浏览器控制台查看API调用日志
localStorage.setItem('debug', 'true');
```

## 更新日志

- v1.0.0: 初始API集成
- 支持所有主要功能模块
- 完整的认证和授权系统
- 文件上传和管理
- 聊天和对话管理 