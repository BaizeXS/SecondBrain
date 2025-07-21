// src/contexts/ProjectContext.js
import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { spaceAPI, documentAPI, noteAPI, chatAPI, authAPI } from '../services/apiService';
import { FiMessageSquare, FiBriefcase, FiEdit2, FiTerminal, FiCpu, FiFeather } from 'react-icons/fi'; // For Agent Icons

const ProjectContext = createContext();

const projectColors = [
  '#FF6B6B', '#FFD166', '#06D6A0', '#118AB2', '#073B4C',
  '#F08080', '#FFC0CB', '#90EE90', '#ADD8E6', '#DDA0DD',
  '#E63946', '#F1FAEE', '#A8DADC', '#457B9D', '#1D3557'
];

const defaultInitialProjects = [
  {
    id: 'proj1-default', name: 'Project Alpha (Default)', iconColor: '#4285F4',
    description: 'Exploring AI fundamentals.',
    files: [{ id: 'file-default-1', name: 'Intro_to_NLP.pdf', type: 'application/pdf', size: 1024 * 300, uploadedAt: new Date(Date.now() - 86400000 * 4).toISOString() }],
    notes: [{ id: 'note-default-1', name: 'Brainstorming Ideas', preview: 'Key concepts include RAG...', content: 'Key concepts include RAG...', createdAt: new Date(Date.now() - 86400000 * 4).toISOString() }],
    sessions: [],
    fileChats: {},
    sharing: {
      isShared: false,
      shareLevel: 'owner',
      sharedWith: [],
      permissions: 'read',
      sharedAt: null,
      sharedBy: null
    },
    createdAt: new Date(Date.now() - 86400000 * 5).toISOString(),
  },
];

