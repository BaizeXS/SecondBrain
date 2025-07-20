// src/services/apiService.js

// API基础配置
import { getApiBaseUrl } from '../config/api';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v1';

// 在 apiRequest 函数中添加更好的错误处理
const apiRequest = async (endpoint, options = {}) => {
  const token = localStorage.getItem('access_token');
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  console.log('API Request Headers:', config.headers);

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      // 如果是认证错误且没有 token，返回空结果而不是抛出错误
      if ((response.status === 401 || response.status === 400) && !token) {
        console.log(`Skipping API call due to missing authentication: ${endpoint}`);
        return getEmptyResponse(endpoint);
      }
      
      // 如果是 /users/me 接口失败，说明 token 无效
      if (endpoint === '/users/me' && (response.status === 401 || response.status === 400)) {
        throw new Error('Token validation failed');
      }
      
      // 如果有 token 但仍然是 400/401，记录详细错误但返回空结果以避免崩溃
      if (response.status === 400 || response.status === 401) {
        console.warn(`API call failed with authentication: ${endpoint}`, errorData);
        return getEmptyResponse(endpoint);
      }
      
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    // 网络错误处理
    if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
      console.error(`Network error for ${endpoint}:`, error);
      return getEmptyResponse(endpoint);
    }
    
    console.error(`API Request failed: ${endpoint}`, error);
    throw error;
  }
};

// 辅助函数：根据端点返回空响应
const getEmptyResponse = (endpoint) => {
  if (endpoint.includes('/agents')) {
    return { agents: [], items: [] };
  } else if (endpoint.includes('/spaces')) {
    return { spaces: [] };
  } else if (endpoint.includes('/documents')) {
    return { documents: [] };
  } else if (endpoint.includes('/chat/models')) {
    return { models: [] };
  } else if (endpoint.includes('/chat/conversations')) {
    return { conversations: [] };
  }
  return {};
};

