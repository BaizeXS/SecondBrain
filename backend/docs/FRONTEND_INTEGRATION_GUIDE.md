# 前后端集成指南

## 1. 后端CORS配置

### 当前配置检查
后端已经配置了CORS中间件，确保在 `.env` 文件中设置正确的前端地址：

```env
# .env 文件
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"]
```

### 开发环境建议配置
```python
# 如果需要更宽松的开发环境配置，可以临时修改
CORS_ORIGINS=["*"]  # 仅用于开发环境！
```

## 2. 重要说明：AI模型统一使用OpenRouter

### 2.1 OpenRouter集成
后端使用OpenRouter作为统一的AI网关，支持多种模型：

```typescript
// AI模型配置
export const AI_MODELS = {
  // OpenRouter Auto模型（推荐）
  auto: "openrouter/auto",
  
  // 免费模型
  free: [
    "qwen/qwen3-235b-a22b:free",
    "qwen/qwen3-30b-a3b:free",
    "deepseek/deepseek-r1-0528:free",
    "meta-llama/llama-4-maverick:free",
    "moonshotai/kimi-k2:free"
  ],
  
  // 付费模型
  premium: [
    "openai/gpt-4.1",
    "openai/gpt-4.1-mini",
    "anthropic/claude-opus-4",
    "anthropic/claude-sonnet-4",
    "google/gemini-2.5-pro"
  ]
};
```

## 3. 前端集成要点

### 3.1 API基础配置
在前端创建API配置文件：

