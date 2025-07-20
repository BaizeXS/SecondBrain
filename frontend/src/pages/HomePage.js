// src/pages/HomePage.js
import React, { useState, useEffect, useRef, useCallback } from 'react';
import styles from './HomePage.module.css';
import { useSidebar } from '../contexts/SidebarContext';
import { useProjects } from '../contexts/ProjectContext';
import {
  FiPaperclip, FiSend, FiDownload, FiSave,
  FiMessageSquare, FiBriefcase, FiEdit2, FiTerminal,
  FiFileText, FiX, FiChevronsRight, FiChevronsLeft
} from 'react-icons/fi';
import { IoSparklesOutline } from "react-icons/io5";
import MessageFileAttachments from '../components/chat/MessageFileAttachments';
import SaveProjectModal from '../components/modals/SaveProjectModal';
import ChatInputInterface from '../components/chat/ChatInputInterface';
import { useNavigate } from 'react-router-dom';
import { useAgents, getIconComponent } from '../contexts/AgentContext'; // <<< 导入 useAgents 和 getIconComponent
import apiService from '../services/apiService';


const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const numBytes = Number(bytes);
  if (isNaN(numBytes) || numBytes === 0) return '0 Bytes';
  const i = Math.floor(Math.log(numBytes) / Math.log(k));
  return parseFloat((numBytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

const simplifyFileForContext = f => ({ 
  id: f.id, 
  name: f.name, 
  size: f.size, 
  type: f.type, 
  preview: f.preview, 
  uploadedAt: f.uploadedAt,
  isAiGenerated: f.isAiGenerated,
  aiAgent: f.aiAgent
});
const simplifyNoteForContext = n => ({ 
  id: n.id, 
  name: n.name, 
  preview: n.preview, 
  content: n.content, 
  createdAt: n.createdAt,
  isAiGenerated: n.isAiGenerated,
  aiAgent: n.aiAgent
});

// 将从后端API获取模型列表


const HomePage = () => {
  const { agents, loadingAgents } = useAgents(); // <<< 从 Context 获取 agents
  const [activeAgentId, setActiveAgentId] = useState(null); // <<< 现在用 ID 来跟踪激活的 agent
  const { openRightSidebarWithView, isRightSidebarOpen, rightSidebarView, closeRightSidebar } = useSidebar();
  const { addProject } = useProjects();
  const navigate = useNavigate();

  const [message, setMessage] = useState(''); // This is managed by ChatInputInterface now if passed as prop
  const [chatHistory, setChatHistory] = useState([]);
  const [activeAgent, setActiveAgent] = useState('general');
  const [conversationId, setConversationId] = useState(null); // 添加对话ID状态

  const [currentChatFiles, setCurrentChatFiles] = useState([]);
  const [currentChatNotes, setCurrentChatNotes] = useState([]);

  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const chatMessagesAreaRef = useRef(null);

  // States for ChatInputInterface props
  const [selectedModel, setSelectedModel] = useState('openrouter/auto');
  const [isDeepSearchMode, setIsDeepSearchMode] = useState(false);
  const [availableModels, setAvailableModels] = useState([]);

  // 添加模拟流式响应测试
  const [useMockStreaming, setUseMockStreaming] = useState(false);

  useEffect(() => {
    if (chatMessagesAreaRef.current) {
      chatMessagesAreaRef.current.scrollTop = chatMessagesAreaRef.current.scrollHeight;
    }
  }, [chatHistory]);

  // 获取可用模型列表
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          console.log('No token available, using default models');
          setAvailableModels([
            { id: 'openrouter/auto', name: 'Auto (自动选择最佳模型)' }
          ]);
          return;
        }
  
        const response = await apiService.chat.getAvailableModels();
        const chatModels = response.models ? response.models.filter(model => model.type === 'chat') : [];
        
        if (chatModels.length > 0) {
          setAvailableModels(chatModels.map(model => ({
            id: model.id,
            name: model.name
          })));
        } else {
          setAvailableModels([
            { id: 'openrouter/auto', name: 'Auto (自动选择最佳模型)' }
          ]);
        }
      } catch (error) {
        console.error('Failed to fetch models:', error);
        setAvailableModels([
          { id: 'openrouter/auto', name: 'Auto (自动选择最佳模型)' }
        ]);
      }
    };
    
    fetchModels();
  }, []);
  
  // 加载最近的对话（如果有）
  useEffect(() => {
    const loadRecentConversation = async () => {
      try {
        // 获取最近的对话列表 - 不传 space_id 参数，而不是传 null
        const conversations = await apiService.chat.getConversations({
          limit: 1
        });
        
        if (conversations.items && conversations.items.length > 0) {
          const recentConv = conversations.items[0];
          setConversationId(recentConv.id);
          
          // 加载对话消息
          const conversationDetail = await apiService.chat.getConversation(recentConv.id);
          if (conversationDetail.messages && conversationDetail.messages.length > 0) {
            const history = conversationDetail.messages.map(msg => ({
              sender: msg.role === 'user' ? 'user' : 'ai',
              text: msg.content,
              timestamp: msg.created_at
            }));
            setChatHistory(history);
          }
        }
      } catch (error) {
        console.error('Failed to load recent conversation:', error);
      }
    };
    
    // 只在没有从 sessionStorage 恢复会话时加载
    if (chatHistory.length === 0) {
      loadRecentConversation();
    }
  }, []);

  // --- 步骤 1.1: 新增 useEffect，用于在挂载时检查 sessionStorage 中是否有恢复请求 ---
  useEffect(() => {
    try {
      const sessionToRestoreJSON = sessionStorage.getItem('sessionToRestore');
      if (sessionToRestoreJSON) {
        console.log("HomePage: Found session restore request in sessionStorage.");
        const sessionToRestore = JSON.parse(sessionToRestoreJSON);
        // 加载恢复的数据到 HomePage 的状态中
        setChatHistory(sessionToRestore.chatHistory || []);
        // 从元数据恢复 files state (注意：rawFile 会丢失)
        setCurrentChatFiles((sessionToRestore.filesMeta || []).map(f => ({ ...f, rawFile: null })));
        setCurrentChatNotes(sessionToRestore.notes || []);

        // 非常重要：加载后立即清除，防止刷新页面后再次恢复
        sessionStorage.removeItem('sessionToRestore');
      }
    } catch (error) {
      console.error("Failed to restore session from sessionStorage:", error);
      sessionStorage.removeItem('sessionToRestore'); // 清除损坏的数据
    }
  }, []); // 空依赖数组，确保只在组件首次挂载时运行一次

  useEffect(() => {
    // 当 agents 加载完成且 activeAgentId 尚未设置时，设置默认的 active agent
    if (!loadingAgents && agents.length > 0 && !activeAgentId) {
      // 如果是深度研究模式，尝试找到 Deep Research Agent
      if (isDeepSearchMode) {
        const researchAgent = agents.find(a => 
          a.name === 'Deep Research' || 
          (a.backendData && a.backendData.agent_type === 'research')
        );
        if (researchAgent) {
          setActiveAgentId(researchAgent.id);
          return;
        }
      }
      
      // 否则使用 General Agent
      const generalAgent = agents.find(a => a.name === 'General');
      setActiveAgentId(generalAgent ? generalAgent.id : agents[0].id);
    }
  }, [agents, loadingAgents, activeAgentId, isDeepSearchMode]);

  // --- 步骤 1.2: 新增 useEffect，用于在组件卸载时保存临时会话 ---
  useEffect(() => {
    // 这个 effect 只在组件挂载时运行，并返回一个清理函数
    return () => {
      // 这个函数会在 HomePage 组件卸载时执行
      // 我们需要一种方法来获取卸载前一刻的最新 state
      // 直接在这里访问 chatHistory, currentChatFiles, currentChatNotes 可能会闭包旧的 state
      // 一个常见的模式是使用一个 ref 来存储最新的 state

      // 不过，对于现代 React，清理函数会闭包最后一次渲染时的 state，这通常是可行的。
      // 让我们先用这个直接的方法。

      // 检查会话是否有实质内容
      if (chatHistory.length > 0 || currentChatFiles.length > 0 || currentChatNotes.length > 0) {
        const tempSession = {
          chatHistory: chatHistory,
          filesMeta: currentChatFiles.map(simplifyFileForContext), // 保存元数据
          notes: currentChatNotes,
          lastUpdatedAt: new Date().toISOString(),
        };
        console.log("HomePage: Unmounting and saving non-empty temporary session to localStorage.");
        localStorage.setItem('tempChatSession', JSON.stringify(tempSession));
      } else {
        // 如果会话是空的，我们不做任何事，保留 localStorage 中可能存在的旧的、有内容的会话
        console.log("HomePage: Unmounting with an empty session, not overwriting temp session in localStorage.");
      }
    };
    // 依赖项包含所有需要保存的状态，这样清理函数中的闭包才是最新的
  }, [chatHistory, currentChatFiles, currentChatNotes]);


  // --- 步骤 1.3: 保持从 sessionStorage 恢复的逻辑不变 ---
  useEffect(() => {
    try {
      const sessionToRestoreJSON = sessionStorage.getItem('sessionToRestore');
      if (sessionToRestoreJSON) {
        console.log("HomePage: Found session restore request.");
        const sessionToRestore = JSON.parse(sessionToRestoreJSON);
        setChatHistory(sessionToRestore.chatHistory || []);
        // 从元数据恢复文件列表 (注意 rawFile 丢失)
        // 你需要一种方式在恢复时，如果可能的话，让用户重新关联原始文件
        // 这是一个更复杂的用户体验问题，目前我们只恢复元数据
        setCurrentChatFiles((sessionToRestore.filesMeta || []).map(f => ({ ...f, rawFile: null })));
        setCurrentChatNotes(sessionToRestore.notes || []);
        sessionStorage.removeItem('sessionToRestore');
      }
    } catch (error) {
      console.error("Failed to restore session:", error);
      sessionStorage.removeItem('sessionToRestore');
    }
  }, []); // 只在挂载时运行

  const handleUpdateChatNotesFromSidebar = useCallback((updatedSimplifiedNotes) => {
    setCurrentChatNotes(prevFullNotes => {
      return updatedSimplifiedNotes.map(simpleNote => {
        const existingNote = prevFullNotes.find(n => n.id === simpleNote.id);
        return { ...(existingNote || {}), ...simpleNote, content: simpleNote.content || existingNote?.content || simpleNote.preview };
      });
    });
  }, []);

  const handleUpdateChatFilesFromSidebar = useCallback((updatedSimplifiedFiles) => {
    setCurrentChatFiles(prevFullFiles => {
      return updatedSimplifiedFiles.map(simpleFile => {
        const existingFile = prevFullFiles.find(f => f.id === simpleFile.id);
        return { ...(existingFile || { rawFile: null }), ...simpleFile, rawFile: existingFile ? existingFile.rawFile : null };
      });
    });
  }, []);

  useEffect(() => {
    const sidebarDataPayload = {
      files: currentChatFiles.map(simplifyFileForContext),
      notes: currentChatNotes.map(simplifyNoteForContext),
      onUpdateChatNotes: handleUpdateChatNotesFromSidebar,
      onUpdateChatFiles: handleUpdateChatFilesFromSidebar,
    };
    if (isRightSidebarOpen) {
      let needsUpdate = false;
      if (rightSidebarView?.type !== 'CHAT_CONTEXT_INFO') {
        needsUpdate = true;
      } else {
        const currentSidebarFiles = rightSidebarView.data?.files || [];
        const currentSidebarNotes = rightSidebarView.data?.notes || [];
        if (JSON.stringify(currentSidebarFiles) !== JSON.stringify(sidebarDataPayload.files) ||
          JSON.stringify(currentSidebarNotes) !== JSON.stringify(sidebarDataPayload.notes)) {
          needsUpdate = true;
        }
      }
      if (needsUpdate) {
        openRightSidebarWithView({
          type: 'CHAT_CONTEXT_INFO', data: sidebarDataPayload,
          activeTab: rightSidebarView?.activeTab // 保持当前tab，不自动切换
        });
      }
    }
  }, [isRightSidebarOpen, rightSidebarView?.type, rightSidebarView?.activeTab, rightSidebarView?.data, currentChatFiles, currentChatNotes, openRightSidebarWithView, handleUpdateChatNotesFromSidebar, handleUpdateChatFilesFromSidebar]);

  const handleAiResponseWithFiles = (aiGeneratedFiles) => {
    const newFilesToAdd = aiGeneratedFiles.map(f => ({ ...f, rawFile: null, uploadedAt: f.uploadedAt || new Date().toISOString() }));
    setCurrentChatFiles(prev => Array.from(new Map([...prev, ...newFilesToAdd].map(item => [item.id, item])).values()));
  };

  // 辅助函数：上传文件到后端
  const uploadFileToBackend = async (file, spaceId = null) => {
    try {
      // 如果没有 spaceId，创建一个临时空间或使用默认空间
      let targetSpaceId = spaceId;
      if (!targetSpaceId) {
        // 创建一个临时空间用于存储聊天文件
        const tempSpace = await apiService.space.createSpace({
          name: `Chat Files - ${new Date().toLocaleDateString()}`,
          description: 'Temporary space for chat file uploads',
          is_public: false,
          tags: ['chat', 'temp']
        });
        targetSpaceId = tempSpace.id;
      }
      
      // 上传文件
      const uploadedDoc = await apiService.document.uploadDocument(
        targetSpaceId,
        file,
        file.name,
        ['chat-attachment']
      );
      
      return uploadedDoc;
    } catch (error) {
      console.error('File upload failed:', error);
      throw error;
    }
  };

  const handleSendMessage = async (messageText, filesFromInput, notesFromInput = []) => {
    // 深度研究模式处理保持不变
    if (isDeepSearchMode) {
      try {
        const newUserMessage = {
          sender: 'user', 
          text: `🔍 深度研究：${messageText}`,
          timestamp: new Date().toISOString()
        };
        setChatHistory(prev => [...prev, newUserMessage]);
        
        const researchingMessage = {
          sender: 'ai',
          text: '正在进行深度研究，这可能需要一些时间...',
          timestamp: new Date().toISOString()
        };
        setChatHistory(prev => [...prev, researchingMessage]);
        
        const response = await apiService.agent.createDeepResearch({
          query: messageText,
          mode: 'general',
          stream: false
        });
        
        setChatHistory(prev => {
          const newHistory = [...prev];
          newHistory[newHistory.length - 1] = {
            sender: 'ai',
            text: response.result,
            timestamp: new Date().toISOString(),
            metadata: {
              space_id: response.space_id,
              sources: response.sources,
              total_sources: response.total_sources
            }
          };
          return newHistory;
        });
        
        if (response.space_id) {
          setTimeout(() => {
            if (window.confirm('深度研究已完成并创建了新的知识空间。是否前往查看？')) {
              navigate(`/neurocore/project/${response.space_id}`);
            }
          }, 1000);
        }
        
        return;
      } catch (error) {
        console.error('Deep research failed:', error);
        setChatHistory(prev => {
          const newHistory = [...prev];
          newHistory[newHistory.length - 1] = {
            sender: 'ai',
            text: `深度研究失败：${error.message}`,
            timestamp: new Date().toISOString()
          };
          return newHistory;
        });
        return;
      }
    }
    
    // === 常规聊天的流式处理 ===
    const activeAgentObject = agents.find(a => a.id === activeAgentId);
    if (!activeAgentObject) {
      alert("Error: Active agent not found!");
      return;
    }

    const filesAttachedToMessage = [...filesFromInput];
    const notesAttachedToMessage = [...notesFromInput];

    // 1. 添加用户消息
    const newUserMessage = {
      sender: 'user', 
      text: messageText,
      files: filesAttachedToMessage.map(f => ({ 
        id: f.id, name: f.name, size: f.size, type: f.type, 
        uploadedAt: f.uploadedAt, preview: f.preview,
        isAiGenerated: f.isAiGenerated, aiAgent: f.aiAgent
      })),
      notes: notesAttachedToMessage.map(n => ({ 
        id: n.id, name: n.name, content: n.content, createdAt: n.createdAt, 
        preview: n.preview, isAiGenerated: n.isAiGenerated, aiAgent: n.aiAgent
      })),
      timestamp: new Date().toISOString()
    };
    
    setChatHistory(prev => [...prev, newUserMessage]);

    // 2. 创建AI消息占位符
    const aiMessageId = `msg-ai-${Date.now()}`;
    const streamingAiMessage = {
      id: aiMessageId,
      sender: 'ai',
      text: '',
      timestamp: new Date().toISOString(),
      files: [],
      streaming: true,
    };
    
    setChatHistory(prev => [...prev, streamingAiMessage]);

    try {
      if (useMockStreaming) {
        // === 使用模拟流式响应 ===
        console.log("Starting mock streaming test");
        
        const mockText = `你好！我收到了你的消息："${messageText}"。这是一个模拟的流式回复，每个字符会逐个显示，展示流式输出的效果。现在你应该能看到文字一个一个地出现。`;
        
        await streamingResponseHandler(
          await apiService.chat.createMockStreamingResponse(mockText),
          aiMessageId
        );
        
      } else if (activeAgentObject.apiProvider === 'custom') {
        // === 自定义API处理（非流式） ===
        console.log("Using custom API:", activeAgentObject.apiEndpoint);
        try {
          const response = await fetch(activeAgentObject.apiEndpoint, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${activeAgentObject.apiKey}`
            },
            body: JSON.stringify({
              model: activeAgentObject.modelName,
              messages: [
                { role: 'system', content: activeAgentObject.systemPrompt },
                ...chatHistory.filter(msg => !msg.streaming).map(msg => ({
                  role: msg.sender === 'user' ? 'user' : 'assistant',
                  content: msg.text
                })),
                { role: 'user', content: messageText },
              ],
            })
          });
          
          if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
          }
          
          const data = await response.json();
          const aiText = data.choices[0].message.content;
          
          // 模拟打字机效果
          await simulateTypingEffect(aiText, aiMessageId);
          
        } catch (error) {
          console.error("Custom API call failed:", error);
          setChatHistory(prev => prev.map(msg => 
            msg.id === aiMessageId 
              ? { ...msg, text: `Error calling custom API: ${error.message}`, streaming: false, error: true }
              : msg
          ));
        }
        
      } else {
        // === 后端API流式处理 ===
        console.log("Using backend streaming API");
        
        let currentConversationId = conversationId;
        if (!currentConversationId) {
          const conversationData = {
            title: messageText.substring(0, 50) + (messageText.length > 50 ? '...' : ''),
            mode: 'chat'
          };
          
          const newConversation = await apiService.chat.createConversation(conversationData);
          currentConversationId = newConversation.id;
          setConversationId(currentConversationId);
        }
        
        // 处理文件上传
        const documentIds = [];
        if (filesAttachedToMessage.length > 0) {
          for (const file of filesAttachedToMessage) {
            if (file.id && !isNaN(parseInt(file.id))) {
              documentIds.push(parseInt(file.id));
            } else if (file.rawFile) {
              try {
                const uploadedDoc = await uploadFileToBackend(file.rawFile, currentConversationId);
                if (uploadedDoc && uploadedDoc.id) {
                  documentIds.push(uploadedDoc.id);
                  file.id = uploadedDoc.id.toString();
                  file.url = `/documents/${uploadedDoc.id}`;
                }
              } catch (uploadError) {
                console.error('Failed to upload file:', uploadError);
              }
            }
          }
        }
        
        // 构建聊天历史
        const messages = [
          { role: 'system', content: activeAgentObject.systemPrompt || '你是一个有帮助的助手。' },
          ...chatHistory.filter(msg => !msg.streaming).map(msg => ({
            role: msg.sender === 'user' ? 'user' : 'assistant',
            content: msg.text
          })),
          { role: 'user', content: messageText }
        ];
        
        // 启动流式聊天
        const streamRequestData = {
          model: selectedModel,
          messages: messages,
          temperature: 0.7,
          conversation_id: currentConversationId,
          ...(documentIds.length > 0 && { document_ids: documentIds })
        };
        
        const streamResponse = await apiService.chat.createStreamingChatCompletion(streamRequestData);
        await streamingResponseHandler(streamResponse, aiMessageId);
      }

      // 处理文件/笔记上下文（保持原有逻辑）
      if (filesFromInput.length > 0) {
        const newFilesToAddToContext = filesFromInput.filter(
          newFile => !currentChatFiles.some(
            existingFile => existingFile.name === newFile.name && existingFile.size === newFile.size
          )
        );

        if (newFilesToAddToContext.length > 0) {
          setCurrentChatFiles(prev => {
            const combined = [...prev, ...newFilesToAddToContext];
            return Array.from(new Map(combined.map(f => [f.id, f])).values());
          });
        }
      }

      if (notesFromInput.length > 0) {
        const newNotesToAddToContext = notesFromInput.filter(
          newNote => !currentChatNotes.some(existingNote => existingNote.id === newNote.id)
        );

        if (newNotesToAddToContext.length > 0) {
          setCurrentChatNotes(prev => {
            const combined = [...prev, ...newNotesToAddToContext];
            return Array.from(new Map(combined.map(n => [n.id, n])).values());
          });
        }
      }

      // 9. AI 生成文件/笔记（保持原有逻辑）
      const shouldGenerateFile = Math.random() > 0.5;
      const shouldGenerateNote = Math.random() > 0.7;
      
      if (shouldGenerateFile) {
        const aiGeneratedFile = {
          id: `ai-file-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
          name: `AI Generated File ${new Date().toLocaleTimeString()}`,
          size: Math.floor(Math.random() * 1000000) + 1000,
          type: 'application/pdf',
          uploadedAt: new Date().toISOString(),
          preview: 'AI generated content',
          isAiGenerated: true,
          aiAgent: activeAgentObject.name
        };
        
        setCurrentChatFiles(prev => {
          const combined = [...prev, aiGeneratedFile];
          return Array.from(new Map(combined.map(f => [f.id, f])).values());
        });
      }

      if (shouldGenerateNote) {
        const aiGeneratedNote = {
          id: `ai-note-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
          name: `AI Generated Note ${new Date().toLocaleTimeString()}`,
          content: `AI generated note based on: "${messageText.substring(0, 50)}..."`,
          preview: `AI generated note...`,
          createdAt: new Date().toISOString(),
          isAiGenerated: true,
          aiAgent: activeAgentObject.name
        };
        
        setCurrentChatNotes(prev => {
          const combined = [...prev, aiGeneratedNote];
          return Array.from(new Map(combined.map(n => [n.id, n])).values());
        });
      }

    } catch (error) {
      console.error('Error in streaming message:', error);
      
      setChatHistory(prev => prev.map(msg => 
        msg.id === aiMessageId 
          ? { 
              ...msg, 
              text: `错误: ${error.message}`, 
              streaming: false, 
              error: true 
            }
          : msg
      ));
    }
  };

  // 通用的流式响应处理器
  const streamingResponseHandler = async (streamResponse, aiMessageId) => {
    console.log('Starting streaming response handler');
    
    if (!streamResponse || !streamResponse.body) {
      throw new Error('No response body for streaming');
    }

    const reader = streamResponse.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullContent = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log('Stream reading completed');
          break;
        }
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine || !trimmedLine.startsWith('data: ')) continue;
          
          const data = trimmedLine.slice(6).trim();
          
          if (data === '[DONE]') {
            console.log('Received [DONE], finalizing stream');
            setChatHistory(prev => prev.map(msg => 
              msg.id === aiMessageId 
                ? { ...msg, text: fullContent, streaming: false }
                : msg
            ));
            return;
          }
          
          if (data === '' || data === 'null') continue;
          
          try {
            const chunk = JSON.parse(data);
            
            if (chunk.error) {
              throw new Error(chunk.error.message || 'Stream error');
            }
            
            const content = chunk.choices?.[0]?.delta?.content;
            
            if (content) {
              fullContent += content;
              console.log('Received content chunk:', content, 'Total length:', fullContent.length);
              
              // 实时更新AI消息 - 这是关键部分
              setChatHistory(prev => {
                const newHistory = prev.map(msg => {
                  if (msg.id === aiMessageId) {
                    return { 
                      ...msg, 
                      text: fullContent, 
                      streaming: true 
                    };
                  }
                  return msg;
                });
                return newHistory;
              });
            }
          } catch (parseError) {
            console.warn('Failed to parse chunk:', data, parseError);
          }
        }
      }
    } finally {
      reader.releaseLock();
      
      // 确保最终状态正确
      setChatHistory(prev => prev.map(msg => 
        msg.id === aiMessageId 
          ? { ...msg, text: fullContent, streaming: false }
          : msg
      ));
    }
  };

  // 模拟打字机效果（用于非流式API）
  const simulateTypingEffect = async (text, aiMessageId) => {
    console.log('Starting typing simulation for text:', text);
    
    let currentText = '';
    const characters = text.split('');
    
    for (let i = 0; i < characters.length; i++) {
      currentText += characters[i];
      
      setChatHistory(prev => prev.map(msg => 
        msg.id === aiMessageId 
          ? { ...msg, text: currentText, streaming: i < characters.length - 1 }
          : msg
      ));
      
      // 等待50ms再显示下一个字符
      await new Promise(resolve => setTimeout(resolve, 50));
    }
    
    console.log('Typing simulation completed');
  };

  const handleOpenSaveModal = () => {
    if (chatHistory.length === 0 && currentChatFiles.length === 0 && currentChatNotes.length === 0) {
      alert("Nothing to save yet."); return;
    } setIsSaveModalOpen(true);
  };
  const handleCloseSaveModal = () => setIsSaveModalOpen(false);
  const actuallySaveProject = (projectNameFromModal) => {
    const newProjectData = {
      name: projectNameFromModal, description: "", chatHistory: [...chatHistory],
      files: currentChatFiles.map(simplifyFileForContext), // Pass simplified
      notes: currentChatNotes.map(simplifyNoteForContext), // Pass simplified
      createdAt: new Date().toISOString(),
    };
    const savedProject = addProject(newProjectData);
    if (savedProject && savedProject.id) {
      alert(`Project "${savedProject.name}" saved!`); handleCloseSaveModal();
      // 清空 HomePage 的状态
      setChatHistory([]);
      setCurrentChatFiles([]);
      setCurrentChatNotes([]);

      // **关键**：因为会话已经被永久保存，所以明确地从 localStorage 中移除临时会话
      localStorage.removeItem('tempChatSession');
      console.log("HomePage: Project saved, temporary session cleared from localStorage.");

      // ... (更新 RightSidebar，导航到新项目)
      navigate(`/neurocore/project/${savedProject.id}`);
    } else { alert("Error saving project."); }
  };

  const handleModelChange = (e) => setSelectedModel(e.target.value);
  const handleToggleDeepSearch = () => setIsDeepSearchMode(!isDeepSearchMode);
  const handleDownloadChat = () => alert('Download chat initiated from HomePage.');

  const isChatStarted = chatHistory.length > 0;
  const showInitialPromptLayout = !isChatStarted;

  // 在组件内添加测试函数
  const testStreamingConnection = async () => {
    console.log('Testing streaming connection...');
    
    try {
      const result = await apiService.chat.testStreamingConnection();
      if (result.success) {
        alert(`流式连接测试成功！\n收到内容: ${result.content}`);
      } else {
        alert(`流式连接测试失败: ${result.error}`);
      }
    } catch (error) {
      alert(`测试失败: ${error.message}`);
    }
  };

  return (
    <div className={styles.homePageLayout}>
      {/* 开发环境调试控制面板 */}
      {process.env.NODE_ENV === 'development' && (
        <div style={{
          position: 'fixed',
          top: '10px',
          right: '10px',
          background: 'white',
          padding: '12px',
          borderRadius: '8px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
          zIndex: 9999,
          minWidth: '200px',
        }}>
          <div style={{ marginBottom: '8px', fontWeight: 'bold', fontSize: '14px' }}>
            🛠️ 调试面板
          </div>
          <label style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px', 
            fontSize: '13px',
            cursor: 'pointer'
          }}>
            <input
              type="checkbox"
              checked={useMockStreaming}
              onChange={(e) => setUseMockStreaming(e.target.checked)}
            />
            使用模拟流式响应
          </label>
          <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
            启用此选项测试前端流式显示逻辑
          </div>
        </div>
      )}

      <div className={`${styles.chatAreaWrapper} ${showInitialPromptLayout ? styles.chatAreaWrapperInitial : styles.chatAreaActive}`}>
        {showInitialPromptLayout && (
          <div className={styles.initialPromptHeader}> <h3 className={styles.mainPromptText}>What would you like to get done, User?</h3> </div>
        )}
        <div className={`${styles.chatMessagesArea} ${showInitialPromptLayout ? styles.hiddenOnInitial : ''}`} ref={chatMessagesAreaRef}>
          {chatHistory.map((entry) => (
            <div key={entry.id || entry.timestamp} className={`${styles.chatMessage} ${entry.sender === 'user' ? styles.userMessage : styles.aiMessage}`}>
              <div className={`${styles.messageBubbleContent} ${entry.streaming ? styles.streaming : ''}`}>
                {((entry.files && entry.files.length > 0) || (entry.notes && entry.notes.length > 0)) && (
                  <MessageFileAttachments files={entry.files || []} notes={entry.notes || []} isAiMessage={entry.sender === 'ai'} />
                )}
                <p>
                  {entry.text}
                  {/* 流式输出光标 */}
                  {entry.streaming && (
                    <span className={styles.streamingCursor}>|</span>
                  )}
                </p>
                {/* 错误指示器 */}
                {entry.error && (
                  <div className={styles.errorIndicator}>
                    ❌ 消息发送失败
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
        <div className={`${styles.interactionArea} ${showInitialPromptLayout ? styles.interactionAreaInitial : ''}`}>
          {/* 动态渲染 Agent 按钮 */}
          <div className={styles.agentButtons}>
            {/* <<< 新增：内层包装器 (.agentButtonsWrapper) 负责按钮的 flex 排列 >>> */}
            <div className={styles.agentButtonsWrapper}>
              {loadingAgents ? <p>Loading agents...</p> : agents.map(agent => {
                const IconComponent = getIconComponent(agent.icon);
                const isActive = agent.id === activeAgentId;
                return (
                  <button
                    key={agent.id}
                    className={`${styles.agentButton} ${isActive ? styles.agentButtonActive : ''}`}
                    onClick={() => setActiveAgentId(agent.id)}
                    style={isActive ? { backgroundColor: agent.color, color: '#fff', borderColor: agent.color } : {}}
                  >
                    <span className={styles.agentIcon} style={{ color: isActive ? '#fff' : agent.color }}>
                      <IconComponent />
                    </span>
                    {agent.name}
                  </button>
                );
              })}
            </div>
          </div>
          <ChatInputInterface
            onSendMessage={handleSendMessage}
            showSaveButton={true}
            onSaveChatAsProject={handleOpenSaveModal}
            showDownloadButton={true}
            onDownloadChat={handleDownloadChat}
            showModelSelector={true}
            availableModels={availableModels}
            currentSelectedModelId={selectedModel}
            onModelChange={handleModelChange}
            showDeepSearchButton={true}
            isDeepSearchActive={isDeepSearchMode}
            onToggleDeepSearch={handleToggleDeepSearch}
            placeholderText="Type your message here... (Shift+Enter for new line)"
          />
        </div>
      </div>
      <SaveProjectModal isOpen={isSaveModalOpen} onClose={handleCloseSaveModal} onSave={actuallySaveProject} />
      {/* 在页面渲染中添加测试按钮（临时用于调试） */}
      {process.env.NODE_ENV === 'development' && (
        <button 
          onClick={testStreamingConnection}
          style={{
            position: 'fixed',
            top: '10px',
            right: '10px',
            background: '#4CAF50',
            color: 'white',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '4px',
            cursor: 'pointer',
            zIndex: 9999,
          }}
        >
          测试流式连接
        </button>
      )}
    </div>
  );
};
export default HomePage;