// 文件上传请求函数
const apiUploadRequest = async (endpoint, formData) => {
  const token = localStorage.getItem('access_token');
  
  const config = {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API Upload failed: ${endpoint}`, error);
    throw error;
  }
};

// ===== 认证相关 API =====

export const authAPI = {
  // 用户注册
  register: async (userData) => {
    return apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  // 用户登录
  login: async (credentials) => {
    // credentials: { username, password }
    const formBody = new URLSearchParams();
    formBody.append('username', credentials.username);
    formBody.append('password', credentials.password);

    const response = await apiRequest('/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formBody.toString(),
    });

    // 保存token到localStorage
    if (response.access_token) {
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
    }

    return response;
  },

  // 刷新token
  refreshToken: async () => {
    const refresh_token = localStorage.getItem('refresh_token');
    if (!refresh_token) {
      throw new Error('No refresh token available');
    }

    const response = await apiRequest('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token }),
    });
    
    if (response.access_token) {
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
    }
    
    return response;
  },

  // 用户登出
  logout: async () => {
    try {
      await apiRequest('/auth/logout', { method: 'POST' });
    } finally {
      // 无论API调用是否成功，都清除本地token
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },

  // 修改密码
  changePassword: async (passwordData) => {
    return apiRequest('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(passwordData),
    });
  },

  // 重置密码请求
  resetPassword: async (email) => {
    return apiRequest('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  },

  // 确认重置密码
  confirmResetPassword: async (token, newPassword) => {
    return apiRequest('/auth/reset-password/confirm', {
      method: 'POST',
      body: JSON.stringify({ token, new_password: newPassword }),
    });
  },
};

// ===== 用户相关 API =====

export const userAPI = {
  // 获取当前用户信息
  getCurrentUser: async () => {
    return apiRequest('/users/me');
  },

  // 更新用户信息
  updateUser: async (userData) => {
    return apiRequest('/users/me', {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  },

  // 获取用户统计信息
  getUserStats: async () => {
    return apiRequest('/users/stats');
  },
};

// ===== 空间相关 API =====

export const spaceAPI = {
  // 获取空间列表
  getSpaces: async (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.skip !== undefined) queryParams.append('skip', params.skip);
    if (params.limit !== undefined) queryParams.append('limit', params.limit);
    if (params.search) queryParams.append('search', params.search);
    if (params.tags) queryParams.append('tags', params.tags.join(','));
    if (params.is_public !== undefined) queryParams.append('is_public', params.is_public);
    if (params.include_public !== undefined) queryParams.append('include_public', params.include_public);

    const queryString = queryParams.toString();
    const endpoint = `/spaces${queryString ? `?${queryString}` : ''}`;
    return apiRequest(endpoint);
  },

  // 获取单个空间详情
  getSpace: async (spaceId) => {
    return apiRequest(`/spaces/${spaceId}`);
  },

  // 创建空间
  createSpace: async (spaceData) => {
    return apiRequest('/spaces/', {
      method: 'POST',
      body: JSON.stringify(spaceData),
    });
  },

  // 更新空间
  updateSpace: async (spaceId, spaceData) => {
    return apiRequest(`/spaces/${spaceId}`, {
      method: 'PUT',
      body: JSON.stringify(spaceData),
    });
  },

  // 删除空间
  deleteSpace: async (spaceId, force = false) => {
    const queryParams = new URLSearchParams();
    if (force) queryParams.append('force', 'true');
    
    const queryString = queryParams.toString();
    const endpoint = `/spaces/${spaceId}${queryString ? `?${queryString}` : ''}`;
    
    return apiRequest(endpoint, { method: 'DELETE' });
  },
};

// ===== 文档相关 API =====

export const documentAPI = {
  // 获取文档列表
  getDocuments: async (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.space_id !== undefined) queryParams.append('space_id', params.space_id);
    if (params.skip !== undefined) queryParams.append('skip', params.skip);
    if (params.limit !== undefined) queryParams.append('limit', params.limit);
    if (params.search) queryParams.append('search', params.search);
    if (params.processing_status) queryParams.append('processing_status', params.processing_status);

    const queryString = queryParams.toString();
    const endpoint = `/documents${queryString ? `?${queryString}` : ''}`;
    return apiRequest(endpoint);
  },

  // 获取单个文档详情
  getDocument: async (documentId) => {
    return apiRequest(`/documents/${documentId}`);
  },

  // 上传文档
  uploadDocument: async (spaceId, file, title = null, tags = null) => {
    const formData = new FormData();
    formData.append('space_id', spaceId);
    formData.append('file', file);
    if (title) formData.append('title', title);
    if (tags) formData.append('tags', tags);

    return apiUploadRequest('/documents/upload', formData);
  },

  // 更新文档
  updateDocument: async (documentId, documentData) => {
    return apiRequest(`/documents/${documentId}`, {
      method: 'PUT',
      body: JSON.stringify(documentData),
    });
  },

  // 删除文档
  deleteDocument: async (documentId) => {
    return apiRequest(`/documents/${documentId}`, { method: 'DELETE' });
  },

  // 下载文档
  downloadDocument: async (documentId) => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/download`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }
    
    return response.blob();
  },

  // 获取文档预览
  getDocumentPreview: async (documentId, page = null, format = 'html') => {
    const queryParams = new URLSearchParams();
    if (page !== null) queryParams.append('page', page);
    queryParams.append('format', format);

    const queryString = queryParams.toString();
    const endpoint = `/documents/${documentId}/preview?${queryString}`;
    return apiRequest(endpoint);
  },

  // 获取文档内容
  getDocumentContent: async (documentId, start = 0, length = 5000) => {
    const queryParams = new URLSearchParams();
    queryParams.append('start', start);
    queryParams.append('length', length);

    const queryString = queryParams.toString();
    const endpoint = `/documents/${documentId}/content?${queryString}`;
    return apiRequest(endpoint);
  },

  // 导入URL
  importURL: async (importData) => {
    return apiRequest('/documents/import-url', {
      method: 'POST',
      body: JSON.stringify(importData),
    });
  },

  // 批量导入URL
  batchImportURLs: async (importData) => {
    return apiRequest('/documents/batch-import-urls', {
      method: 'POST',
      body: JSON.stringify(importData),
    });
  },

  // 分析URL
  analyzeURL: async (analysisData) => {
    return apiRequest('/documents/analyze-url', {
      method: 'POST',
      body: JSON.stringify(analysisData),
    });
  },
};