```typescript
// config/api.ts
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
export const API_VERSION = '/api/v1';

export const API_ENDPOINTS = {
  // 认证
  auth: {
    login: `${API_BASE_URL}${API_VERSION}/auth/login`,
    loginJson: `${API_BASE_URL}${API_VERSION}/auth/login/json`, // JSON格式登录
    register: `${API_BASE_URL}${API_VERSION}/auth/register`,
    refresh: `${API_BASE_URL}${API_VERSION}/auth/refresh`,
    logout: `${API_BASE_URL}${API_VERSION}/auth/logout`,
    changePassword: `${API_BASE_URL}${API_VERSION}/auth/change-password`,
    resetPassword: `${API_BASE_URL}${API_VERSION}/auth/reset-password`,
    resetPasswordConfirm: `${API_BASE_URL}${API_VERSION}/auth/reset-password/confirm`,
  },
  
  // 用户
  users: {
    me: `${API_BASE_URL}${API_VERSION}/users/me`,
    update: `${API_BASE_URL}${API_VERSION}/users/me`,
    uploadAvatar: `${API_BASE_URL}${API_VERSION}/users/me/avatar`,
    stats: `${API_BASE_URL}${API_VERSION}/users/me/stats`,
  },
  
  // 聊天（OpenAI兼容接口）
  chat: {
    completions: `${API_BASE_URL}${API_VERSION}/chat/completions`,
    conversations: `${API_BASE_URL}${API_VERSION}/chat/conversations`,
    conversationDetail: (id: number) => `${API_BASE_URL}${API_VERSION}/chat/conversations/${id}`,
    messages: (convId: number) => `${API_BASE_URL}${API_VERSION}/chat/conversations/${convId}/messages`,
    messageBranches: (convId: number) => `${API_BASE_URL}${API_VERSION}/chat/conversations/${convId}/branches`,
    switchBranch: (convId: number) => `${API_BASE_URL}${API_VERSION}/chat/conversations/${convId}/branches/switch`,
    multimodal: `${API_BASE_URL}${API_VERSION}/chat/multimodal`,
  },
  
  // AI代理
  agents: {
    list: `${API_BASE_URL}${API_VERSION}/agents/`,
    detail: (id: number) => `${API_BASE_URL}${API_VERSION}/agents/${id}`,
    execute: (id: number) => `${API_BASE_URL}${API_VERSION}/agents/${id}/execute`,
    deepResearch: `${API_BASE_URL}${API_VERSION}/agents/deep-research`, // Deep Research专用端点
  },
  
  // 空间
  spaces: {
    list: `${API_BASE_URL}${API_VERSION}/spaces/`,
    create: `${API_BASE_URL}${API_VERSION}/spaces/`,
    detail: (id: number) => `${API_BASE_URL}${API_VERSION}/spaces/${id}`,
    update: (id: number) => `${API_BASE_URL}${API_VERSION}/spaces/${id}`,
    delete: (id: number) => `${API_BASE_URL}${API_VERSION}/spaces/${id}`,
    share: (id: number) => `${API_BASE_URL}${API_VERSION}/spaces/${id}/share`,
    access: (id: number) => `${API_BASE_URL}${API_VERSION}/spaces/${id}/access`,
    stats: (id: number) => `${API_BASE_URL}${API_VERSION}/spaces/${id}/stats`,
  },
  
  // 文档
  documents: {
    list: `${API_BASE_URL}${API_VERSION}/documents/`,
    upload: `${API_BASE_URL}${API_VERSION}/documents/upload`,
    search: `${API_BASE_URL}${API_VERSION}/documents/search`,
    detail: (id: number) => `${API_BASE_URL}${API_VERSION}/documents/${id}`,
    download: (id: number) => `${API_BASE_URL}${API_VERSION}/documents/${id}/download`,
    preview: (id: number) => `${API_BASE_URL}${API_VERSION}/documents/${id}/preview`,
    delete: (id: number) => `${API_BASE_URL}${API_VERSION}/documents/${id}`,
  },
  
  // 笔记
  notes: {
    list: `${API_BASE_URL}${API_VERSION}/notes/`,
    create: `${API_BASE_URL}${API_VERSION}/notes/`,
    detail: (id: number) => `${API_BASE_URL}${API_VERSION}/notes/${id}`,
    update: (id: number) => `${API_BASE_URL}${API_VERSION}/notes/${id}`,
    delete: (id: number) => `${API_BASE_URL}${API_VERSION}/notes/${id}`,
    search: `${API_BASE_URL}${API_VERSION}/notes/search`,
  },
  
  // 标注
  annotations: {
    list: `${API_BASE_URL}${API_VERSION}/annotations/`,
    create: `${API_BASE_URL}${API_VERSION}/annotations/`,
    update: (id: number) => `${API_BASE_URL}${API_VERSION}/annotations/${id}`,
    delete: (id: number) => `${API_BASE_URL}${API_VERSION}/annotations/${id}`,
  },
  
  // 引用
  citations: {
    list: `${API_BASE_URL}${API_VERSION}/citations/`,
    create: `${API_BASE_URL}${API_VERSION}/citations/`,
  },
  
  // 导出
  export: {
    markdown: `${API_BASE_URL}${API_VERSION}/export/markdown`,
    pdf: `${API_BASE_URL}${API_VERSION}/export/pdf`,
    notion: `${API_BASE_URL}${API_VERSION}/export/notion`,
    obsidian: `${API_BASE_URL}${API_VERSION}/export/obsidian`,
  },
  
  // Ollama（本地模型）
  ollama: {
    models: `${API_BASE_URL}${API_VERSION}/ollama/models`,
    tags: `${API_BASE_URL}${API_VERSION}/ollama/api/tags`,
    chat: `${API_BASE_URL}${API_VERSION}/ollama/api/chat`,
  },
};
```

### 3.2 认证处理

#### 登录支持两种格式
```typescript
// 方式1：FormData格式（标准OAuth2）
const loginWithFormData = async (username: string, password: string) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await axios.post(API_ENDPOINTS.auth.login, formData);
  return response.data;
};

// 方式2：JSON格式
const loginWithJson = async (username: string, password: string) => {
  const response = await axios.post(API_ENDPOINTS.auth.loginJson, {
    username,
    password
  });
  return response.data;
};
```

#### 完整的认证管理
```typescript
// utils/auth.ts
import axios from 'axios';

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器 - 处理token刷新
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(API_ENDPOINTS.auth.refresh, {
          refresh_token: refreshToken,
        });
        
        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);
        
        // 重试原始请求
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // 刷新失败，跳转到登录页
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
```

### 3.3 文件上传处理
```typescript
// utils/upload.ts
export const uploadDocument = async (file: File, spaceId: number) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('space_id', spaceId.toString());
  
  const response = await apiClient.post(API_ENDPOINTS.documents.upload, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      );
      console.log('Upload progress:', percentCompleted);
    },
  });
  
  return response.data;
};
```