export const ProjectProvider = ({ children }) => {
  const [projects, setProjects] = useState([]);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [isCreateProjectModalOpen, setIsCreateProjectModalOpen] = useState(false);
  const [nextColorIndex, setNextColorIndex] = useState(0);

  // 从后端加载空间列表 - 修改后的版本
  const loadProjects = useCallback(async (isRetry = false) => {
    try {
      setLoadingProjects(true);
      
      // 检查是否有认证 token
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.log("ProjectContext: No token found, clearing projects");
        setProjects([]);
        return;
      }
      
      console.log("ProjectContext: Loading projects from backend...");
      const response = await spaceAPI.getSpaces({ limit: 100 });
      const spaces = response.spaces || [];
      
      // 过滤掉自动创建的研究空间（可选：用户可以在设置中启用显示这些空间）
      const userSpaces = spaces.filter(space => {
        // 如果空间的meta_data中包含created_by: "deep_research"，则视为自动创建的
        return !space.meta_data?.created_by || space.meta_data.created_by !== 'deep_research';
      });
      
      console.log(`ProjectContext: 成功加载${spaces.length}个空间，过滤后显示${userSpaces.length}个用户空间`);
      
      // 将后端空间数据转换为前端项目格式，并加载完整数据
      const convertedProjects = await Promise.all(userSpaces.map(async (space, index) => {
        // 并行加载该空间的文档、笔记和对话
        const [documentsResponse, notesResponse, conversationsResponse] = await Promise.allSettled([
          documentAPI.getDocuments({ space_id: space.id }),
          noteAPI.getNotes({ space_id: space.id }),
          chatAPI.getConversations({ space_id: space.id })
        ]);

        // 处理文档数据
        const files = documentsResponse.status === 'fulfilled' 
          ? (documentsResponse.value.documents || []).map(doc => ({
              id: doc.id.toString(),
              name: doc.filename,
              type: doc.content_type,
              size: doc.file_size,
              uploadedAt: doc.created_at,
              url: `/documents/${doc.id}`,
              preview: `Size: ${doc.file_size} bytes`
            }))
          : [];

        // 处理笔记数据
        const notes = notesResponse.status === 'fulfilled'
          ? (notesResponse.value.notes || []).map(note => ({
              id: note.id.toString(),
              name: note.title,
              content: note.content,
              preview: note.content?.substring(0, 100) + '...',
              createdAt: note.created_at,
              updatedAt: note.updated_at
            }))
          : [];

        // 处理对话数据
        const sessions = conversationsResponse.status === 'fulfilled'
          ? (conversationsResponse.value.conversations || []).map(conv => ({
              sessionId: conv.id.toString(),
              startTime: conv.created_at,
              endTime: conv.updated_at,
              messages: [], // 消息将在需要时单独加载
              sessionFiles: files, // 简化关联
              sessionNotes: notes  // 简化关联
            }))
          : [];

        return {
          id: space.id.toString(),
          name: space.name,
          description: space.description || '',
          iconColor: projectColors[index % projectColors.length],
          createdAt: space.created_at,
          updatedAt: space.updated_at,
          files: files,
          notes: notes,
          sessions: sessions,
          fileChats: {},
          sharing: {
            isShared: space.is_public,
            shareLevel: space.user_id ? 'owner' : 'collaborator',
            sharedWith: [],
            permissions: 'read',
            sharedAt: space.updated_at,
            sharedBy: space.user_id
          },
          // 后端字段映射
          spaceId: space.id,
          isPublic: space.is_public,
          tags: space.tags || [],
          userId: space.user_id,
        };
      }));
      
      setProjects(convertedProjects);
      setNextColorIndex(convertedProjects.length % projectColors.length);
    } catch (error) {
      console.error("ProjectContext: Error loading spaces from backend", error);
      
      // 检查是否为认证错误
      const isAuthError = error.message.includes('401') || 
                         error.message.includes('403') ||
                         error.message.includes('认证失败') || 
                         error.message.includes('权限不足') ||
                         error.message.includes('Unauthorized');
      
      if (isAuthError && !isRetry) {
        console.log("ProjectContext: Authentication failed, attempting token refresh");
        try {
          // 尝试刷新token
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            const refreshResult = await authAPI.refreshToken();
            if (refreshResult.access_token) {
              console.log("ProjectContext: Token refreshed successfully, retrying loadProjects");
              // 重试加载项目
              return await loadProjects(true);
            }
          }
        } catch (refreshError) {
          console.error("ProjectContext: Token refresh failed", refreshError);
        }
        
        // 刷新失败，清除认证状态
        console.log("ProjectContext: Clearing auth state due to failed authentication");
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        setProjects([]);
        
        // 不自动跳转，让AuthContext处理重定向
        window.dispatchEvent(new Event('auth-expired'));
        return;
      }
      
      // 非认证错误或重试后仍失败
      console.error("ProjectContext: Non-auth error or retry failed:", error.message);
      setProjects([]);
    } finally {
      setLoadingProjects(false);
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const openCreateProjectModal = useCallback(() => setIsCreateProjectModalOpen(true), []);
  const closeCreateProjectModal = useCallback(() => setIsCreateProjectModalOpen(false), []);

  const addProject = useCallback(async (projectDetails) => {
    try {
      console.log("ProjectContext: Creating project with details:", projectDetails);
      
      // 1. 检查是否已存在同名空间
      const existingProject = projects.find(p => p.name.toLowerCase() === projectDetails.name.toLowerCase());
      if (existingProject) {
        const confirmMessage = `项目 "${projectDetails.name}" 已存在。是否要创建一个唯一名称的项目？`;
        if (window.confirm(confirmMessage)) {
          // 生成唯一名称
          const timestamp = new Date().toLocaleString('zh-CN', { 
            month: '2-digit', 
            day: '2-digit', 
            hour: '2-digit', 
            minute: '2-digit' 
          }).replace(/[/:]/g, '-');
          projectDetails.name = `${projectDetails.name}-${timestamp}`;
        } else {
          throw new Error('用户取消创建重复名称的项目');
        }
      }

      const spaceData = {
        name: projectDetails.name,
        description: projectDetails.description || '',
        is_public: false,
        tags: projectDetails.tags || [],
      };

      // 2. 创建空间
      const newSpace = await spaceAPI.createSpace(spaceData);
      console.log("ProjectContext: Space created:", newSpace.id);

      const savedFiles = [];
      const savedNotes = [];
      let savedConversation = null;

      // 3. 上传文件到新空间
      if (projectDetails.files && projectDetails.files.length > 0) {
        console.log("ProjectContext: Uploading", projectDetails.files.length, "files to space");
        
        for (const file of projectDetails.files) {
          try {
            let uploadedDoc = null;
            
            console.log("ProjectContext: Processing file:", file.name, "ID:", file.id, "hasRawFile:", !!file.rawFile);
            
            if (file.rawFile) {
              // 上传新文件
              console.log("ProjectContext: Uploading file with rawFile");
              uploadedDoc = await documentAPI.uploadDocument(
                newSpace.id,
                file.rawFile,
                file.name,
                ['saved-from-chat']
              );
              console.log("ProjectContext: File uploaded:", uploadedDoc.id);
            } else if (file.id && !isNaN(parseInt(file.id))) {
              // 文件已存在，获取文件信息
              console.log("ProjectContext: Getting existing file:", file.id);
              try {
                uploadedDoc = await documentAPI.getDocument(parseInt(file.id));
                console.log("ProjectContext: Existing file referenced:", uploadedDoc.id);
              } catch (getError) {
                console.warn("ProjectContext: Could not get existing file:", file.id, getError);
                continue;
              }
            } else {
              // 如果既没有rawFile也没有有效ID，可能是临时文件，尝试重新创建
              console.warn("ProjectContext: File has no rawFile or valid ID:", file);
              
              // 检查是否是从localStorage恢复的文件，这种情况下rawFile会丢失
              if (file.name && file.size) {
                console.log("ProjectContext: Skipping file without rawFile - likely from localStorage:", file.name);
                // 创建一个占位符，表示文件存在但需要重新上传
                savedFiles.push({
                  id: `placeholder-${Date.now()}`,
                  name: file.name,
                  type: file.type || 'application/octet-stream',
                  size: file.size || 0,
                  uploadedAt: new Date().toISOString(),
                  url: null,
                  preview: `File metadata saved (${file.size || 0} bytes) - re-upload required`,
                  isPlaceholder: true
                });
              }
              continue;
            }
            
            if (uploadedDoc) {
              savedFiles.push({
                id: uploadedDoc.id.toString(),
                name: uploadedDoc.filename || uploadedDoc.original_filename || file.name,
                type: uploadedDoc.content_type,
                size: uploadedDoc.file_size || uploadedDoc.size,
                uploadedAt: uploadedDoc.created_at,
                url: `/documents/${uploadedDoc.id}`,
                preview: file.preview || `Size: ${uploadedDoc.file_size || uploadedDoc.size} bytes`
              });
            }
          } catch (fileError) {
            console.error("ProjectContext: Failed to process file:", file.name, fileError);
            // 记录错误但继续处理其他文件
            savedFiles.push({
              id: `error-${Date.now()}`,
              name: file.name,
              type: file.type || 'application/octet-stream',
              size: file.size || 0,
              uploadedAt: new Date().toISOString(),
              url: null,
              preview: `Upload failed: ${fileError.message}`,
              isError: true
            });
          }
        }
      }

      // 4. 保存笔记到新空间
      if (projectDetails.notes && projectDetails.notes.length > 0) {
        console.log("ProjectContext: Saving", projectDetails.notes.length, "notes to space");
        
        for (const note of projectDetails.notes) {
          try {
            const noteData = {
              title: note.name || 'Untitled Note',
              content: note.content || note.preview || '',
              space_id: newSpace.id,
              tags: ['saved-from-chat']
            };
            
            const savedNote = await noteAPI.createNote(noteData);
            console.log("ProjectContext: Note saved:", savedNote.id);
            
            savedNotes.push({
              id: savedNote.id.toString(),
              name: savedNote.title,
              content: savedNote.content,
              preview: savedNote.content?.substring(0, 100) + '...',
              createdAt: savedNote.created_at,
              updatedAt: savedNote.updated_at
            });
          } catch (noteError) {
            console.error("ProjectContext: Failed to save note:", note.name, noteError);
            // 继续处理其他笔记
          }
        }
      }

      // 5. 保存聊天记录为对话
      if (projectDetails.chatHistory && projectDetails.chatHistory.length > 0) {
        console.log("ProjectContext: Saving chat history as conversation");
        
        try {
          // 创建对话
          const conversationData = {
            title: projectDetails.name,
            mode: 'chat',
            space_id: newSpace.id
          };
          
          savedConversation = await chatAPI.createConversation(conversationData);
          console.log("ProjectContext: Conversation created:", savedConversation.id);
          
          // 保存聊天消息到对话
          for (const message of projectDetails.chatHistory) {
            try {
              const messageData = {
                content: message.text,
                role: message.sender === 'user' ? 'user' : 'assistant',
                conversation_id: savedConversation.id,
                metadata: {
                  timestamp: message.timestamp,
                  files: message.files || [],
                  notes: message.notes || []
                }
              };
              
              await chatAPI.sendMessage(messageData);
            } catch (msgError) {
              console.error("ProjectContext: Failed to save message:", msgError);
            }
          }
        } catch (convError) {
          console.error("ProjectContext: Failed to create conversation:", convError);
        }
      }
      
      // 6. 创建完整的项目对象
      const newProject = {
        id: newSpace.id.toString(),
        name: newSpace.name,
        description: newSpace.description || '',
        iconColor: projectColors[nextColorIndex % projectColors.length],
        createdAt: newSpace.created_at,
        updatedAt: newSpace.updated_at,
        files: savedFiles,
        notes: savedNotes,
        sessions: savedConversation ? [{
          sessionId: savedConversation.id.toString(),
          startTime: savedConversation.created_at,
          endTime: savedConversation.updated_at,
          messages: projectDetails.chatHistory || [],
          sessionFiles: savedFiles,
          sessionNotes: savedNotes
        }] : [],
        fileChats: {},
        sharing: {
          isShared: newSpace.is_public,
          shareLevel: 'owner',
          sharedWith: [],
          permissions: 'read',
          sharedAt: newSpace.created_at,
          sharedBy: newSpace.user_id
        },
        spaceId: newSpace.id,
        isPublic: newSpace.is_public,
        tags: newSpace.tags || [],
        userId: newSpace.user_id,
      };

      setProjects(prev => [...prev, newProject]);
      setNextColorIndex(prev => (prev + 1) % projectColors.length);
      closeCreateProjectModal();
      
      console.log("ProjectContext: Project created successfully with", savedFiles.length, "files,", savedNotes.length, "notes");
      return newProject;
    } catch (error) {
      console.error("ProjectContext: Error creating project", error);
      
      // 如果是用户主动取消，不显示错误
      if (error.message === '用户取消创建重复名称的项目') {
        return null; // 返回null表示用户取消
      }
      
      // 其他错误显示友好的错误信息
      let errorMessage = '创建项目失败';
      if (error.message.includes('400') || error.message.includes('已存在')) {
        errorMessage = '项目名称已存在或格式不正确，请尝试其他名称';
      } else if (error.message.includes('401') || error.message.includes('403')) {
        errorMessage = '认证失败，请重新登录';
        // 触发认证过期事件
        window.dispatchEvent(new Event('auth-expired'));
      } else if (error.message) {
        errorMessage = `创建项目失败: ${error.message}`;
      }
      
      // 只有在不是用户取消的情况下才显示错误
      alert(errorMessage);
      throw error;
    }
  }, [nextColorIndex, closeCreateProjectModal]);

  const getProjectById = useCallback((projectId) => {
    return projects.find(p => p.id === projectId);
  }, [projects]);

  const deleteProject = useCallback(async (projectIdToDelete) => {
    try {
      // 使用force=true确保能够删除含有内容的项目
      await spaceAPI.deleteSpace(parseInt(projectIdToDelete), true);
      setProjects(prev => prev.filter(project => project.id !== projectIdToDelete));
      console.log(`ProjectContext: Successfully deleted project ${projectIdToDelete}`);
    } catch (error) {
      console.error("ProjectContext: Error deleting space", error);
      // 显示用户友好的错误信息
      if (error.message.includes('404') || error.message.includes('空间不存在')) {
        // 如果项目已经不存在，从前端列表中移除
        setProjects(prev => prev.filter(project => project.id !== projectIdToDelete));
        console.log(`ProjectContext: Project ${projectIdToDelete} was already deleted, removed from UI`);
      } else if (error.message.includes('403') || error.message.includes('无权')) {
        alert('没有权限删除此项目');
      } else {
        alert(`删除项目失败: ${error.message}`);
      }
      throw error;
    }
  }, []);

  // 批量删除项目
  const batchDeleteProjects = useCallback(async (projectIdsToDelete) => {
    if (!projectIdsToDelete || projectIdsToDelete.length === 0) return;
    
    console.log("ProjectContext: Batch deleting projects:", projectIdsToDelete);
    
    const results = [];
    const errors = [];
    
    // 并发删除项目，但限制并发数量
    const batchSize = 3;
    for (let i = 0; i < projectIdsToDelete.length; i += batchSize) {
      const batch = projectIdsToDelete.slice(i, i + batchSize);
      
      const batchPromises = batch.map(async (projectId) => {
        try {
          // 使用force=true确保能够删除含有内容的项目
          await spaceAPI.deleteSpace(parseInt(projectId), true);
          return { id: projectId, success: true };
        } catch (error) {
          console.error(`Failed to delete project ${projectId}:`, error);
          return { id: projectId, success: false, error: error.message };
        }
      });
      
      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);
    }
    
    // 统计结果
    const successIds = results.filter(r => r.success).map(r => r.id);
    const failedResults = results.filter(r => !r.success);
    
    // 更新本地状态 - 移除成功删除的项目
    if (successIds.length > 0) {
      setProjects(prev => prev.filter(project => !successIds.includes(project.id)));
    }
    
    console.log(`ProjectContext: Batch delete completed. Success: ${successIds.length}, Failed: ${failedResults.length}`);
    
    // 如果有失败的项目，抛出错误信息
    if (failedResults.length > 0) {
      const errorMessage = `删除完成：成功 ${successIds.length} 个，失败 ${failedResults.length} 个\n\n失败详情:\n` +
        failedResults.map(r => `• ${r.id}: ${r.error}`).join('\n');
      
      if (successIds.length === 0) {
        // 全部失败
        throw new Error(`批量删除失败：\n${failedResults.map(r => r.error).join('\n')}`);
      } else {
        // 部分成功，部分失败
        alert(errorMessage);
      }
    }
    
    return {
      success: successIds.length,
      failed: failedResults.length,
      failedDetails: failedResults
    };
  }, []);

  const updateProject = useCallback(async (projectId, partialUpdatedData) => {
    try {
      const spaceData = {
        name: partialUpdatedData.name,
        description: partialUpdatedData.description,
        is_public: partialUpdatedData.isPublic,
        tags: partialUpdatedData.tags,
      };

      const updatedSpace = await spaceAPI.updateSpace(parseInt(projectId), spaceData);
      
      setProjects(prevProjects =>
        prevProjects.map(p => {
          if (p.id === projectId) {
            return {
              ...p,
              ...partialUpdatedData,
              name: updatedSpace.name,
              description: updatedSpace.description,
              updatedAt: updatedSpace.updated_at,
              isPublic: updatedSpace.is_public,
              tags: updatedSpace.tags || [],
            };
          }
          return p;
        })
      );
    } catch (error) {
      console.error("ProjectContext: Error updating space", error);
      throw error;
    }
  }, []);

  const updateProjectSharing = useCallback(async (projectId, sharingData) => {
    try {
      const spaceData = {
        is_public: sharingData.isShared,
      };

      await spaceAPI.updateSpace(parseInt(projectId), spaceData);
      
      setProjects(prevProjects =>
        prevProjects.map(p => {
          if (p.id === projectId) {
            return {
              ...p,
              sharing: {
                ...p.sharing,
                ...sharingData,
                sharedAt: sharingData.isShared ? new Date().toISOString() : null,
                sharedBy: sharingData.isShared ? 'current-user' : null
              },
              isPublic: sharingData.isShared,
            };
          }
          return p;
        })
      );
    } catch (error) {
      console.error("ProjectContext: Error updating space sharing", error);
      throw error;
    }
  }, []);

  // 加载项目的文档
  const loadProjectDocuments = useCallback(async (projectId) => {
    try {
      const response = await documentAPI.getDocuments({ space_id: parseInt(projectId) });
      const documents = response.documents || [];
      
      const files = documents.map(doc => ({
        id: doc.id.toString(),
        name: doc.title || doc.filename,
        type: doc.content_type,
        size: doc.file_size,
        uploadedAt: doc.created_at,
        url: `/documents/${doc.id}`,
        content: doc.content,
        processingStatus: doc.processing_status,
      }));

      setProjects(prevProjects =>
        prevProjects.map(p => {
          if (p.id === projectId) {
            return { ...p, files };
          }
          return p;
        })
      );

      return files;
    } catch (error) {
      console.error("ProjectContext: Error loading documents", error);
      return [];
    }
  }, []);

  // 加载项目的笔记
  const loadProjectNotes = useCallback(async (projectId) => {
    try {
      const response = await noteAPI.getNotes({ space_id: parseInt(projectId) });
      const notes = response.notes || [];
      
      const convertedNotes = notes.map(note => ({
        id: note.id.toString(),
        name: note.title,
        preview: note.content?.substring(0, 100) || '',
        content: note.content,
        createdAt: note.created_at,
        updatedAt: note.updated_at,
      }));

      setProjects(prevProjects =>
        prevProjects.map(p => {
          if (p.id === projectId) {
            return { ...p, notes: convertedNotes };
          }
          return p;
        })
      );

      return convertedNotes;
    } catch (error) {
      console.error("ProjectContext: Error loading notes", error);
      return [];
    }
  }, []);

  const value = {
    projects, 
    loadingProjects,
    addProject, 
    getProjectById, 
    deleteProject, 
    batchDeleteProjects,
    updateProject,
    updateProjectSharing,
    loadProjectDocuments,
    loadProjectNotes,
    isCreateProjectModalOpen, 
    openCreateProjectModal, 
    closeCreateProjectModal,
    refreshProjects: loadProjects,
  };

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  );
};

export const useProjects = () => {
  const context = useContext(ProjectContext);
  if (context === undefined) throw new Error('useProjects must be used within a ProjectProvider');
  return context;
};