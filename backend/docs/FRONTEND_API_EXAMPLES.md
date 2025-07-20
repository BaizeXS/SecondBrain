# 前端API调用示例

## 基础配置

### Axios配置示例
```javascript
import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器 - 添加认证token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// 响应拦截器 - 处理token过期
api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Token过期，尝试刷新
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken
          });
          localStorage.setItem('access_token', data.access_token);
          // 重试原请求
          error.config.headers.Authorization = `Bearer ${data.access_token}`;
          return axios(error.config);
        } catch {
          // 刷新失败，跳转到登录页
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

## 认证相关

### 用户注册
```javascript
async function register(userData) {
  try {
    const response = await api.post('/auth/register', {
      username: userData.username,
      email: userData.email,
      password: userData.password,
      full_name: userData.fullName
    });
    return response.data;
  } catch (error) {
    console.error('注册失败:', error.response?.data?.detail);
    throw error;
  }
}
```

### 用户登录
```javascript
async function login(username, password) {
  try {
    // 注意：登录使用FormData
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    
    const { access_token, refresh_token } = response.data;
    
    // 保存tokens
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    
    return response.data;
  } catch (error) {
    console.error('登录失败:', error.response?.data?.detail);
    throw error;
  }
}
```

### 获取当前用户信息
```javascript
async function getCurrentUser() {
  try {
    const response = await api.get('/users/me');
    return response.data;
  } catch (error) {
    console.error('获取用户信息失败:', error);
    throw error;
  }
}
```

## 空间管理

### 创建空间
```javascript
async function createSpace(spaceData) {
  try {
    const response = await api.post('/spaces/', {
      name: spaceData.name,
      description: spaceData.description,
      color: spaceData.color || '#FF5733',
      icon: spaceData.icon || 'folder',
      is_public: false,
      tags: spaceData.tags || []
    });
    return response.data;
  } catch (error) {
    console.error('创建空间失败:', error);
    throw error;
  }
}
```

### 获取空间列表
```javascript
async function getSpaces(page = 0, pageSize = 10, search = '') {
  try {
    const params = {
      skip: page * pageSize,
      limit: pageSize
    };
    
    if (search) {
      params.search = search;
    }
    
    const response = await api.get('/spaces/', { params });
    return response.data;
  } catch (error) {
    console.error('获取空间列表失败:', error);
    throw error;
  }
}
```

## 笔记管理

### 创建笔记
```javascript
async function createNote(noteData) {
  try {
    const response = await api.post('/notes/', {
      title: noteData.title,
      content: noteData.content,
      space_id: noteData.spaceId,
      note_type: 'manual',
      tags: noteData.tags || [],
      meta_data: noteData.metadata || {}
    });
    return response.data;
  } catch (error) {
    console.error('创建笔记失败:', error);
    throw error;
  }
}
```

### 搜索笔记
```javascript
async function searchNotes(query, spaceId = null, tags = []) {
  try {
    const searchParams = { query };
    
    if (spaceId) {
      searchParams.space_id = spaceId;
    }
    
    if (tags.length > 0) {
      searchParams.tags = tags;
    }
    
    const response = await api.post('/notes/search', searchParams);
    return response.data;
  } catch (error) {
    console.error('搜索笔记失败:', error);
    throw error;
  }
}
```

### 更新笔记
```javascript
async function updateNote(noteId, updates) {
  try {
    const response = await api.put(`/notes/${noteId}`, updates);
    return response.data;
  } catch (error) {
    console.error('更新笔记失败:', error);
    throw error;
  }
}
```

## AI对话功能

### 创建对话
```javascript
async function createConversation(title, spaceId = null) {
  try {
    const data = { title, mode: 'chat' };
    
    if (spaceId) {
      data.space_id = spaceId;
    }
    
    const response = await api.post('/chat/conversations', data);
    return response.data;
  } catch (error) {
    console.error('创建对话失败:', error);
    throw error;
  }
}
```

### 发送消息（支持流式响应）
```javascript
async function sendMessage(conversationId, message) {
  try {
    const response = await api.post(
      `/chat/conversations/${conversationId}/messages`,
      { content: message }
    );
    return response.data;
  } catch (error) {
    console.error('发送消息失败:', error);
    throw error;
  }
}