### 3.4 实时聊天处理（OpenAI兼容格式）

#### 聊天完成请求（支持流式和非流式）
```typescript
// utils/chat.ts
interface ChatCompletionRequest {
  model: string;  // 使用OpenRouter模型，如 "openrouter/auto"
  messages: Array<{
    role: 'system' | 'user' | 'assistant';
    content: string | Array<{type: string; text?: string; image_url?: {url: string}}>;
  }>;
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
  conversation_id?: number;  // 可选：关联到对话
  space_id?: number;         // 可选：使用空间文档作为上下文
}

// 非流式聊天
export const createChatCompletion = async (request: ChatCompletionRequest) => {
  const response = await apiClient.post(API_ENDPOINTS.chat.completions, {
    ...request,
    stream: false
  });
  return response.data;
};

// 流式聊天（使用fetch实现SSE）
export const streamChatCompletion = async (
  request: ChatCompletionRequest,
  onMessage: (chunk: string) => void,
  onComplete: () => void,
  onError: (error: any) => void
) => {
  try {
    const response = await fetch(API_ENDPOINTS.chat.completions, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: JSON.stringify({
        ...request,
        stream: true
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader!.read();
      if (done) {
        onComplete();
        break;
      }

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            onComplete();
            return;
          }
          
          try {
            const parsed = JSON.parse(data);
            if (parsed.choices?.[0]?.delta?.content) {
              onMessage(parsed.choices[0].delta.content);
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
  } catch (error) {
    onError(error);
  }
};
```

#### Deep Research API使用
```typescript
// utils/deepResearch.ts
interface DeepResearchRequest {
  query: string;  // 注意：是query不是prompt
  mode: 'general' | 'academic';
  stream?: boolean;
  space_id?: number;  // 可选：关联到空间
}

export const createDeepResearch = async (request: DeepResearchRequest) => {
  if (request.stream) {
    // 流式处理类似上面的streamChatCompletion
    const response = await fetch(API_ENDPOINTS.agents.deepResearch, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: JSON.stringify(request),
    });
    
    // 处理SSE流...
  } else {
    const response = await apiClient.post(API_ENDPOINTS.agents.deepResearch, request);
    return response.data;
  }
};
```

## 4. API测试方案

### 4.1 使用HTTPie进行快速测试
安装HTTPie：
```bash
brew install httpie  # macOS
# 或
pip install httpie
```

创建测试脚本：
```bash
# test_api.sh
#!/bin/bash

API_BASE="http://localhost:8000/api/v1"
TOKEN=""

# 1. 注册用户（密码需满足要求：至少8位，包含大小写字母和数字）
echo "=== 注册用户 ==="
http POST $API_BASE/auth/register \
  username="testuser" \
  email="test@example.com" \
  password="TestPass123" \
  full_name="Test User"

# 2. 登录（使用FormData格式）
echo -e "\n=== 登录 ==="
LOGIN_RESPONSE=$(http --form POST $API_BASE/auth/login \
  username="testuser" \
  password="TestPass123")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Token: ${TOKEN:0:20}..."

# 3. 测试OpenAI兼容的聊天接口
echo -e "\n=== 测试聊天 ==="
http POST $API_BASE/chat/completions \
  "Authorization: Bearer $TOKEN" \
  model="openrouter/auto" \
  messages:='[{"role": "user", "content": "Hello, AI!"}]' \
  stream:=false

# 4. 创建空间
echo -e "\n=== 创建空间 ==="
SPACE_RESPONSE=$(http POST $API_BASE/spaces/ \
  "Authorization: Bearer $TOKEN" \
  name="测试空间" \
  description="这是一个测试空间" \
  color="#4CAF50" \
  icon="📚")

SPACE_ID=$(echo $SPACE_RESPONSE | jq -r '.id')
echo "Space ID: $SPACE_ID"

# 5. 测试Deep Research
echo -e "\n=== 测试Deep Research ==="
http POST $API_BASE/agents/deep-research \
  "Authorization: Bearer $TOKEN" \
  query="人工智能的最新进展" \
  mode="general" \
  stream:=false \
  space_id:=$SPACE_ID

# 6. 上传文档
echo -e "\n=== 上传文档 ==="
echo "测试文档内容" > test.txt
http --form POST $API_BASE/documents/upload \
  "Authorization: Bearer $TOKEN" \
  space_id=$SPACE_ID \
  file@test.txt

# 7. 搜索文档
echo -e "\n=== 搜索文档 ==="
http POST $API_BASE/documents/search \
  "Authorization: Bearer $TOKEN" \
  query="测试" \
  space_id:=$SPACE_ID

# 清理
rm test.txt
```

