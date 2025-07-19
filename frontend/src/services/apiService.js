// src/services/apiService.js

// --- 项目 (Project) 相关的 API ---

const PROJECTS_STORAGE_KEY = 'neuroCoreProjects';
const COLOR_INDEX_STORAGE_KEY = 'projectColorIndex';

// 模拟获取所有项目
export const fetchProjects = async () => {
  console.log("apiService: Fetching all projects...");
  return new Promise((resolve) => {
    setTimeout(() => { // 模拟网络延迟
      try {
        const storedProjects = localStorage.getItem(PROJECTS_STORAGE_KEY);
        const projects = storedProjects ? JSON.parse(storedProjects) : []; // 如果没有则返回空数组
        console.log("apiService: Fetched projects successfully.", projects);
        resolve(projects);
      } catch (error) {
        console.error("apiService: Error fetching projects.", error);
        resolve([]); // 出错时返回空数组
      }
    }, 500); // 500ms 延迟
  });
};

// 模拟保存/更新整个项目列表 (批量操作)
export const saveAllProjects = async (projects, colorIndex) => {
  console.log("apiService: Saving all projects and color index...");
  return new Promise((resolve) => {
    setTimeout(() => {
      try {
        localStorage.setItem(PROJECTS_STORAGE_KEY, JSON.stringify(projects));
        localStorage.setItem(COLOR_INDEX_STORAGE_KEY, colorIndex.toString());
        console.log("apiService: Saved all projects successfully.");
        resolve(true);
      } catch (error) {
        console.error("apiService: Error saving all projects.", error);
        resolve(false);
      }
    }, 300);
  });
};

// --- 文件 (File) 相关的 API ---

// 模拟获取单个文件的详细内容
export const fetchFileContent = async (projectId, fileId) => {
  console.log(`apiService: Fetching content for file ${fileId} in project ${projectId}...`);
  // **后端协作点**: 这里是后端需要提供的核心接口之一。
  // GET /api/projects/{projectId}/files/{fileId}
  return new Promise((resolve) => {
    setTimeout(() => {
      // 模拟：从 localStorage 的项目数据中查找文件内容
      const projects = JSON.parse(localStorage.getItem(PROJECTS_STORAGE_KEY) || '[]');
      const project = projects.find(p => p.id === projectId);
      const file = project?.files?.find(f => f.id === fileId);
      if (file && file.content) {
        console.log("apiService: Found file content.");
        resolve(file.content);
      } else {
        console.error("apiService: File content not found.");
        resolve(null); // 或 reject(new Error('File content not found'))
      }
    }, 400);
  });
};


// 模拟文件上传 (这是一个复杂的过程)
// 前端职责：将文件发送到后端。后端职责：接收、存储、返回文件元数据。
export const uploadFile = async (projectId, fileObject /* File object from input */) => {
  console.log(`apiService: Uploading file "${fileObject.name}" to project ${projectId}...`);
  // **后端协作点**: 后端需要提供一个文件上传的 endpoint。
  // POST /api/projects/{projectId}/files
  // 通常使用 FormData 来发送文件
  const formData = new FormData();
  formData.append('file', fileObject);
  formData.append('fileName', fileObject.name);
  // formData.append('other_metadata', 'some_value');

  // **未来真实的 fetch 调用会是这样:**
  /*
  try {
    const response = await fetch(`/api/projects/${projectId}/files`, {
      method: 'POST',
      body: formData,
      // headers: { 'Authorization': 'Bearer ...' } // 如果需要认证
    });
    if (!response.ok) throw new Error('File upload failed.');
    const newFileMetadata = await response.json(); // 后端应返回新文件的元数据
    return newFileMetadata;
  } catch (error) {
    console.error("apiService: File upload failed.", error);
    throw error;
  }
  */

  // **当前模拟的实现**:
  return new Promise((resolve) => {
    setTimeout(() => {
      // 模拟成功上传，并返回一个包含 URL 和元数据的新文件对象
      const newFileMetadata = {
        id: `file-server-${fileObject.name}-${Date.now()}`,
        name: fileObject.name,
        type: fileObject.type,
        size: fileObject.size,
        uploadedAt: new Date().toISOString(),
        url: `/mock-files/${fileObject.name}`, // 模拟的服务器文件URL
        content: `(This is the mocked content for ${fileObject.name})` // 模拟后端也保存了内容
      };
      console.log("apiService: Mock upload successful. Returning metadata:", newFileMetadata);
      resolve(newFileMetadata);
    }, 800);
  });
};

// --- AI 聊天相关的 API ---
export const getAiChatResponse = async (agent, chatHistory, userMessage, attachedFiles) => {
  console.log(`apiService: Getting AI response using agent "${agent.name}"...`);
  // **后端协作点**: 这是调用大模型的核心接口。
  // POST /api/chat
  const payload = {
    agentConfig: {
      systemPrompt: agent.systemPrompt,
      model: agent.modelName,
    },
    // 如果是自定义API，后端可能需要这些额外信息
    customApiConfig: agent.apiProvider === 'custom' ? {
      endpoint: agent.apiEndpoint,
      apiKey: agent.apiKey, // 后端应安全处理此 key
    } : null,
    history: chatHistory.map(msg => ({ role: msg.sender === 'user' ? 'user' : 'assistant', content: msg.text })),
    newMessage: userMessage,
    // 后端需要知道如何处理这些文件引用
    contextFiles: attachedFiles.map(f => ({ id: f.id, name: f.name })),
  };
  console.log("apiService: Sending payload to chat API:", payload);

  // **未来真实的 fetch 调用:**
  /*
  const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
  });
  const data = await response.json();
  return data.reply; // 假设后端返回 { reply: "..." }
  */

  // **当前模拟的实现**:
  return new Promise(resolve => {
    setTimeout(() => {
      const reply = `Mock AI response using agent "${agent.name}" for message: "${userMessage.substring(0, 20)}..."`;
      console.log("apiService: Mock AI reply received:", reply);
      resolve(reply);
    }, 1200);
  });
};