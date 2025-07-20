// src/pages/ProjectPage.js
import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import styles from './ProjectPage.module.css';
import { useSidebar } from '../contexts/SidebarContext';
import { useProjects } from '../contexts/ProjectContext';
import { useAgents, getIconComponent } from '../contexts/AgentContext'; // <<< 导入 useAgents 和 getIconComponent
import {
  FiMessageSquare, FiLayout, FiFileText, FiEdit3,
  FiBriefcase, FiEdit2, FiTerminal, FiSend, FiX, // For Chat & Input
  FiShare2, FiUsers, FiUser, FiGlobe, // 添加分享相关图标
  // FiBriefcase, FiTerminal, FiEdit2 in getIconComponent will be resolved
} from 'react-icons/fi';
import MessageFileAttachments from '../components/chat/MessageFileAttachments';
import ChatInputInterface from '../components/chat/ChatInputInterface';
import ShareProjectModal from '../components/modals/ShareProjectModal';
import apiService from '../services/apiService';

const agentConfigFromHomePage = {
  general: { icon: <FiMessageSquare />, color: '#4CAF50' },
  professor: { icon: <FiBriefcase />, color: '#FF9800' },
  copywriter: { icon: <FiEdit2 />, color: '#9C27B0' },
  coder: { icon: <FiTerminal />, color: '#00BCD4' }
};

// Helper function (if not globally available, define or import it)
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

// Models will be loaded from backend API