### 4.2 创建Python测试客户端
```python
# test_client.py
import asyncio
import aiohttp
import json
from typing import Dict, Any

class SecondBrainTestClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.token = None
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """注册新用户"""
        data = {
            "username": username,
            "email": email,
            "password": password,
            "full_name": "Test User"
        }
        async with self.session.post(
            f"{self.api_base}/auth/register",
            json=data
        ) as resp:
            return await resp.json()
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录（使用FormData）"""
        data = aiohttp.FormData()
        data.add_field('username', username)
        data.add_field('password', password)
        
        async with self.session.post(
            f"{self.api_base}/auth/login",
            data=data
        ) as resp:
            result = await resp.json()
            self.token = result.get("access_token")
            return result
    
    async def chat_completion(self, message: str, model: str = "openrouter/auto") -> str:
        """发送聊天消息（OpenAI兼容格式）"""
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": message}
            ],
            "stream": False
        }
        async with self.session.post(
            f"{self.api_base}/chat/completions",
            json=data,
            headers=self._headers()
        ) as resp:
            result = await resp.json()
            return result["choices"][0]["message"]["content"]
    
    async def deep_research(self, query: str, mode: str = "general") -> Dict[str, Any]:
        """执行Deep Research"""
        data = {
            "query": query,  # 注意：是query不是prompt
            "mode": mode,
            "stream": False
        }
        async with self.session.post(
            f"{self.api_base}/agents/deep-research",
            json=data,
            headers=self._headers()
        ) as resp:
            return await resp.json()
    
    async def create_space(self, name: str, description: str) -> Dict[str, Any]:
        """创建空间"""
        data = {
            "name": name,
            "description": description,
            "color": "#4CAF50",
            "icon": "📚"
        }
        async with self.session.post(
            f"{self.api_base}/spaces/",
            json=data,
            headers=self._headers()
        ) as resp:
            return await resp.json()
    
    async def upload_document(self, space_id: int, file_path: str) -> Dict[str, Any]:
        """上传文档"""
        data = aiohttp.FormData()
        data.add_field('space_id', str(space_id))
        data.add_field('file',
                      open(file_path, 'rb'),
                      filename=file_path.split('/')[-1])
        
        headers = {"Authorization": f"Bearer {self.token}"}
        async with self.session.post(
            f"{self.api_base}/documents/upload",
            data=data,
            headers=headers
        ) as resp:
            return await resp.json()


async def test_full_flow():
    """测试完整流程"""
    async with SecondBrainTestClient() as client:
        print("1. 注册用户...")
        try:
            await client.register("testuser2", "test2@example.com", "TestPass123")
            print("✓ 注册成功")
        except Exception as e:
            print(f"✗ 注册失败: {e}")
        
        print("\n2. 用户登录...")
        login_result = await client.login("testuser2", "TestPass123")
        print(f"✓ 登录成功，Token: {login_result['access_token'][:20]}...")
        
        print("\n3. 测试AI聊天...")
        ai_response = await client.chat_completion("你好，请介绍一下你自己")
        print(f"✓ AI回复: {ai_response[:100]}...")
        
        print("\n4. 创建空间...")
        space = await client.create_space("测试空间", "API测试用空间")
        print(f"✓ 空间创建成功，ID: {space['id']}")
        
        print("\n5. 测试Deep Research...")
        research = await client.deep_research("人工智能的最新进展", "general")
        print(f"✓ Deep Research完成，结果: {str(research)[:100]}...")
        
        print("\n6. 创建测试文档...")
        with open("test_doc.txt", "w") as f:
            f.write("这是一个测试文档，包含一些AI和机器学习的内容。")
        
        print("\n7. 上传文档...")
        doc = await client.upload_document(space['id'], "test_doc.txt")
        print(f"✓ 文档上传成功，ID: {doc['id']}")
        
        print("\n测试完成！")
        
        # 清理
        import os
        os.remove("test_doc.txt")


if __name__ == "__main__":
    asyncio.run(test_full_flow())
```