// ===== 聊天相关 API =====

export const chatAPI = {
  // 获取可用模型列表
  getAvailableModels: async () => {
    return apiRequest('/chat/models');
  },
  
  // 创建聊天完成（兼容OpenAI）
  createChatCompletion: async (requestData) => {
    return apiRequest('/chat/completions', {
      method: 'POST',
      body: JSON.stringify(requestData),
    });
  },
  
  // 创建新对话
  createConversation: async (conversationData) => {
    // 过滤掉 null 值
    const cleanData = {};
    for (const [key, value] of Object.entries(conversationData)) {
      if (value !== null && value !== undefined) {
        cleanData[key] = value;
      }
    }
    
    return apiRequest('/chat/conversations', {
      method: 'POST',
      body: JSON.stringify(cleanData),
    });
  },

  // 获取对话列表
  getConversations: async (params = {}) => {
    const queryParams = new URLSearchParams();
    // 只有当 space_id 不是 null 和 undefined 时才添加参数
    if (params.space_id !== undefined && params.space_id !== null) {
      queryParams.append('space_id', params.space_id);
    }
    if (params.mode) queryParams.append('mode', params.mode);
    if (params.skip !== undefined) queryParams.append('skip', params.skip);
    if (params.limit !== undefined) queryParams.append('limit', params.limit);

    const queryString = queryParams.toString();
    const endpoint = `/chat/conversations${queryString ? `?${queryString}` : ''}`;
    return apiRequest(endpoint);
  },

  // 获取单个对话详情
  getConversation: async (conversationId, messageLimit = 50) => {
    const queryParams = new URLSearchParams();
    queryParams.append('message_limit', messageLimit);

    const queryString = queryParams.toString();
    const endpoint = `/chat/conversations/${conversationId}?${queryString}`;
    return apiRequest(endpoint);
  },

  // 更新对话
  updateConversation: async (conversationId, conversationData) => {
    return apiRequest(`/chat/conversations/${conversationId}`, {
      method: 'PUT',
      body: JSON.stringify(conversationData),
    });
  },

  // 删除对话
  deleteConversation: async (conversationId) => {
    return apiRequest(`/chat/conversations/${conversationId}`, { method: 'DELETE' });
  },

  // 发送消息
  sendMessage: async (conversationId, messageData, files = []) => {
    const formData = new FormData();
    
    // 添加消息内容
    if (messageData.content) {
      formData.append('content', messageData.content);
    }
    
    // 添加模型信息
    if (messageData.model) {
      formData.append('model', messageData.model);
    }
    
    // 添加自动切换视觉模式
    formData.append('auto_switch_vision', messageData.auto_switch_vision !== false);
    
    // 添加文件附件
    files.forEach(file => {
      formData.append('attachments', file);
    });

    return apiUploadRequest(`/chat/conversations/${conversationId}/messages`, formData);
  },

  // 重新生成消息
  regenerateMessage: async (conversationId, messageId, params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.model) queryParams.append('model', params.model);
    if (params.temperature !== undefined) queryParams.append('temperature', params.temperature);

    const queryString = queryParams.toString();
    const endpoint = `/chat/conversations/${conversationId}/messages/${messageId}/regenerate${queryString ? `?${queryString}` : ''}`;
    
    return apiRequest(endpoint, { method: 'POST' });
  },

  // 分析附件
  analyzeAttachments: async (files) => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('attachments', file);
    });

    return apiUploadRequest('/chat/analyze-attachments', formData);
  },

  // 分支相关API
  branches: {
    // 创建分支
    createBranch: async (conversationId, branchData) => {
      return apiRequest(`/chat/conversations/${conversationId}/branches`, {
        method: 'POST',
        body: JSON.stringify(branchData),
      });
    },

    // 获取分支列表
    getBranches: async (conversationId) => {
      return apiRequest(`/chat/conversations/${conversationId}/branches`);
    },

    // 切换分支
    switchBranch: async (conversationId, switchData) => {
      return apiRequest(`/chat/conversations/${conversationId}/branches/switch`, {
        method: 'POST',
        body: JSON.stringify(switchData),
      });
    },

    // 获取分支历史
    getBranchHistory: async (conversationId, messageId = null) => {
      const queryParams = new URLSearchParams();
      if (messageId !== null) queryParams.append('message_id', messageId);

      const queryString = queryParams.toString();
      const endpoint = `/chat/conversations/${conversationId}/branches/history${queryString ? `?${queryString}` : ''}`;
      return apiRequest(endpoint);
    },

    // 合并分支
    mergeBranch: async (conversationId, mergeData) => {
      return apiRequest(`/chat/conversations/${conversationId}/branches/merge`, {
        method: 'POST',
        body: JSON.stringify(mergeData),
      });
    },

    // 删除分支
    deleteBranch: async (conversationId, branchName) => {
      return apiRequest(`/chat/conversations/${conversationId}/branches/${branchName}`, { 
        method: 'DELETE' 
      });
    },
  },

  // 正确的流式聊天完成实现
  createStreamingChatCompletion: async (requestData) => {
    console.log('=== Starting streaming chat completion ===');
    console.log('Request data:', requestData);
    
    const token = localStorage.getItem('access_token');
    if (!token) {
      throw new Error('No authentication token found');
    }
    
    const url = `${API_BASE_URL}/chat/completions`;
    console.log('Request URL:', url);
    
    const requestBody = {
      ...requestData,
      stream: true, // 确保启用流式输出
    };
    console.log('Request body:', requestBody);
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/event-stream', // 明确接受SSE
        },
        body: JSON.stringify(requestBody),
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', [...response.headers.entries()]);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      // 检查响应类型
      const contentType = response.headers.get('content-type');
      console.log('Content-Type:', contentType);
      
      if (!contentType?.includes('text/event-stream') && !contentType?.includes('text/plain')) {
        console.warn('Unexpected content type for streaming response:', contentType);
      }

      console.log('Stream response ready, returning reader');
      return response;
    } catch (error) {
      console.error('Failed to create streaming request:', error);
      throw error;
    }
  },

  // 测试流式接口连接
  testStreamingConnection: async () => {
    console.log('Testing streaming connection...');
    
    try {
      const response = await chatAPI.createStreamingChatCompletion({
        model: 'openrouter/auto',
        messages: [
          { role: 'user', content: 'Hello, this is a test message. Please respond with a simple greeting.' }
        ],
        temperature: 0.7,
        max_tokens: 50,
      });

      console.log('Test response received:', response);
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            
            if (data === '[DONE]') {
              console.log('Test completed successfully with content:', fullContent);
              return { success: true, content: fullContent };
            }
            
            if (data === '' || data === 'null') continue;
            
            try {
              const chunk = JSON.parse(data);
              const content = chunk.choices?.[0]?.delta?.content;
              if (content) {
                fullContent += content;
              }
            } catch (e) {
              console.warn('Parse error in test:', e);
            }
          }
        }
      }
      
      return { success: true, content: fullContent };
      
    } catch (error) {
      console.error('Streaming test failed:', error);
      return { success: false, error: error.message };
    }
  },

  // 重新实现模拟流式响应
  createMockStreamingResponse: async (text = "这是一个模拟的流式响应测试。我会一个字一个字地出现，让你看到流式输出的效果。") => {
    console.log('Creating mock streaming response with text:', text);
    
    return new Promise((resolve) => {
      const encoder = new TextEncoder();
      let index = 0;
      
      const stream = new ReadableStream({
        start(controller) {
          console.log('Starting mock stream');
          
          const sendNextChunk = () => {
            if (index < text.length) {
              const char = text[index];
              const chunk = {
                id: "chatcmpl-mock",
                object: "chat.completion.chunk", 
                created: Math.floor(Date.now() / 1000),
                model: "mock-model",
                choices: [{
                  index: 0,
                  delta: { content: char },
                  finish_reason: null
                }]
              };
              
              const chunkData = `data: ${JSON.stringify(chunk)}\n\n`;
              console.log('Sending chunk:', char, 'Index:', index);
              controller.enqueue(encoder.encode(chunkData));
              
              index++;
              // 使用更短的延迟让效果更明显
              setTimeout(sendNextChunk, 50); // 50ms延迟
            } else {
              console.log('Mock stream finished, sending final chunks');
              
              // 发送结束chunk
              const finalChunk = {
                id: "chatcmpl-mock",
                object: "chat.completion.chunk",
                created: Math.floor(Date.now() / 1000), 
                model: "mock-model",
                choices: [{
                  index: 0,
                  delta: {},
                  finish_reason: "stop"
                }]
              };
              
              controller.enqueue(encoder.encode(`data: ${JSON.stringify(finalChunk)}\n\n`));
              controller.enqueue(encoder.encode(`data: [DONE]\n\n`));
              controller.close();
            }
          };
          
          // 开始发送
          sendNextChunk();
        }
      });
      
      const response = new Response(stream, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        }
      });
      
      resolve(response);
    });
  },
};