// --- ProjectDashboardView Sub-component ---
const ProjectDashboardView = ({ projectData, onStartChat }) => {
  const [showAllSessions, setShowAllSessions] = useState(false);
  const projectSessions = projectData.sessions || [];
  const displayedSessions = showAllSessions ? projectSessions : projectSessions.slice(0, 5);
  const filesPreviewCount = 3;
  const notesPreviewCount = 3;

  return (
    <div className={styles.dashboardView}>
      <div className={`${styles.dashboardSection} ${styles.aiSummarySection}`}>
        <h4>AI Project Insights & Summary</h4>
        <p className={styles.aiSummaryPlaceholder}>
          <em>AI is analyzing project "{projectData.name}"... Key insights will appear here.</em><br />
          Based on current files, notes, and chat history, the main themes identified are X, Y, and Z.
          Consider exploring A or B next to deepen your understanding.
        </p>
      </div>

      {projectSessions.length > 0 && (
        <div className={`${styles.dashboardSection} ${styles.chatHistoryHighlightsSection}`}>
          <div className={styles.sectionHeaderWithAction}>
            <h4><FiMessageSquare /> Recent Chat Sessions</h4>
            {projectSessions.length > 5 && (
              <button onClick={() => setShowAllSessions(!showAllSessions)} className={styles.moreButton}>
                {showAllSessions ? 'Show Less' : `More (${projectSessions.length - displayedSessions.length})`}
              </button>
            )}
          </div>
          <div className={styles.chatHistoryCardsContainer}>
            {displayedSessions.map((session) => (
              <div key={session.sessionId} className={styles.chatHistoryCard}>
                <h5 className={styles.sessionSummaryTitle}>{session.aiSummary || "Session Summary"}</h5>
                <p className={styles.sessionTimeframe}>
                  {new Date(session.startTime).toLocaleString()}
                  {session.endTime && ` - ${new Date(session.endTime).toLocaleString()}`}
                </p>
                <div className={styles.sessionMeta}>
                  <span>{session.messages?.length || 0} messages</span>
                  {session.sessionFiles && session.sessionFiles.length > 0 && (
                    <span>· {session.sessionFiles.length} file(s) discussed</span>
                  )}
                </div>
                <button
                  className={styles.viewSessionChatButton}
                  onClick={() => onStartChat(session.sessionId)}
                >
                  View Full Conversation
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className={styles.filesAndNotesContainer}>
        <div className={`${styles.dashboardSection} ${styles.resourceSection}`}>
          <div className={styles.sectionHeaderWithAction}>
            <h4><FiFileText /> Files ({projectData.files?.length || 0})</h4>
          </div>
          {projectData.files && projectData.files.length > 0 ? (
            <ul className={styles.summaryList}>
              {(projectData.files.slice(0, filesPreviewCount)).map(file => (
                <li key={file.id} className={styles.summaryItem}>
                  {/* <<< 用 Link 包裹文件名 >>> */}
                  <Link to={`/neurocore/project/${projectData.id}/file/${file.id}`}>
                    {file.name}
                  </Link>
                </li>
              ))}
              {projectData.files.length > filesPreviewCount && <li className={styles.moreListItem}>... and {projectData.files.length - filesPreviewCount} more files.</li>}
            </ul>
          ) : <p className={styles.emptyResourceText}>No files in this project yet.</p>}
        </div>
        <div className={`${styles.dashboardSection} ${styles.resourceSection}`}>
          <div className={styles.sectionHeaderWithAction}>
            <h4><FiEdit3 /> Notes ({projectData.notes?.length || 0})</h4>
          </div>
          {projectData.notes && projectData.notes.length > 0 ? (
            <ul className={styles.summaryList}>
              {(projectData.notes.slice(0, notesPreviewCount)).map(note => (
                <li key={note.id} className={styles.summaryItem}>
                  <strong>{note.name}</strong>: <em>{note.preview}</em>
                </li>
              ))}
              {projectData.notes.length > notesPreviewCount && <li className={styles.moreListItem}>... and {projectData.notes.length - notesPreviewCount} more notes.</li>}
            </ul>
          ) : <p className={styles.emptyResourceText}>No notes in this project yet.</p>}
        </div>
      </div>
    </div>
  );
};

// --- ProjectChatView Sub-component ---
const ProjectChatView = ({ projectData, activeSessionId, onSendMessageToProject, availableModels = [] }) => {
  const chatMessagesViewRef = useRef(null);
  let messagesToShow = [];
  let sessionTitle = `New Chat for "${projectData.name}"`;

  // --- 从 AgentContext 获取 Agents ---
  const { agents, loadingAgents } = useAgents();

  // --- States specific to this Chat View ---
  const [projectChatActiveAgentId, setProjectChatActiveAgentId] = useState(null);
  const [projectChatSelectedModel, setProjectChatSelectedModel] = useState('openrouter/auto');
  const [projectChatIsDeepSearch, setProjectChatIsDeepSearch] = useState(false);

  // 当 agents 加载完成后，设置默认的 active agent
  useEffect(() => {
    if (!loadingAgents && agents.length > 0 && !projectChatActiveAgentId) {
      const generalAgent = agents.find(a => a.name === 'General');
      setProjectChatActiveAgentId(generalAgent ? generalAgent.id : agents[0].id);
    }
  }, [agents, loadingAgents, projectChatActiveAgentId]);

  if (activeSessionId && projectData.sessions) {
    const activeSession = projectData.sessions.find(s => s.sessionId === activeSessionId);
    if (activeSession) {
      messagesToShow = activeSession.messages || [];
      sessionTitle = activeSession.aiSummary || `Chat Session (${new Date(activeSession.startTime).toLocaleDateString()})`;
    }
  }

  useEffect(() => {
    if (chatMessagesViewRef.current) {
      chatMessagesViewRef.current.scrollTop = chatMessagesViewRef.current.scrollHeight;
    }
  }, [messagesToShow]);

  const handleSendMessageViaInterface = (messageText, filesFromInput, notesFromInput = []) => {
    // 传递整个 activeAgentObject，以便上层可以访问所有API配置
    onSendMessageToProject(messageText, filesFromInput, notesFromInput, activeSessionId, projectChatActiveAgentId, projectChatSelectedModel);
  };

  const handleProjectChatModelChange = (e) => setProjectChatSelectedModel(e.target.value);
  const handleProjectChatToggleDeepSearch = () => setProjectChatIsDeepSearch(!projectChatIsDeepSearch);

  // 判断是否显示初始居中布局和提示文本
  const showInitialChatLayout = messagesToShow.length === 0 && !activeSessionId; // 新会话且无消息
  const chatViewWrapperClass = `${styles.chatViewWrapper} ${showInitialChatLayout ? styles.chatViewWrapperInitial : styles.chatViewWrapperActive}`;

  return (
    <div className={styles.chatView}>
      {/* 移除了 chatViewHeader */}
      <div className={chatViewWrapperClass}>
        {/* 初始提示文本，类似于 HomePage */}
        {showInitialChatLayout && (
          <div className={styles.projectChatInitialPromptHeader}>
            <h3 className={styles.projectChatMainPromptText}>
              Start a new chat session for project "{projectData.name}". What would you like to discuss?
            </h3>
          </div>
        )}

        {/* 消息显示区，使用与 HomePage 相同的气泡样式 */}
        <div className={`${styles.projectChatMessagesArea} ${showInitialChatLayout ? styles.hiddenOnInitial : ''}`} ref={chatMessagesViewRef}>
          {messagesToShow.length > 0 ? (
            messagesToShow.map((entry, index) => (
              <div key={`${entry.timestamp}-${index}`} className={`${styles.chatMessage} ${entry.sender === 'user' ? styles.userMessage : styles.aiMessage}`}>
                <div className={styles.messageBubbleContent}> {/* 包装器用于气泡样式 */}
                  {((entry.files && entry.files.length > 0) || (entry.notes && entry.notes.length > 0)) && (
                    <MessageFileAttachments files={entry.files || []} notes={entry.notes || []} isAiMessage={entry.sender === 'ai'} />
                  )}
                  <p>{entry.text}</p>
                </div>
              </div>
            ))
          ) : (
            !showInitialChatLayout && <p className={styles.emptyChatMessage}>This chat session is empty. Start by typing a message below.</p>
          )}
        </div>

        {/* 输入交互区 */}
        <div className={`${styles.projectInteractionArea} ${showInitialChatLayout ? styles.projectInteractionAreaInitial : ''}`}>
          {/* --- 核心修改区域：为 Agent 按钮添加双层容器 --- */}
          {/* 外层容器 (.projectAgentButtons) */}
          <div className={styles.projectAgentButtons}>
            {/* 内层包装器 (.agentButtonsWrapper) */}
            <div className={styles.agentButtonsWrapper}>
              {loadingAgents ? <p>Loading agents...</p> : agents.map(agent => {
                const IconComponent = getIconComponent(agent.icon);
                const isActive = agent.id === projectChatActiveAgentId;
                return (
                  <button
                    key={agent.id}
                    className={`${styles.agentButton} ${isActive ? styles.agentButtonActive : ''}`}
                    onClick={() => setProjectChatActiveAgentId(agent.id)}
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
            onSendMessage={handleSendMessageViaInterface} // handleSendMessageViaInterface 会调用 onSendMessageToProject
            existingFilesForDedupe={projectData.files || []} // <<< 传递当前项目的文件列表
            showSaveButton={false} // 明确不在项目聊天中显示"保存为项目"
            showDownloadButton={false} // 可以保留下载功能，但其实现可能不同
            // onDownloadChat={handleProjectChatDownload} // 需要实现项目聊天下载逻辑
            showModelSelector={true}
            availableModels={availableModels}
            currentSelectedModelId={projectChatSelectedModel}
            onModelChange={handleProjectChatModelChange}
            showDeepSearchButton={true}
            isDeepSearchActive={projectChatIsDeepSearch}
            onToggleDeepSearch={handleProjectChatToggleDeepSearch}
            placeholderText={`Message in "${projectData.name}" (Session: ${sessionTitle.substring(0, 15)})...`}
          />
        </div>
      </div>
    </div>
  );
};


// --- ProjectPage Main Component ---
const ProjectPage = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { openRightSidebarWithView, isRightSidebarOpen, rightSidebarView, closeRightSidebar } = useSidebar();
  const { projects, getProjectById, updateProject, updateProjectSharing, loadProjectDocuments, loadingProjects: projectsContextLoading } = useProjects();
  const { agents } = useAgents();
  const [projectData, setProjectData] = useState(null); // Local SSoT for this page after fetching
  const [pageLoading, setPageLoading] = useState(true);
  const [currentView, setCurrentView] = useState('dashboard');
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [conversationId, setConversationId] = useState(null); // 后端对话ID
  const [availableModels, setAvailableModels] = useState([]);


  // Effect to load available models
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await apiService.chat.getAvailableModels();
        const chatModels = response.models.filter(model => model.type === 'chat');
        setAvailableModels(chatModels.map(model => ({
          id: model.id,
          name: model.name
        })));
      } catch (error) {
        console.error('Failed to fetch models:', error);
        setAvailableModels([
          { id: 'openrouter/auto', name: 'Auto (自动选择最佳模型)' }
        ]);
      }
    };
    
    fetchModels();
  }, []);

  // Effect 1: 当 projectId 或全局 projects 列表变化时，更新本地 projectData
  useEffect(() => {
    console.log(`ProjectPage Effect 1 (Set Local ProjectData): Fired. ProjectId: ${projectId}, ContextLoading: ${projectsContextLoading}`);
    if (projectsContextLoading) {
      if (!pageLoading) setPageLoading(true);
      return;
    }
    const foundProject = getProjectById(projectId); // 从最新的 projects 列表中获取
    if (foundProject) {
      // 只有当找到的项目与当前 projectData 引用不同时才更新，避免不必要的渲染
      // 或者当内容不同时（更安全，但 JSON.stringify 有性能开销）
      if (JSON.stringify(foundProject) !== JSON.stringify(projectData)) {
        console.log("ProjectPage Effect 1: Setting local projectData from context for:", projectId);
        setProjectData(foundProject);
      }
      if (pageLoading) setPageLoading(false);
    } else {
      if (!projectsContextLoading) { // 确保不是因为 context 还在加载
        console.warn(`ProjectPage Effect 1: Project ${projectId} not found in context. Navigating.`);
        navigate('/neurocore', { replace: true });
        if (isRightSidebarOpen) closeRightSidebar();
        if (pageLoading) setPageLoading(false);
      }
    }
  }, [projectId, projects, getProjectById, projectsContextLoading, navigate, isRightSidebarOpen, closeRightSidebar, pageLoading, projectData]);
  // 依赖项包含 projects，当 context 中的项目列表更新时，这个 effect 会重新获取 projectData


  // Callbacks for RightSidebar - 这些回调现在直接操作最新的 projectData (通过 getProjectById)
  const handleUpdateProjectFiles = useCallback((updatedSimplifiedFiles) => {
    if (!projectId || !updateProject || !getProjectById) return;
    const currentProjectFromContext = getProjectById(projectId); // 获取最新版本
    if (!currentProjectFromContext) return;

    const newFullFilesList = updatedSimplifiedFiles.map(sf => {
      const existing = currentProjectFromContext.files?.find(f => f.id === sf.id);
      return existing ? { ...existing, ...sf, rawFile: existing.rawFile } : { ...sf, rawFile: null };
    });
    // 更新 ProjectContext，这会触发上面的 Effect 1 重新设置 projectData
    updateProject(projectId, { ...currentProjectFromContext, files: newFullFilesList });
  }, [projectId, updateProject, getProjectById]);

  const handleUpdateProjectNotes = useCallback((updatedSimplifiedNotes) => {
    if (!projectId || !updateProject || !getProjectById) return;
    const currentProjectFromContext = getProjectById(projectId);
    if (!currentProjectFromContext) return;

    const newFullNotesList = updatedSimplifiedNotes.map(sn => {
      const existing = currentProjectFromContext.notes?.find(n => n.id === sn.id);
      return existing ? { ...existing, ...sn } : { ...sn, content: sn.content || sn.preview };
    });
    updateProject(projectId, { ...currentProjectFromContext, notes: newFullNotesList });
  }, [projectId, updateProject, getProjectById]);


  // Effect 2: 当 projectData (本地的、已与context同步的最新版本) 或侧边栏状态变化时，更新 RightSidebar 显示
  useEffect(() => {
    console.log(`ProjectPage Effect 2 (Update Sidebar Display): Fired. ProjectData Name: ${projectData?.name}, PageLoading: ${pageLoading}, SidebarOpen: ${isRightSidebarOpen}`);
    if (!projectData || pageLoading || projectsContextLoading) {
      // 如果 projectData 还没准备好，或者页面还在加载，或者 context 还在加载，则不更新侧边栏
      // 以免传递 null 或不完整的数据给侧边栏。
      return;
    }

    const sidebarDataPayload = {
      projectName: projectData.name, projectId: projectData.id,
      files: (projectData.files || []).map(simplifyFileForContext),
      notes: (projectData.notes || []).map(simplifyNoteForContext),
      onUpdateProjectFiles: handleUpdateProjectFiles, // 传递稳定的回调
      onUpdateProjectNotes: handleUpdateProjectNotes, // 传递稳定的回调
    };

    if (isRightSidebarOpen) {
      // 只要侧边栏是打开的，就用最新的 projectData (已通过Effect 1同步) 来刷新它
      // 或者更精确：只有当类型/ID不对，或内容（files/notes数量或内容）确实变了才更新
      let needsUpdate = false;
      if (rightSidebarView?.type !== 'PROJECT_DETAILS' || rightSidebarView?.data?.projectId !== projectData.id) {
        needsUpdate = true;
      } else {
        if (JSON.stringify(rightSidebarView.data?.files || []) !== JSON.stringify(sidebarDataPayload.files) ||
          JSON.stringify(rightSidebarView.data?.notes || []) !== JSON.stringify(sidebarDataPayload.notes)
          // 回调引用通常是稳定的，可以不比较，除非它们的依赖项变化导致它们重新创建
          // || rightSidebarView.data.onUpdateProjectFiles !== handleUpdateProjectFiles
          // || rightSidebarView.data.onUpdateProjectNotes !== handleUpdateProjectNotes
        ) {
          needsUpdate = true;
        }
      }

      if (needsUpdate) {
        console.log(`ProjectPage Effect 2: Pushing updated project data to RightSidebar for ${projectData.name}. Files: ${sidebarDataPayload.files.length}`);
        openRightSidebarWithView({
          type: 'PROJECT_DETAILS',
          data: sidebarDataPayload,
          activeTab: rightSidebarView?.activeTab // 保持当前tab，不自动切换
        });
      } else {
        console.log("ProjectPage Effect 2: Sidebar open and data appears current, no forced update.");
      }
    }
  }, [
    projectData, // 主驱动：当本地 projectData 更新后，此 effect 执行
    isRightSidebarOpen, rightSidebarView, // 侧边栏状态
    openRightSidebarWithView, // stable
    handleUpdateProjectFiles, handleUpdateProjectNotes, // stable callbacks
    pageLoading, projectsContextLoading // guards
  ]);


  // 辅助函数：上传文件到后端
  const uploadFileToBackend = async (file, spaceId) => {
    try {
      const uploadedDoc = await apiService.document.uploadDocument(
        spaceId,
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

  const handleSendMessageToProject = async (messageText, attachedFiles, attachedNotes = [], currentActiveSessionId, agentId, selectedModel = 'openrouter/auto') => {
    const activeAgentObject = agents.find(a => a.id === agentId);
    if (!projectData || !activeAgentObject) {
      console.error("Missing data for sending message: projectData or activeAgentObject");
      return;
    }
    
    try {
      // 如果还没有创建对话，先创建一个
      let currentConversationId = conversationId;
      if (!currentConversationId) {
        const conversationData = {
          title: messageText.substring(0, 50) + (messageText.length > 50 ? '...' : ''),
          mode: 'chat',
          space_id: parseInt(projectData.spaceId || projectData.id) // 关联到当前 Space
        };
        
        const newConversation = await apiService.chat.createConversation(conversationData);
        currentConversationId = newConversation.id;
        setConversationId(currentConversationId);
      }
      
      // 准备文档 ID 列表
      const documentIds = [];
      if (attachedFiles.length > 0) {
        for (const file of attachedFiles) {
          if (file.id && !isNaN(parseInt(file.id))) {
            documentIds.push(parseInt(file.id));
          } else if (file.rawFile) {
            // 如果是新文件，先上传
            const uploadedDoc = await uploadFileToBackend(file.rawFile, parseInt(projectData.spaceId || projectData.id));
            if (uploadedDoc && uploadedDoc.id) {
              documentIds.push(uploadedDoc.id);
            }
          }
        }
      }
      
      // 获取聊天历史（从当前会话）
      let chatHistory = [];
      if (currentActiveSessionId && projectData.sessions) {
        const activeSession = projectData.sessions.find(s => s.sessionId === currentActiveSessionId);
        if (activeSession && activeSession.messages) {
          chatHistory = activeSession.messages;
        }
      }
      
      // 构建消息
      const messages = [
        { role: 'system', content: activeAgentObject.systemPrompt || '你是一个有帮助的助手。' },
        ...chatHistory.map(msg => ({
          role: msg.sender === 'user' ? 'user' : 'assistant',
          content: msg.text
        })),
        { role: 'user', content: messageText }
      ];
      
      // 调用聊天 API
      const response = await apiService.chat.createChatCompletion({
        model: selectedModel,
        messages: messages,
        temperature: 0.7,
        stream: false,
        conversation_id: currentConversationId,
        document_ids: documentIds.length > 0 ? documentIds : undefined
      });
      
      const aiReplyText = response.choices[0].message.content;

      // 更新本地状态以显示消息
      const newUserMessage = {
        sender: 'user', 
        text: messageText,
        files: attachedFiles.map(f => ({ 
          id: f.id, 
          name: f.name, 
          size: f.size, 
          type: f.type, 
          uploadedAt: f.uploadedAt, 
          preview: f.preview,
          isAiGenerated: f.isAiGenerated,
          aiAgent: f.aiAgent
        })),
        notes: attachedNotes.map(n => ({ 
          id: n.id, 
          name: n.name, 
          content: n.content, 
          createdAt: n.createdAt, 
          preview: n.preview,
          isAiGenerated: n.isAiGenerated,
          aiAgent: n.aiAgent
        })),
        timestamp: new Date().toISOString(),
      };
      
      const aiResponse = {
        id: `msg-ai-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        sender: 'ai', 
        text: aiReplyText, 
        timestamp: new Date().toISOString(), 
        files: []
      };

      // 更新本地会话状态
      let targetSessionId = currentActiveSessionId;
      let updatedSessions = projectData.sessions ? [...projectData.sessions] : [];
      let sessionModifiedOrCreated = false;
      let newSessionWasCreated = false;

    if (targetSessionId) {
      const sessionIndex = updatedSessions.findIndex(s => s.sessionId === targetSessionId);
      if (sessionIndex !== -1) {
        const sessionToUpdate = { ...updatedSessions[sessionIndex] };
        sessionToUpdate.messages = [...(sessionToUpdate.messages || []), newUserMessage];
        sessionToUpdate.endTime = new Date().toISOString();
        const newSessionFiles = attachedFiles.map(f => ({ 
          id: f.id, 
          name: f.name, 
          type: f.type, 
          size: f.size, 
          uploadedAt: f.uploadedAt,
          isAiGenerated: f.isAiGenerated,
          aiAgent: f.aiAgent
        }));
        sessionToUpdate.sessionFiles = Array.from(new Map([...(sessionToUpdate.sessionFiles || []), ...newSessionFiles].map(f => [f.id, f])).values());
        // 新增：处理会话中的笔记
        const newSessionNotes = attachedNotes.map(n => ({ 
          id: n.id, 
          name: n.name, 
          content: n.content, 
          createdAt: n.createdAt,
          isAiGenerated: n.isAiGenerated,
          aiAgent: n.aiAgent
        }));
        sessionToUpdate.sessionNotes = Array.from(new Map([...(sessionToUpdate.sessionNotes || []), ...newSessionNotes].map(n => [n.id, n])).values());
        updatedSessions[sessionIndex] = sessionToUpdate;
        sessionModifiedOrCreated = true;
      } else { targetSessionId = null; }
    }

    if (!targetSessionId) {
      targetSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
      const newSession = {
        sessionId: targetSessionId, startTime: new Date().toISOString(), messages: [newUserMessage],
        aiSummary: `Chat started ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}`, // Better placeholder
        sessionFiles: attachedFiles.map(f => ({ 
          id: f.id, 
          name: f.name, 
          type: f.type, 
          size: f.size, 
          uploadedAt: f.uploadedAt,
          isAiGenerated: f.isAiGenerated,
          aiAgent: f.aiAgent
        })),
        sessionNotes: attachedNotes.map(n => ({ 
          id: n.id, 
          name: n.name, 
          content: n.content, 
          createdAt: n.createdAt,
          isAiGenerated: n.isAiGenerated,
          aiAgent: n.aiAgent
        })),
        endTime: new Date().toISOString(),
      };
      updatedSessions.push(newSession);
      setActiveSessionId(targetSessionId);
      sessionModifiedOrCreated = true;
      newSessionWasCreated = true;
    }

    if (sessionModifiedOrCreated) {
      // --- 调用 AI 的逻辑 ---
      const getAiReply = async () => {
        if (activeAgentObject.apiProvider === 'custom') {
          // --- 调用自定义 API ---
          try {
            const response = await fetch(activeAgentObject.apiEndpoint, { /* ... (fetch options) ... */ });
            if (!response.ok) throw new Error(`API Error: ${response.status}`);
            const data = await response.json();
            return data.choices[0].message.content; // Adjust based on API response structure
          } catch (error) {
            console.error("Custom API call failed:", error);
            return `Error calling custom API: ${error.message}`;
          }
        } else {
          // --- 调用默认模型服务 (模拟) ---
          return new Promise(resolve => {
            setTimeout(() => {
              resolve(`AI mock response to "${messageText.substring(0, 20)}..." (using ${activeAgentObject.name} agent for project: ${projectData.name})`);
            }, 800);
          });
        }
      };

      // 等待 AI 回复
      const aiText = await getAiReply();

      const aiResponse = {
        id: `msg-ai-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        sender: 'ai', text: aiText, timestamp: new Date().toISOString(), files: []
      };

      const finalSessionIndex = updatedSessions.findIndex(s => s.sessionId === targetSessionId);
      if (finalSessionIndex !== -1) {
        updatedSessions[finalSessionIndex].messages.push(aiResponse);
        updatedSessions[finalSessionIndex].endTime = new Date().toISOString();
      }
      
      // 新增：模拟AI生成文件或笔记
      const shouldGenerateFile = Math.random() > 0.5; // 50%概率生成文件
      const shouldGenerateNote = Math.random() > 0.7; // 30%概率生成笔记
      
      let updatedProjectFiles = [...(projectData.files || [])];
      let updatedProjectNotes = [...(projectData.notes || [])];
      let filesWereAddedToProject = false; // 标志位，判断是否需要更新项目
      let notesWereAddedToProject = false; // 标志位，判断是否需要更新项目

      if (attachedFiles && attachedFiles.length > 0) {
        const newFilesToAddToProject = attachedFiles.filter(
          newFile => !updatedProjectFiles.some(
            existingFile => existingFile.name === newFile.name && existingFile.size === newFile.size
          )
        );

        if (newFilesToAddToProject.length > 0) {
          console.log("ProjectPage: Adding new unique files to project's main file list:", newFilesToAddToProject.map(f => f.name));
          const newSimplifiedFiles = newFilesToAddToProject.map(simplifyFileForContext); // 使用简化版
          updatedProjectFiles = [...updatedProjectFiles, ...newSimplifiedFiles];
          filesWereAddedToProject = true;
        } else {
          console.log("ProjectPage: All attached files already exist in the project. No update to project's file list needed.");
        }
      }

      // 新增：处理AI生成的文件
      if (shouldGenerateFile) {
        const aiGeneratedFile = {
          id: `ai-file-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
          name: `AI Generated File ${new Date().toLocaleTimeString()}`,
          size: Math.floor(Math.random() * 1000000) + 1000, // 1KB to 1MB
          type: 'application/pdf',
          uploadedAt: new Date().toISOString(),
          preview: 'AI generated content',
          isAiGenerated: true, // 标记为AI生成
          aiAgent: activeAgentObject.name
        };
        
        const simplifiedAiFile = simplifyFileForContext(aiGeneratedFile);
        updatedProjectFiles = [...updatedProjectFiles, simplifiedAiFile];
        filesWereAddedToProject = true;
        
        console.log("AI generated file for project:", aiGeneratedFile.name);
      }
      
      // 新增：处理AI生成的笔记
      if (shouldGenerateNote) {
        const aiGeneratedNote = {
          id: `ai-note-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
          name: `AI Generated Note ${new Date().toLocaleTimeString()}`,
          content: `AI generated note based on: "${messageText.substring(0, 50)}..."`,
          preview: `AI generated note based on: "${messageText.substring(0, 30)}..."`,
          createdAt: new Date().toISOString(),
          isAiGenerated: true, // 标记为AI生成
          aiAgent: activeAgentObject.name
        };
        
        const simplifiedAiNote = simplifyNoteForContext(aiGeneratedNote);
        updatedProjectNotes = [...updatedProjectNotes, simplifiedAiNote];
        notesWereAddedToProject = true;
        
        console.log("AI generated note for project:", aiGeneratedNote.name);
      }

      // 只有在会话被修改或有新文件/笔记添加到项目时才更新
      if (sessionModifiedOrCreated || filesWereAddedToProject || notesWereAddedToProject) {
        const updatedProjectData = {
          ...projectData,
          sessions: updatedSessions,
          files: updatedProjectFiles,
          notes: updatedProjectNotes,
        };
        updateProject(projectData.id, updatedProjectData);
      }
    }
    } catch (error) {
      console.error('Error sending message:', error);
      alert(`发送消息失败: ${error.message}`);
    }
  };

  const handleStartChatView = (sessionId = null) => { setActiveSessionId(sessionId); setCurrentView('chat'); };
  const handleGoBackToDashboard = () => { setCurrentView('dashboard'); setActiveSessionId(null); };

  const handleShareProject = () => {
    setIsShareModalOpen(true);
  };

  const handleCloseShareModal = () => {
    setIsShareModalOpen(false);
  };

  const handleUpdateSharing = (sharingData) => {
    if (projectId && updateProjectSharing) {
      updateProjectSharing(projectId, sharingData);
    }
  };

  const getShareIcon = (sharing) => {
    if (!sharing || !sharing.isShared) {
      return <FiUser />;
    }
    switch (sharing.shareLevel) {
      case 'organization':
        return <FiUsers />;
      case 'public':
        return <FiGlobe />;
      default:
        return <FiShare2 />;
    }
  };

  const getShareTooltip = (sharing) => {
    if (!sharing || !sharing.isShared) {
      return 'Private project';
    }
    switch (sharing.shareLevel) {
      case 'organization':
        return 'Shared with organization';
      case 'public':
        return 'Public project';
      default:
        return 'Shared with specific users';
    }
  };

  if (pageLoading || projectsContextLoading) { return <div className={styles.loadingState}>Loading project data...</div>; }
  if (!projectData) { return <div className={styles.errorState}>Project not found.</div>; }

  const isProjectSidebarOpen = isRightSidebarOpen && rightSidebarView?.type === 'PROJECT_DETAILS' && rightSidebarView?.data?.projectId === projectId;

  return (
    <div className={styles.projectPage}>
      <div className={styles.mainContentArea}>
        <div className={styles.projectHeader}>
          <div className={styles.projectTitleSection}>
            <h2>{projectData.name}</h2>
            <button 
              onClick={handleShareProject}
              className={styles.shareButton}
              title={getShareTooltip(projectData.sharing)}
            >
              {getShareIcon(projectData.sharing)}
            </button>
          </div>
          <div className={styles.viewToggleButtons}>
            <button onClick={() => { setCurrentView('dashboard'); setActiveSessionId(null); }} className={`${styles.viewToggleButton} ${currentView === 'dashboard' ? styles.activeView : ''}`}> <FiLayout /> Dashboard </button>
            <button onClick={() => handleStartChatView(activeSessionId)} className={`${styles.viewToggleButton} ${currentView === 'chat' ? styles.activeView : ''}`}> <FiMessageSquare /> Chat </button>
          </div>
        </div>
        {currentView === 'dashboard' ? (
          <ProjectDashboardView projectData={projectData} onStartChat={handleStartChatView} />
        ) : (
          <ProjectChatView
            projectData={projectData}
            activeSessionId={activeSessionId}
            onGoBackToDashboard={handleGoBackToDashboard}
            onSendMessageToProject={handleSendMessageToProject}
            availableModels={availableModels}
          />
        )}
      </div>

      {/* Share Project Modal */}
      <ShareProjectModal
        isOpen={isShareModalOpen}
        onClose={handleCloseShareModal}
        projectData={projectData}
        onUpdateSharing={handleUpdateSharing}
      />
    </div>
  );
};
export default ProjectPage;