### 4.3 Postman测试集合
创建Postman环境变量：
```json
{
  "name": "SecondBrain Dev",
  "values": [
    {
      "key": "base_url",
      "value": "http://localhost:8000",
      "enabled": true
    },
    {
      "key": "api_version",
      "value": "/api/v1",
      "enabled": true
    },
    {
      "key": "token",
      "value": "",
      "enabled": true
    },
    {
      "key": "space_id",
      "value": "",
      "enabled": true
    },
    {
      "key": "conversation_id",
      "value": "",
      "enabled": true
    }
  ]
}
```

创建测试集合，包含以下请求：

1. **认证流程**
   - POST `{{base_url}}{{api_version}}/auth/register` (JSON Body)
   - POST `{{base_url}}{{api_version}}/auth/login` (x-www-form-urlencoded)
   - POST `{{base_url}}{{api_version}}/auth/login/json` (JSON Body)
   - GET `{{base_url}}{{api_version}}/users/me`

2. **AI聊天（OpenAI兼容）**
   - POST `{{base_url}}{{api_version}}/chat/completions`
     ```json
     {
       "model": "openrouter/auto",
       "messages": [
         {"role": "user", "content": "Hello!"}
       ],
       "stream": false
     }
     ```

3. **Deep Research**
   - POST `{{base_url}}{{api_version}}/agents/deep-research`
     ```json
     {
       "query": "AI最新进展",
       "mode": "general",
       "stream": false
     }
     ```

4. **空间管理**
   - GET `{{base_url}}{{api_version}}/spaces/`
   - POST `{{base_url}}{{api_version}}/spaces/`
   - PUT `{{base_url}}{{api_version}}/spaces/{{space_id}}`

5. **文档操作**
   - POST `{{base_url}}{{api_version}}/documents/upload` (form-data)
   - GET `{{base_url}}{{api_version}}/documents/`
   - POST `{{base_url}}{{api_version}}/documents/search`

在登录请求的Tests标签中添加：
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Save token", function () {
    var jsonData = pm.response.json();
    pm.environment.set("token", jsonData.access_token);
});
```

## 5. 实时API测试工具

### 5.1 创建实时测试界面
```html
<!DOCTYPE html>
<html>
<head>
    <title>SecondBrain API测试器</title>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .test-section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
        .success { color: green; }
        .error { color: red; }
        button { padding: 10px 20px; margin: 5px; }
        input, textarea { width: 100%; margin: 5px 0; padding: 8px; }
        #results { background: #f5f5f5; padding: 15px; margin-top: 20px; }
        .model-select { margin: 10px 0; }
    </style>