// ===== 代理相关 API =====

export const agentAPI = {
  // 获取代理列表
  getAgents: async () => {
    return apiRequest('/agents/');
  },

  // 获取单个代理
  getAgent: async (agentId) => {
    return apiRequest(`/agents/${agentId}`);
  },

  // 创建代理
  createAgent: async (agentData) => {
    return apiRequest('/agents/', {
      method: 'POST',
      body: JSON.stringify(agentData),
    });
  },

  // 更新代理
  updateAgent: async (agentId, agentData) => {
    return apiRequest(`/agents/${agentId}`, {
      method: 'PUT',
      body: JSON.stringify(agentData),
    });
  },

  // 删除代理
  deleteAgent: async (agentId) => {
    return apiRequest(`/agents/${agentId}`, { method: 'DELETE' });
  },
  
  // 创建深度研究
  createDeepResearch: async (requestData) => {
    return apiRequest('/agents/deep-research', {
      method: 'POST',
      body: JSON.stringify(requestData),
    });
  },
};

// ===== 笔记相关 API =====

export const noteAPI = {
  // 获取笔记列表
  getNotes: async (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.space_id !== undefined) queryParams.append('space_id', params.space_id);
    if (params.skip !== undefined) queryParams.append('skip', params.skip);
    if (params.limit !== undefined) queryParams.append('limit', params.limit);
    if (params.search) queryParams.append('search', params.search);

    const queryString = queryParams.toString();
    const endpoint = `/notes${queryString ? `?${queryString}` : ''}`;
    return apiRequest(endpoint);
  },

  // 获取单个笔记
  getNote: async (noteId) => {
    return apiRequest(`/notes/${noteId}`);
  },

  // 创建笔记
  createNote: async (noteData) => {
    return apiRequest('/notes/', {
      method: 'POST',
      body: JSON.stringify(noteData),
    });
  },

  // 更新笔记
  updateNote: async (noteId, noteData) => {
    return apiRequest(`/notes/${noteId}`, {
      method: 'PUT',
      body: JSON.stringify(noteData),
    });
  },

  // 删除笔记
  deleteNote: async (noteId) => {
    return apiRequest(`/notes/${noteId}`, { method: 'DELETE' });
  },

  // 获取笔记版本历史
  getNoteVersions: async (noteId) => {
    return apiRequest(`/notes/${noteId}/versions`);
  },
};

