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


const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const numBytes = Number(bytes);
  if (isNaN(numBytes) || numBytes === 0) return '0 Bytes';
  const i = Math.floor(Math.log(numBytes) / Math.log(k));
  return parseFloat((numBytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

const simplifyFileForContext = f => ({ id: f.id, name: f.name, size: f.size, type: f.type, preview: f.preview, uploadedAt: f.uploadedAt });
const simplifyNoteForContext = n => ({ id: n.id, name: n.name, preview: n.preview, content: n.content, createdAt: n.createdAt });

const mockModelsDataFromHome = [ // Renamed to avoid conflict if ChatInputInterface has its own default
  { id: 'deepseek', name: 'DeepSeek' },
  { id: 'gpt4', name: 'GPT-4' },
];


const HomePage = () => {
  const { agents, loadingAgents } = useAgents(); // <<< 从 Context 获取 agents
  const [activeAgentId, setActiveAgentId] = useState(null); // <<< 现在用 ID 来跟踪激活的 agent
  const { openRightSidebarWithView, isRightSidebarOpen, rightSidebarView, closeRightSidebar } = useSidebar();
  const { addProject } = useProjects();
  const navigate = useNavigate();

  const [message, setMessage] = useState(''); // This is managed by ChatInputInterface now if passed as prop
  const [chatHistory, setChatHistory] = useState([]);
  const [activeAgent, setActiveAgent] = useState('general');

  const [currentChatFiles, setCurrentChatFiles] = useState([]);
  const [currentChatNotes, setCurrentChatNotes] = useState([]);

  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const chatMessagesAreaRef = useRef(null);

  // States for ChatInputInterface props
  const [selectedModel, setSelectedModel] = useState(mockModelsDataFromHome[0].id);
  const [isDeepSearchMode, setIsDeepSearchMode] = useState(false);

  useEffect(() => {
    if (chatMessagesAreaRef.current) {
      chatMessagesAreaRef.current.scrollTop = chatMessagesAreaRef.current.scrollHeight;
    }
  }, [chatHistory]);

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
      const generalAgent = agents.find(a => a.name === 'General');
      setActiveAgentId(generalAgent ? generalAgent.id : agents[0].id);
    }
  }, [agents, loadingAgents, activeAgentId]);

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

  const handleSendMessage = (messageText, filesFromInput) => {
    const activeAgentObject = agents.find(a => a.id === activeAgentId);
    if (!activeAgentObject) {
      alert("Error: Active agent not found!");
      return;
    }
    const activeAgentName = activeAgentObject ? activeAgentObject.name : 'general';
    const filesAttachedToMessage = [...filesFromInput]; // These have rawFile

    const getAiReply = async () => {
      if (activeAgentObject.apiProvider === 'custom') {
        // --- 调用自定义 API ---
        console.log("Using custom API:", activeAgentObject.apiEndpoint);
        try {
          const response = await fetch(activeAgentObject.apiEndpoint, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${activeAgentObject.apiKey}` // 常见的认证方式
            },
            body: JSON.stringify({
              model: activeAgentObject.modelName,
              // 构建符合目标 API 的消息格式
              messages: [
                { role: 'system', content: activeAgentObject.systemPrompt },
                // ... (将 chatHistory 转换为 API 需要的格式) ...
                { role: 'user', content: messageText },
              ],
              // ... (其他参数如 temperature)
            })
          });
          if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
          }
          const data = await response.json();
          // 从 data 中解析出 AI 的回复文本
          // 例如, 对于 OpenAI API: data.choices[0].message.content
          return data.choices[0].message.content;
        } catch (error) {
          console.error("Custom API call failed:", error);
          return `Error calling custom API: ${error.message}`;
        }
      } else {
        // --- 调用默认模型服务 (目前还是模拟) ---
        console.log("Using default model service for agent:", activeAgentObject.name);
        return new Promise(resolve => {
          setTimeout(() => {
            resolve(`AI mock response to "${messageText.substring(0, 30)}..." (Agent: ${activeAgentObject.name})`);
          }, 800);
        });
      }
    };

    const newUserMessage = {
      sender: 'user', text: messageText,
      files: filesAttachedToMessage.map(f => ({ id: f.id, name: f.name, size: f.size, type: f.type, uploadedAt: f.uploadedAt, preview: f.preview })),
      timestamp: new Date().toISOString()
    };
    setChatHistory(prev => [...prev, newUserMessage]);

    if (filesFromInput.length > 0) {
      // 对比 currentChatFiles，只添加真正新的文件
      const newFilesToAddToContext = filesFromInput.filter(
        newFile => !currentChatFiles.some(
          existingFile => existingFile.name === newFile.name && existingFile.size === newFile.size
        )
      );

      // 如果有真正新的文件，才更新全局列表
      if (newFilesToAddToContext.length > 0) {
        console.log("HomePage: Adding new unique files to chat context:", newFilesToAddToContext.map(f => f.name));
        setCurrentChatFiles(prev => {
          const combined = [...prev, ...newFilesToAddToContext];
          // 虽然我们已经过滤了，但用 Map 再次去重更保险
          return Array.from(new Map(combined.map(f => [f.id, f])).values());
        });
        // 之后的 useEffect 会负责将更新后的 currentChatFiles 推送到 RightSidebar
      } else {
        console.log("HomePage: All attached files already exist in chat context. No update to context needed.");
      }
    }

    // 获取并显示 AI 回复
    getAiReply().then(aiText => {
      const aiResponse = {
        id: `msg-ai-${Date.now()}`,
        sender: 'ai',
        text: aiText,
        timestamp: new Date().toISOString(),
        files: []
      };
      setChatHistory(prev => [...prev, aiResponse]);
    });
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

  return (
    <div className={styles.homePageLayout}>
      <div className={`${styles.chatAreaWrapper} ${showInitialPromptLayout ? styles.chatAreaWrapperInitial : styles.chatAreaActive}`}>
        {showInitialPromptLayout && (
          <div className={styles.initialPromptHeader}> <h3 className={styles.mainPromptText}>What would you like to get done, User?</h3> </div>
        )}
        <div className={`${styles.chatMessagesArea} ${showInitialPromptLayout ? styles.hiddenOnInitial : ''}`} ref={chatMessagesAreaRef}>
          {chatHistory.map((entry) => (
            // 使用与 ProjectPage 完全相同的 JSX 结构和类名
            <div key={entry.id || entry.timestamp} className={`${styles.chatMessage} ${entry.sender === 'user' ? styles.userMessage : styles.aiMessage}`}>
              <div className={styles.messageBubbleContent}> {/* 包装器用于气泡样式 */}
                {(entry.files && entry.files.length > 0) && (
                  <MessageFileAttachments files={entry.files} isAiMessage={entry.sender === 'ai'} />
                )}
                <p>{entry.text}</p>
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
            availableModels={mockModelsDataFromHome}
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
    </div>
  );
};
export default HomePage;