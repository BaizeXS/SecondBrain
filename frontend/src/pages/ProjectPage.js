// src/pages/ProjectPage.js
import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import styles from './ProjectPage.module.css';
import { useSidebar } from '../contexts/SidebarContext';
import { useProjects } from '../contexts/ProjectContext';
import { useAgents, getIconComponent } from '../contexts/AgentContext'; // <<< 导入 useAgents 和 getIconComponent
import { useChat } from '../contexts/ChatContext'; // 新增：导入useChat
import {
  FiMessageSquare, FiLayout, FiFileText, FiEdit3,
  FiBriefcase, FiEdit2, FiTerminal, FiSend, FiX, // For Chat & Input
  FiShare2, FiUsers, FiUser, FiGlobe, // 添加分享相关图标
  // FiBriefcase, FiTerminal, FiEdit2 in getIconComponent will be resolved
} from 'react-icons/fi';
import MessageFileAttachments from '../components/chat/MessageFileAttachments';
import ChatInputInterface from '../components/chat/ChatInputInterface';
import MarkdownRenderer from '../components/chat/MarkdownRenderer';
import ErrorBoundary from '../components/common/ErrorBoundary';
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
  aiAgent: f.aiAgent,
  rawFile: f.rawFile,
  url: f.url
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
const ProjectChatView = ({ projectData, activeSessionId, onGoBackToDashboard, onSendMessageToProject, availableModels = [], localChatSessions }) => {
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

  // 使用本地状态和项目状态的合并数据，优先使用本地状态
  if (activeSessionId) {
    const localSession = localChatSessions.find(s => s.sessionId === activeSessionId);
    const projectSession = projectData.sessions?.find(s => s.sessionId === activeSessionId);
    
    const activeSession = localSession || projectSession;
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
                  {entry.sender === 'ai' ? (
                    <>
                      {entry.streaming && !entry.text ? (
                        <div className={styles.thinkingIndicator}>
                          <span>正在思考</span>
                          <span className={styles.streamingCursor}>|</span>
                        </div>
                      ) : (
                        <ErrorBoundary
                          fallback={<p>{entry.text}</p>}
                        >
                          <MarkdownRenderer>
                            {entry.text}
                          </MarkdownRenderer>
                        </ErrorBoundary>
                      )}
                      {entry.streaming && entry.text && <span className={styles.streamingCursor}>|</span>}
                    </>
                  ) : (
                    <p>{entry.text}{entry.streaming && <span className={styles.streamingCursor}>|</span>}</p>
                  )}
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
  const { getDocumentIdsForAPI, getFilesNeedingUpload, clearChatSelections } = useChat(); // 新增：使用重新构建的ChatContext API
  const [projectData, setProjectData] = useState(null); // Local SSoT for this page after fetching
  const [pageLoading, setPageLoading] = useState(true);
  const [currentView, setCurrentView] = useState('dashboard');
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [conversationId, setConversationId] = useState(null); // 后端对话ID
  const [localChatSessions, setLocalChatSessions] = useState([]); // 本地聊天会话状态
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
      // 🔧 修复：保留简化文件中的rawFile，不要覆盖为null
      return existing 
        ? { ...existing, ...sf, rawFile: sf.rawFile || existing.rawFile }
        : { ...sf }; // 保持简化文件中的所有数据，包括rawFile
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
    projectData?.id, // 只监听项目ID变化，避免因内容更新导致循环
    projectData?.name, // 监听名称变化
    projectData?.files?.length, // 监听文件数量变化
    projectData?.notes?.length, // 监听笔记数量变化
    isRightSidebarOpen, rightSidebarView?.type, rightSidebarView?.data?.projectId, // 侧边栏状态
    openRightSidebarWithView, // stable
    handleUpdateProjectFiles, handleUpdateProjectNotes, // stable callbacks
    pageLoading, projectsContextLoading // guards
  ]);


  // 辅助函数：上传文件到后端
  const uploadFileToBackend = async (file, spaceId) => {
    try {
      console.log('Uploading file to space:', spaceId);
      const uploadedDoc = await apiService.document.uploadDocument(
        spaceId,
        file,
        file.name,
        ['chat-attachment']
      );
      console.log('File uploaded successfully:', uploadedDoc);
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
      // 1. 确保有对话 ID
      let currentConversationId = conversationId;
      if (!currentConversationId) {
        const conversationData = {
          title: messageText.substring(0, 50) + (messageText.length > 50 ? '...' : ''),
          mode: 'chat',
          space_id: parseInt(projectData.spaceId || projectData.id)
        };
        
        const newConversation = await apiService.chat.createConversation(conversationData);
        currentConversationId = newConversation.id;
        setConversationId(currentConversationId);
      }
      
      // 🆕 使用重新构建的ChatContext API进行文档处理
      console.log('🚀 ProjectPage: Using new ChatContext API for document handling');
      const documentIds = getDocumentIdsForAPI();
      const filesToUpload = getFilesNeedingUpload();
      
      console.log('📋 ProjectPage: Document IDs from ChatContext:', documentIds);
      console.log('📤 ProjectPage: Files needing upload:', filesToUpload.length);
      
      // 处理文件上传
      if (filesToUpload.length > 0 && projectData?.spaceId) {
        console.log('📤 ProjectPage: Uploading files...');
        for (const file of filesToUpload) {
          try {
            console.log(`📤 Uploading file: ${file.name}`);
            const uploadedDoc = await uploadFileToBackend(file.rawFile, parseInt(projectData.spaceId));
            if (uploadedDoc && uploadedDoc.id) {
              documentIds.push(uploadedDoc.id);
              console.log(`✅ File uploaded successfully, document ID: ${uploadedDoc.id}`);
            }
          } catch (uploadError) {
            console.error(`❌ Failed to upload file ${file.name}:`, uploadError);
            alert(`文件 "${file.name}" 上传失败: ${uploadError.message}`);
          }
        }
      }
      
      console.log('🎯 ProjectPage: Final document IDs for AI:', documentIds);
      
      // 3. 获取聊天历史
      let chatHistory = [];
      if (currentActiveSessionId && projectData.sessions) {
        const activeSession = projectData.sessions.find(s => s.sessionId === currentActiveSessionId);
        if (activeSession && activeSession.messages) {
          chatHistory = activeSession.messages;
        }
      }
      
      // 4. 构建消息
      const messages = [
        { role: 'system', content: activeAgentObject.systemPrompt || '你是一个有帮助的助手。' },
        ...chatHistory.map(msg => ({
          role: msg.sender === 'user' ? 'user' : 'assistant',
          content: msg.text
        })),
        { role: 'user', content: messageText }
      ];
      
      // 5. 创建用户消息
      const newUserMessage = {
        sender: 'user', 
        text: messageText,
        files: attachedFiles.map(f => ({ 
          id: f.id, name: f.name, size: f.size, type: f.type, 
          uploadedAt: f.uploadedAt, preview: f.preview,
          isAiGenerated: f.isAiGenerated, aiAgent: f.aiAgent
        })),
        notes: attachedNotes.map(n => ({ 
          id: n.id, name: n.name, content: n.content, createdAt: n.createdAt, 
          preview: n.preview, isAiGenerated: n.isAiGenerated, aiAgent: n.aiAgent
        })),
        timestamp: new Date().toISOString(),
      };
      
      // 6. 创建流式 AI 响应占位符
      const aiMessageId = `msg-ai-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const streamingAiResponse = {
        id: aiMessageId,
        sender: 'ai', 
        text: '', 
        timestamp: new Date().toISOString(), 
        files: [],
        streaming: true,
      };

      // 7. 更新会话状态
      let targetSessionId = currentActiveSessionId;
      
      if (!targetSessionId) {
        // 创建新会话
        targetSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
        const newSession = {
          sessionId: targetSessionId,
          startTime: new Date().toISOString(),
          endTime: new Date().toISOString(),
          messages: [newUserMessage, streamingAiResponse],
          sessionFiles: attachedFiles.map(f => ({ 
            id: f.id, name: f.name, type: f.type, size: f.size, 
            uploadedAt: f.uploadedAt, isAiGenerated: f.isAiGenerated, aiAgent: f.aiAgent
          })),
          sessionNotes: attachedNotes.map(n => ({ 
            id: n.id, name: n.name, content: n.content, createdAt: n.createdAt,
            isAiGenerated: n.isAiGenerated, aiAgent: n.aiAgent
          }))
        };
        
        // 8. 更新本地状态
        setLocalChatSessions(prev => [newSession, ...prev]);
        setActiveSessionId(targetSessionId);
      } else {
        // 更新现有会话 - 使用本地状态
        setLocalChatSessions(prev => {
          const sessionIndex = prev.findIndex(s => s.sessionId === targetSessionId);
          if (sessionIndex !== -1) {
            const sessionToUpdate = { ...prev[sessionIndex] };
            sessionToUpdate.messages = [...(sessionToUpdate.messages || []), newUserMessage, streamingAiResponse];
            sessionToUpdate.endTime = new Date().toISOString();
            
            const newSessionFiles = attachedFiles.map(f => ({ 
              id: f.id, name: f.name, type: f.type, size: f.size, 
              uploadedAt: f.uploadedAt, isAiGenerated: f.isAiGenerated, aiAgent: f.aiAgent
            }));
            sessionToUpdate.sessionFiles = Array.from(new Map([...(sessionToUpdate.sessionFiles || []), ...newSessionFiles].map(f => [f.id, f])).values());
            
            const newSessionNotes = attachedNotes.map(n => ({ 
              id: n.id, name: n.name, content: n.content, createdAt: n.createdAt,
              isAiGenerated: n.isAiGenerated, aiAgent: n.aiAgent
            }));
            sessionToUpdate.sessionNotes = Array.from(new Map([...(sessionToUpdate.sessionNotes || []), ...newSessionNotes].map(n => [n.id, n])).values());
            
            const newSessions = [...prev];
            newSessions[sessionIndex] = sessionToUpdate;
            return newSessions;
          } else {
            // 如果本地状态没有，从项目状态创建新的本地副本
            const projectSession = projectData.sessions?.find(s => s.sessionId === targetSessionId);
            if (projectSession) {
              const updatedSession = {
                ...projectSession,
                messages: [...(projectSession.messages || []), newUserMessage, streamingAiResponse],
                endTime: new Date().toISOString()
              };
              return [updatedSession, ...prev];
            }
            return prev;
          }
        });
      }
      
      console.log('🎯 ProjectPage: Final document IDs for AI:', documentIds);

      // 9. 开始流式聊天
      const streamResponse = await apiService.chat.createStreamingChatCompletion({
        model: selectedModel,
        messages: messages,
        temperature: 0.7,
        stream: true, // 确保启用流式输出
        conversation_id: currentConversationId,
        document_ids: documentIds.length > 0 ? documentIds : undefined
      });

      // 10. 处理流式响应
      const reader = streamResponse.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullContent = '';
      let updateCounter = 0;
      const UPDATE_THROTTLE = 10; // 每10个chunk更新一次UI

      console.log('开始处理流式响应...');

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log('流式响应完成，最终内容长度:', fullContent.length);
          break;
        }
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            if (data === '[DONE]') {
              console.log('收到[DONE]信号，完成流式响应');
              
              // 最终更新本地状态
              setLocalChatSessions(prev => {
                return prev.map(session => {
                  if (session.sessionId === targetSessionId) {
                    return {
                      ...session,
                      messages: session.messages.map(msg => 
                        msg.id === aiMessageId 
                          ? { ...msg, text: fullContent, streaming: false }
                          : msg
                      ),
                      endTime: new Date().toISOString()
                    };
                  }
                  return session;
                });
              });
              
              // 同步最终状态到项目
              setTimeout(() => {
                const finalLocalSessions = localChatSessions.map(session => {
                  if (session.sessionId === targetSessionId) {
                    return {
                      ...session,
                      messages: session.messages.map(msg => 
                        msg.id === aiMessageId 
                          ? { ...msg, text: fullContent, streaming: false }
                          : msg
                      ),
                      endTime: new Date().toISOString()
                    };
                  }
                  return session;
                });
                
                updateProject(projectData.id, {
                  ...projectData,
                  sessions: [...(projectData.sessions || []), ...finalLocalSessions.filter(
                    localSession => !projectData.sessions?.some(
                      projectSession => projectSession.sessionId === localSession.sessionId
                    )
                  )]
                });
              }, 100);
              
              return; // 退出函数
            }
            
            try {
              const chunk = JSON.parse(data);
              const content = chunk.choices?.[0]?.delta?.content;
              
              if (content) {
                fullContent += content;
                updateCounter++;
                
                // 节流更新：只在特定间隔更新本地状态
                if (updateCounter % UPDATE_THROTTLE === 0) {
                  console.log(`流式更新 (${updateCounter}): 内容长度 ${fullContent.length}`);
                  
                  // 更新本地聊天状态
                  setLocalChatSessions(prev => {
                    return prev.map(session => {
                      if (session.sessionId === targetSessionId) {
                        return {
                          ...session,
                          messages: session.messages.map(msg => 
                            msg.id === aiMessageId 
                              ? { ...msg, text: fullContent, streaming: true }
                              : msg
                          )
                        };
                      }
                      return session;
                    });
                  });
                }
              }
            } catch (e) {
              console.warn('Failed to parse chunk:', data);
            }
          }
        }
      }

    } catch (error) {
      console.error('Error sending streaming message to project:', error);
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
            localChatSessions={localChatSessions}
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