// ===== 标注相关 API =====

export const annotationAPI = {
  // 获取标注列表
  getAnnotations: async (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.document_id !== undefined) queryParams.append('document_id', params.document_id);
    if (params.skip !== undefined) queryParams.append('skip', params.skip);
    if (params.limit !== undefined) queryParams.append('limit', params.limit);

    const queryString = queryParams.toString();
    const endpoint = `/annotations${queryString ? `?${queryString}` : ''}`;
    return apiRequest(endpoint);
  },

  // 创建标注
  createAnnotation: async (annotationData) => {
    return apiRequest('/annotations/', {
      method: 'POST',
      body: JSON.stringify(annotationData),
    });
  },

  // 更新标注
  updateAnnotation: async (annotationId, annotationData) => {
    return apiRequest(`/annotations/${annotationId}`, {
      method: 'PUT',
      body: JSON.stringify(annotationData),
    });
  },

  // 删除标注
  deleteAnnotation: async (annotationId) => {
    return apiRequest(`/annotations/${annotationId}`, { method: 'DELETE' });
  },
};

// ===== 引用相关 API =====

export const citationAPI = {
  // 获取引用列表
  getCitations: async (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.document_id !== undefined) queryParams.append('document_id', params.document_id);
    if (params.skip !== undefined) queryParams.append('skip', params.skip);
    if (params.limit !== undefined) queryParams.append('limit', params.limit);

    const queryString = queryParams.toString();
    const endpoint = `/citations${queryString ? `?${queryString}` : ''}`;
    return apiRequest(endpoint);
  },

  // 创建引用
  createCitation: async (citationData) => {
    return apiRequest('/citations/', {
      method: 'POST',
      body: JSON.stringify(citationData),
    });
  },

  // 更新引用
  updateCitation: async (citationId, citationData) => {
    return apiRequest(`/citations/${citationId}`, {
      method: 'PUT',
      body: JSON.stringify(citationData),
    });
  },

  // 删除引用
  deleteCitation: async (citationId) => {
    return apiRequest(`/citations/${citationId}`, { method: 'DELETE' });
  },
};