// 流式响应版本（如果后端支持）
async function sendMessageStream(conversationId, message, onChunk) {
  try {
    const response = await fetch(
      `http://localhost:8000/api/v1/chat/conversations/${conversationId}/messages/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ content: message })
      }
    );
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      onChunk(chunk);
    }
  } catch (error) {
    console.error('流式响应失败:', error);
    throw error;
  }
}
```

## 文件上传

### 上传文档
```javascript
async function uploadDocument(file, spaceId, description = '') {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('space_id', spaceId);
    formData.append('description', description);
    
    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('上传文档失败:', error);
    throw error;
  }
}
```

## 深度研究

### 执行深度研究
```javascript
async function deepResearch(query, mode = 'general') {
  try {
    const response = await api.post('/agents/deep-research', {
      query,
      mode,
      stream: false
    });
    return response.data;
  } catch (error) {
    console.error('深度研究失败:', error);
    throw error;
  }
}
```

## 导出功能

### 导出笔记为PDF
```javascript
async function exportNotes(noteIds, format = 'pdf') {
  try {
    const response = await api.post('/export/notes', 
      {
        note_ids: noteIds,
        format: format,
        include_metadata: true
      },
      {
        responseType: 'blob' // 重要：接收二进制数据
      }
    );
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `notes_export.${format}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    return true;
  } catch (error) {
    console.error('导出失败:', error);
    throw error;
  }
}
```

## React组件示例

### 笔记编辑器组件
```jsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from './api';

function NoteEditor() {
  const { noteId } = useParams();
  const [note, setNote] = useState({ title: '', content: '', tags: [] });
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);

  // 加载笔记
  useEffect(() => {
    if (noteId) {
      loadNote();
    }
  }, [noteId]);

  const loadNote = async () => {
    try {
      const response = await api.get(`/notes/${noteId}`);
      setNote(response.data);
    } catch (error) {
      console.error('加载笔记失败:', error);
    }
  };

  // 自动保存
  useEffect(() => {
    const timer = setTimeout(() => {
      if (note.content && noteId) {
        saveNote();
      }
    }, 2000); // 2秒后自动保存

    return () => clearTimeout(timer);
  }, [note.content]);

  const saveNote = async () => {
    setSaving(true);
    try {
      await api.put(`/notes/${noteId}`, {
        title: note.title,
        content: note.content,
        tags: note.tags
      });
      setLastSaved(new Date());
    } catch (error) {
      console.error('保存失败:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="note-editor">
      <input
        type="text"
        value={note.title}
        onChange={(e) => setNote({ ...note, title: e.target.value })}
        placeholder="笔记标题"
      />
      
      <textarea
        value={note.content}
        onChange={(e) => setNote({ ...note, content: e.target.value })}
        placeholder="开始写作..."
      />
      
      <div className="status-bar">
        {saving ? '保存中...' : lastSaved ? `已保存于 ${lastSaved.toLocaleTimeString()}` : ''}
      </div>
    </div>
  );
}
```

### AI对话组件
```jsx
import React, { useState, useRef, useEffect } from 'react';
import api from './api';

function ChatInterface({ conversationId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.post(
        `/chat/conversations/${conversationId}/messages`,
        { content: input }
      );
      
      setMessages(prev => [...prev, response.data]);
    } catch (error) {
      console.error('发送消息失败:', error);
      // 显示错误消息
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="content">{msg.content}</div>
          </div>
        ))}
        {loading && <div className="loading">AI正在思考...</div>}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="输入消息..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading}>
          发送
        </button>
      </div>
    </div>
  );
}
```

## 错误处理最佳实践

```javascript
// 统一的错误处理
class ApiError extends Error {
  constructor(message, code, details) {
    super(message);
    this.code = code;
    this.details = details;
  }
}

// 错误处理装饰器
function handleApiError(target, propertyKey, descriptor) {
  const originalMethod = descriptor.value;
  
  descriptor.value = async function(...args) {
    try {
      return await originalMethod.apply(this, args);
    } catch (error) {
      if (error.response) {
        // 服务器返回错误
        throw new ApiError(
          error.response.data.detail || '请求失败',
          error.response.status,
          error.response.data
        );
      } else if (error.request) {
        // 网络错误
        throw new ApiError('网络连接失败', 0, null);
      } else {
        // 其他错误
        throw new ApiError('未知错误', -1, error.message);
      }
    }
  };
  
  return descriptor;
}

// 使用示例
class NoteService {
  @handleApiError
  async createNote(noteData) {
    const response = await api.post('/notes/', noteData);
    return response.data;
  }
}
```

## 性能优化建议

1. **使用缓存**
```javascript
const cache = new Map();

async function getCachedData(key, fetcher, ttl = 60000) {
  const cached = cache.get(key);
  
  if (cached && Date.now() - cached.timestamp < ttl) {
    return cached.data;
  }
  
  const data = await fetcher();
  cache.set(key, { data, timestamp: Date.now() });
  
  return data;
}

// 使用示例
const spaces = await getCachedData(
  'user_spaces',
  () => api.get('/spaces/').then(r => r.data),
  300000 // 5分钟缓存
);
```

2. **批量请求**
```javascript
async function batchRequests(requests) {
  const results = await Promise.allSettled(requests);
  
  return results.map((result, index) => ({
    success: result.status === 'fulfilled',
    data: result.value || null,
    error: result.reason || null,
    request: requests[index]
  }));
}
```

3. **防抖搜索**
```javascript
import { debounce } from 'lodash';

const debouncedSearch = debounce(async (query) => {
  const results = await api.post('/notes/search', { query });
  updateSearchResults(results.data);
}, 300);
```

## 测试建议

使用Mock Service Worker (MSW)进行API测试：
```javascript
// mocks/handlers.js
import { rest } from 'msw';

export const handlers = [
  rest.post('/api/v1/auth/login', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'mock_token',
        refresh_token: 'mock_refresh',
        token_type: 'bearer'
      })
    );
  }),
  
  rest.get('/api/v1/notes/', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
        { id: 1, title: 'Mock Note 1', content: '...' },
        { id: 2, title: 'Mock Note 2', content: '...' }
      ])
    );
  })
];
```