// src/pages/NeuroCorePage.js
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import styles from './NeuroCorePage.module.css';
import { useProjects } from '../contexts/ProjectContext';
import { FiPlusSquare, FiTrash2, FiSettings } from 'react-icons/fi';
import ManageProjectsModal from '../components/modals/ManageProjectsModal';

const NeuroCorePage = () => {
  // 从 Context 获取 projects 列表, openCreateProjectModal 函数, deleteProject 函数, 和加载状态
  const { projects, openCreateProjectModal, deleteProject, batchDeleteProjects, refreshProjects, loadingProjects } = useProjects();
  const navigate = useNavigate(); // useNavigate 仍然需要，以防未来有其他导航需求
  
  // 项目管理模态框状态
  const [isManageModalOpen, setIsManageModalOpen] = useState(false);

  // handleCreateProjectClick 现在只负责打开模态框
  const handleTriggerCreateModal = () => {
    console.log("NeuroCorePage: Create card clicked, calling openCreateProjectModal."); // <<< 添加日志
    openCreateProjectModal(); // 调用 Context 中提供的函数来打开全局模态框
  };

  const handleDeleteProject = async (event, projectIdToDelete, projectName) => {
    event.preventDefault();
    event.stopPropagation();
    if (window.confirm(`Are you sure you want to delete the project "${projectName}"? This action cannot be undone.`)) {
      if (deleteProject) {
        try {
          await deleteProject(projectIdToDelete);
          // 删除成功的提示已经在ProjectContext中处理了
        } catch (error) {
          // 错误处理已经在ProjectContext中完成
          console.error(`Failed to delete project ${projectName}:`, error);
        }
      } else {
        alert("Delete functionality is not available in ProjectContext.");
      }
    }
  };

  // 处理项目管理模态框
  const handleOpenManageModal = () => {
    setIsManageModalOpen(true);
  };

  const handleCloseManageModal = () => {
    setIsManageModalOpen(false);
  };

  const handleBatchDeleteProjects = async (projectIds) => {
    await batchDeleteProjects(projectIds);
  };

  const handleRefreshProjects = async () => {
    await refreshProjects();
  };

  if (loadingProjects) {
    return (
      <div className={styles.neuroCorePage}>
        <h2>Welcome to Second Brain</h2>
        <p className={styles.platformDescription}>
          Second Brain is an AI-driven smart knowledge management and learning aid platform...
        </p>
        <div className={styles.loadingState}>Loading projects...</div>
      </div>
    );
  }

  return (
    <div className={styles.neuroCorePage}>
      <div className={styles.pageHeader}>
        <div className={styles.headerContent}>
          <h2>Welcome to Second Brain</h2>
          <button
            onClick={handleOpenManageModal}
            className={styles.manageButton}
            title="管理项目"
          >
            <FiSettings />
            管理项目
          </button>
        </div>
      </div>
      
      <p className={styles.platformDescription}>
        Second Brain is an AI-driven smart knowledge management and learning aid platform.
        Positioned as "AI + knowledge management + learning ecosystem", it uses NLP, KG, RAG and edge computing.
        You can create your own neuro core here!
      </p>

      <div className={styles.cardsContainer}>
        {/* 创建新项目的卡片 - onClick 调用 handleTriggerCreateModal */}
        <div
          className={`${styles.card} ${styles.createCard}`}
          onClick={handleTriggerCreateModal}
          role="button"
          tabIndex={0}
          onKeyPress={(e) => e.key === 'Enter' && handleTriggerCreateModal()}
        >
          <FiPlusSquare className={styles.createIcon} />
          <h3>Create Neuro Core</h3>
          <p>Start a new exploration</p>
        </div>

        {/* 已有项目的卡片 */}
        {projects.map(project => (
          <Link
            to={`/neurocore/project/${project.id}`}
            key={project.id}
            className={styles.card}
          >
            <div className={styles.cardHeader}>
              <span className={styles.projectColorIcon} style={{ backgroundColor: project.iconColor || '#cccccc' }}></span>
              <h3 className={styles.projectName}>{project.name}</h3>
              <button
                className={styles.deleteCardButton}
                onClick={(e) => handleDeleteProject(e, project.id, project.name)}
                title={`Delete project ${project.name}`}
              >
                <FiTrash2 />
              </button>
            </div>
            <p className={styles.projectDescription}>{project.description || 'No description available.'}</p>
            <div className={styles.cardFooter}>
              <span className={styles.projectInfo}>
                {(project.files?.length || 0)} files, {(project.notes?.length || 0)} notes
              </span>
            </div>
          </Link>
        ))}
      </div>
      
      {/* 项目管理模态框 */}
      <ManageProjectsModal
        isOpen={isManageModalOpen}
        onClose={handleCloseManageModal}
        projects={projects}
        onDeleteProjects={handleBatchDeleteProjects}
        onRefreshProjects={handleRefreshProjects}
      />
      
      {/* 创建项目的模态框现在由 App.js 中的 GlobalCreateProjectModal 渲染和管理 */}
    </div>
  );
};
export default NeuroCorePage;