// ===== 导出相关 API =====

export const exportAPI = {
  // 导出对话
  exportConversation: async (conversationId, format = 'json') => {
    const queryParams = new URLSearchParams();
    queryParams.append('format', format);

    const queryString = queryParams.toString();
    const endpoint = `/export/conversations/${conversationId}?${queryString}`;
    
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    if (!response.ok) {
      throw new Error(`Export failed: ${response.status}`);
    }
    
    return response.blob();
  },

  // 导出空间
  exportSpace: async (spaceId, format = 'json') => {
    const queryParams = new URLSearchParams();
    queryParams.append('format', format);

    const queryString = queryParams.toString();
    const endpoint = `/export/spaces/${spaceId}?${queryString}`;
    
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    if (!response.ok) {
      throw new Error(`Export failed: ${response.status}`);
    }
    
    return response.blob();
  },
};

// ===== Ollama相关 API =====

export const ollamaAPI = {
  // 获取模型列表
  getModels: async () => {
    return apiRequest('/ollama/models');
  },

  // 获取模型信息
  getModelInfo: async (modelName) => {
    return apiRequest(`/ollama/models/${modelName}`);
  },

  // 拉取模型
  pullModel: async (modelName) => {
    return apiRequest(`/ollama/models/${modelName}/pull`, { method: 'POST' });
  },

  // 删除模型
  deleteModel: async (modelName) => {
    return apiRequest(`/ollama/models/${modelName}`, { method: 'DELETE' });
  },
};

// ===== 兼容性函数（保持向后兼容） =====

// 为了保持与现有代码的兼容性，保留一些原有的函数名
export const fetchProjects = async () => {
  // 现在从后端获取空间列表
  const response = await spaceAPI.getSpaces();
  return response.spaces || [];
};

export const saveAllProjects = async (projects, colorIndex) => {
  // 这个函数现在主要用于本地状态管理
  // 实际的数据保存通过各个API完成
  console.log('Projects saved to backend via individual APIs');
  return true;
};

export const fetchFileContent = async (projectId, fileId) => {
  // 现在从后端获取文档内容
  const document = await documentAPI.getDocument(fileId);
  return document.content;
};

export const uploadFile = async (projectId, fileObject) => {
  // 现在通过后端API上传文档
  const response = await documentAPI.uploadDocument(projectId, fileObject);
  return {
    id: response.id,
    name: response.filename,
    type: response.content_type,
    size: response.file_size,
    uploadedAt: response.created_at,
    url: `/documents/${response.id}`,
    content: response.content,
  };
};

export const getAiChatResponse = async (agent, chatHistory, userMessage, attachedFiles) => {
  // 现在通过后端聊天API获取响应
  const requestData = {
    model: agent.modelName,
    messages: [
      ...chatHistory.map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'assistant',
        content: msg.text
      })),
      { role: 'user', content: userMessage }
    ],
    stream: false,
  };

  const response = await chatAPI.createChatCompletion(requestData);
  return response.choices[0].message.content;
};

// 导出所有API模块
export default {
  auth: authAPI,
  user: userAPI,
  space: spaceAPI,
  document: documentAPI,
  chat: chatAPI,
  agent: agentAPI,
  note: noteAPI,
  annotation: annotationAPI,
  citation: citationAPI,
  export: exportAPI,
  ollama: ollamaAPI,
};