</head>
<body>
    <h1>SecondBrain API 测试器</h1>
    
    <div class="test-section">
        <h2>1. 登录测试</h2>
        <input type="text" id="username" placeholder="用户名" value="demo_user">
        <input type="password" id="password" placeholder="密码" value="DemoPass123">
        <button onclick="testLogin()">测试登录</button>
    </div>
    
    <div class="test-section">
        <h2>2. 获取空间列表</h2>
        <button onclick="testGetSpaces()">获取空间</button>
    </div>
    
    <div class="test-section">
        <h2>3. 文档搜索</h2>
        <input type="text" id="searchQuery" placeholder="搜索关键词" value="transformer">
        <button onclick="testSearch()">搜索文档</button>
    </div>
    
    <div class="test-section">
        <h2>4. AI对话测试（OpenRouter）</h2>
        <div class="model-select">
            <label>选择模型：</label>
            <select id="modelSelect">
                <option value="openrouter/auto">Auto（自动选择）</option>
                <option value="qwen/qwen3-235b-a22b:free">Qwen3 235B（免费）</option>
                <option value="deepseek/deepseek-r1-0528:free">DeepSeek R1（免费）</option>
                <option value="openai/gpt-4.1">GPT-4.1（付费）</option>
                <option value="anthropic/claude-opus-4">Claude Opus 4（付费）</option>
            </select>
        </div>
        <textarea id="chatMessage" rows="3" placeholder="输入消息">什么是注意力机制？</textarea>
        <button onclick="testChat()">发送消息</button>
    </div>
    
    <div class="test-section">
        <h2>5. Deep Research测试</h2>
        <input type="text" id="researchQuery" placeholder="研究主题" value="人工智能的最新进展">
        <select id="researchMode">
            <option value="general">常规模式</option>
            <option value="academic">学术模式</option>
        </select>
        <button onclick="testDeepResearch()">开始研究</button>
    </div>
    
    <div id="results">
        <h3>测试结果：</h3>
        <pre id="output">等待测试...</pre>
    </div>
    
    <script>
        const API_BASE = 'http://localhost:8000/api/v1';
        let token = '';
        let conversationId = null;
        
        function log(message, isError = false) {
            const output = document.getElementById('output');
            const timestamp = new Date().toLocaleTimeString();
            const className = isError ? 'error' : 'success';
            output.innerHTML += `<span class="${className}">[${timestamp}] ${message}</span>\n`;
            output.scrollTop = output.scrollHeight;
        }
        
        async function testLogin() {
            try {
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                
                const formData = new FormData();
                formData.append('username', username);
                formData.append('password', password);
                
                const response = await axios.post(`${API_BASE}/auth/login`, formData);
                token = response.data.access_token;
                
                log(`✓ 登录成功！Token: ${token.substring(0, 20)}...`);
                
                // 设置默认请求头
                axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            } catch (error) {
                log(`✗ 登录失败: ${error.response?.data?.detail || error.message}`, true);
            }
        }
        
        async function testGetSpaces() {
            try {
                const response = await axios.get(`${API_BASE}/spaces/`);
                log(`✓ 获取空间成功！找到 ${response.data.total} 个空间`);
                log(JSON.stringify(response.data.spaces.map(s => s.name), null, 2));
            } catch (error) {
                log(`✗ 获取空间失败: ${error.response?.data?.detail || error.message}`, true);
            }
        }
        
        async function testSearch() {
            try {
                const query = document.getElementById('searchQuery').value;
                const response = await axios.post(`${API_BASE}/documents/search`, {
                    query: query,
                    limit: 5
                });
                log(`✓ 搜索成功！找到 ${response.data.total} 个结果`);
                response.data.results.forEach(r => {
                    log(`  - ${r.title} (相关度: ${r.score})`);
                });
            } catch (error) {
                log(`✗ 搜索失败: ${error.response?.data?.detail || error.message}`, true);
            }
        }
        
        async function testChat() {
            try {
                const message = document.getElementById('chatMessage').value;
                const model = document.getElementById('modelSelect').value;
                
                const response = await axios.post(`${API_BASE}/chat/completions`, {
                    messages: [
                        {role: "user", content: message}
                    ],
                    model: model,
                    stream: false
                });
                
                const aiResponse = response.data.choices[0].message.content;
                log(`✓ AI回复 (${model}): ${aiResponse.substring(0, 200)}...`);
            } catch (error) {
                log(`✗ 聊天失败: ${error.response?.data?.detail || error.message}`, true);
            }
        }
        
        async function testDeepResearch() {
            try {
                const query = document.getElementById('researchQuery').value;
                const mode = document.getElementById('researchMode').value;
                
                log(`开始Deep Research: ${query} (${mode}模式)...`);
                
                const response = await axios.post(`${API_BASE}/agents/deep-research`, {
                    query: query,
                    mode: mode,
                    stream: false
                });
                
                log(`✓ Deep Research完成！`);
                log(`研究ID: ${response.data.research_id}`);
                log(`空间ID: ${response.data.space_id}`);
                log(`状态: ${response.data.status}`);
            } catch (error) {
                log(`✗ Deep Research失败: ${error.response?.data?.detail || error.message}`, true);
            }
        }
        
        // 页面加载时自动登录
        window.onload = () => {
            log('API测试器准备就绪！请先点击"测试登录"按钮。');
            log('注意：确保后端已配置OPENROUTER_API_KEY');
        };
    </script>
