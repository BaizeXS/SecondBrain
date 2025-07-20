// src/contexts/ProjectContext.js
import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { spaceAPI, documentAPI, noteAPI } from '../services/apiService';
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
  const loadProjects = useCallback(async () => {
    try {
      setLoadingProjects(true);
      
      // 检查是否有认证 token
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.log("ProjectContext: No token found, skipping projects load");
        setProjects([]);
        setLoadingProjects(false);
        return;
      }
      
      const response = await spaceAPI.getSpaces({ limit: 100 });
      const spaces = response.spaces || [];
      
      // 将后端空间数据转换为前端项目格式
      const convertedProjects = spaces.map((space, index) => ({
        id: space.id.toString(),
        name: space.name,
        description: space.description || '',
        iconColor: projectColors[index % projectColors.length],
        createdAt: space.created_at,
        updatedAt: space.updated_at,
        files: [], // 文档将在需要时单独加载
        notes: [], // 笔记将在需要时单独加载
        sessions: [], // 聊天会话将在需要时单独加载
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
      }));
      
      setProjects(convertedProjects);
      setNextColorIndex(convertedProjects.length % projectColors.length);
    } catch (error) {
      console.error("ProjectContext: Error loading spaces from backend", error);
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
      const spaceData = {
        name: projectDetails.name,
        description: projectDetails.description || '',
        is_public: false,
        tags: projectDetails.tags || [],
      };

      const newSpace = await spaceAPI.createSpace(spaceData);
      
      const newProject = {
        id: newSpace.id.toString(),
        name: newSpace.name,
        description: newSpace.description || '',
        iconColor: projectColors[nextColorIndex % projectColors.length],
        createdAt: newSpace.created_at,
        updatedAt: newSpace.updated_at,
        files: [],
        notes: [],
        sessions: [],
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
      return newProject;
    } catch (error) {
      console.error("ProjectContext: Error creating space", error);
      throw error;
    }
  }, [nextColorIndex, closeCreateProjectModal]);

  const getProjectById = useCallback((projectId) => {
    return projects.find(p => p.id === projectId);
  }, [projects]);

  const deleteProject = useCallback(async (projectIdToDelete) => {
    try {
      await spaceAPI.deleteSpace(parseInt(projectIdToDelete));
      setProjects(prev => prev.filter(project => project.id !== projectIdToDelete));
    } catch (error) {
      console.error("ProjectContext: Error deleting space", error);
      throw error;
    }
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