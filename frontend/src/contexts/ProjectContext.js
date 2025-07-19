// src/contexts/ProjectContext.js
import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
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

  useEffect(() => {
    try {
      const storedProjects = localStorage.getItem('neuroCoreProjects');
      const storedColorIdx = parseInt(localStorage.getItem('projectColorIndex') || '0', 10);
      const initialProjects = storedProjects ? JSON.parse(storedProjects) : defaultInitialProjects;
      setProjects(initialProjects);
      setNextColorIndex(isNaN(storedColorIdx) ? initialProjects.length % projectColors.length : storedColorIdx);
      if (!storedProjects) localStorage.setItem('neuroCoreProjects', JSON.stringify(defaultInitialProjects));
    } catch (error) {
      console.error("ProjectContext: Error loading from localStorage", error);
      setProjects(defaultInitialProjects);
    }
    setLoadingProjects(false);
  }, []);

  useEffect(() => {
    if (!loadingProjects) {
      localStorage.setItem('neuroCoreProjects', JSON.stringify(projects));
      localStorage.setItem('projectColorIndex', nextColorIndex.toString());
    }
  }, [projects, nextColorIndex, loadingProjects]);

  const openCreateProjectModal = useCallback(() => setIsCreateProjectModalOpen(true), []);
  const closeCreateProjectModal = useCallback(() => setIsCreateProjectModalOpen(false), []);

  const addProject = useCallback((projectDetails) => {
    const newProject = {
      id: `proj-${Date.now()}`,
      name: projectDetails.name,
      description: projectDetails.description || '',
      iconColor: projectColors[nextColorIndex % projectColors.length],
      createdAt: new Date().toISOString(),
      files: (projectDetails.files || []).map(file => ({
        id: `file-${file.name}-${Date.now()}`, name: file.name, type: file.type, size: file.size, uploadedAt: new Date().toISOString(),
      })),
      notes: projectDetails.notes || [],
      sessions: projectDetails.chatHistory && projectDetails.chatHistory.length > 0
        ? [{
          sessionId: `session-${Date.now()}`, startTime: new Date().toISOString(), messages: projectDetails.chatHistory,
          aiSummary: `Initial discussion in "${projectDetails.name.substring(0, 20)}..."`,
          sessionFiles: (projectDetails.files || []).map(f => ({ id: `file-${f.name}-${Date.now()}`, name: f.name }))
        }]
        : [],
      fileChats: {},
      sharing: {
        isShared: false,
        shareLevel: 'owner',
        sharedWith: [],
        permissions: 'read',
        sharedAt: null,
        sharedBy: null
      },
    };
    setProjects(prev => [...prev, newProject]);
    setNextColorIndex(prev => (prev + 1) % projectColors.length);
    closeCreateProjectModal();
    return newProject;
  }, [nextColorIndex, closeCreateProjectModal]);

  const getProjectById = useCallback((projectId) => projects.find(p => p.id === projectId), [projects]);

  const deleteProject = useCallback((projectIdToDelete) => {
    setProjects(prev => prev.filter(project => project.id !== projectIdToDelete));
  }, []);

  const updateProject = useCallback((projectId, partialUpdatedData) => {
    setProjects(prevProjects =>
      prevProjects.map(p => {
        if (p.id === projectId) {
          const updatedProject = { ...p, ...partialUpdatedData, updatedAt: new Date().toISOString() };
          // Ensure arrays are new references if they are updated
          if (partialUpdatedData.files) updatedProject.files = [...partialUpdatedData.files];
          if (partialUpdatedData.notes) updatedProject.notes = [...partialUpdatedData.notes];
          if (partialUpdatedData.sessions) updatedProject.sessions = [...partialUpdatedData.sessions];
          if (partialUpdatedData.fileChats) updatedProject.fileChats = { ...partialUpdatedData.fileChats };
          if (partialUpdatedData.sharing) updatedProject.sharing = { ...partialUpdatedData.sharing };
          return updatedProject;
        }
        return p;
      })
    );
  }, []);

  const updateProjectSharing = useCallback((projectId, sharingData) => {
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
            }
          };
        }
        return p;
      })
    );
  }, []);

  const value = {
    projects, loadingProjects,
    addProject, getProjectById, deleteProject, updateProject,
    updateProjectSharing,
    isCreateProjectModalOpen, openCreateProjectModal, closeCreateProjectModal,
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