</body>
</html>
```

## 6. 前端集成检查清单

### 6.1 环境配置
- [ ] 确认后端运行在 `http://localhost:8000`
- [ ] 确认前端CORS来源已添加到后端配置
- [ ] 确认API文档可访问：`http://localhost:8000/api/v1/docs`
- [ ] 确认OpenRouter API密钥已配置：`OPENROUTER_API_KEY`

### 6.2 认证流程
- [ ] 登录支持FormData和JSON两种格式
- [ ] 密码满足要求（8位以上，包含大小写字母和数字）
- [ ] Token存储在localStorage
- [ ] 请求自动携带Authorization头
- [ ] Token过期自动刷新
- [ ] 401错误正确处理

### 6.3 核心功能
- [ ] AI聊天使用OpenRouter模型格式（如：`openrouter/auto`）
- [ ] Deep Research使用`query`字段（不是`prompt`）
- [ ] 文件上传使用FormData
- [ ] 搜索功能使用POST请求
- [ ] 聊天流式响应处理（SSE）
- [ ] 错误信息正确显示
- [ ] 加载状态管理

### 6.4 性能优化
- [ ] API请求缓存
- [ ] 图片懒加载
- [ ] 分页加载
- [ ] 请求防抖/节流

## 7. 常见问题解决

### CORS错误
```
Access to XMLHttpRequest at 'http://localhost:8000/...' from origin 'http://localhost:3000' has been blocked by CORS policy
```
**解决方案**：
1. 检查后端 `.env` 中的 `CORS_ORIGINS`
2. 重启后端服务
3. 确认请求URL正确

### 401 Unauthorized
```
Request failed with status code 401
```
**解决方案**：
1. 检查token是否正确存储
2. 确认token格式：`Bearer <token>`
3. 检查token是否过期

### 密码验证失败
```
密码长度至少8位 / 密码必须包含至少一个大写字母
```
**解决方案**：
确保密码满足所有要求：
- 至少8个字符
- 至少一个大写字母
- 至少一个小写字母
- 至少一个数字

### 文件上传失败
```
Request failed with status code 422
```
**解决方案**：
1. 使用FormData而不是JSON
2. 不要手动设置Content-Type（让浏览器自动设置）
3. 检查文件大小限制（默认100MB）

### OpenRouter API错误
```
OpenRouter API key not configured
```
**解决方案**：
1. 在 `.env` 文件中配置 `OPENROUTER_API_KEY`
2. 重启后端服务
3. 检查API密钥是否有效

### WebSocket/SSE连接失败
**解决方案**：
1. 使用fetch API或EventSource处理SSE
2. 确保后端返回正确的Content-Type: text/event-stream
3. 处理连接断开和重连
4. 注意SSE的数据格式：`data: {...}\n\n`

### Deep Research失败
```
query field required
```
**解决方案**：
Deep Research API使用`query`字段，不是`prompt`：
```json
{
  "query": "研究主题",  // 正确
  "mode": "general"
}
```

## 8. 部署前检查

1. **环境变量**：
   - 生产环境的OpenRouter API密钥
   - 数据库连接字符串
   - JWT密钥
   - CORS允许的域名

2. **HTTPS**：生产环境必须使用HTTPS

3. **CORS**：生产环境限制具体域名，不要使用 `*`

4. **日志**：配置适当的日志级别

5. **监控**：添加API监控和告警

6. **限流**：配置API速率限制

## 9. API端点快速参考

### 认证相关
- `POST /auth/login` - FormData格式登录
- `POST /auth/login/json` - JSON格式登录
- `POST /auth/register` - 用户注册
- `POST /auth/refresh` - 刷新Token

### AI功能
- `POST /chat/completions` - OpenAI兼容聊天接口
- `POST /agents/deep-research` - Deep Research API
- `GET /agents/` - 获取AI代理列表

### 内容管理
- `GET/POST /spaces/` - 空间管理
- `POST /documents/upload` - 文档上传
- `POST /documents/search` - 文档搜索
- `GET/POST /notes/` - 笔记管理

### 导出功能
- `POST /export/markdown` - 导出为Markdown
- `POST /export/pdf` - 导出为PDF
- `POST /export/notion` - 导出到Notion