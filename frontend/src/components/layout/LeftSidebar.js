// src/components/layout/LeftSidebar.js
import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import styles from './LeftSidebar.module.css';
import { useSidebar } from '../../contexts/SidebarContext';
import { useProjects } from '../../contexts/ProjectContext'; // 已导入
import {
  FiMessageCircle, FiPlus, FiMoreHorizontal, FiArchive, FiCpu, FiUsers, FiSettings, FiUser,
  FiChevronLeft, FiChevronRight, FiShare2, FiGlobe
} from 'react-icons/fi';

const LeftSidebar = () => {
  const { isLeftSidebarOpen, toggleLeftSidebar } = useSidebar();
  // 从 Context 获取 projects 列表, openCreateProjectModal 函数, 和加载状态
  // 不再需要 addProject，因为创建逻辑由全局模态框处理，模态框再调用 context 的 addProject
  const { projects, openCreateProjectModal, loadingProjects } = useProjects();
  const navigate = useNavigate(); // useNavigate 仍然可能被其他导航逻辑使用

  const maxProjectsToShow = 6;
  const projectsToDisplayInUI = projects ? projects.slice(0, maxProjectsToShow) : [];

  // handleCreateNewProjectViaPlusButton 现在只负责打开模态框
  const handleTriggerCreateModalFromSidebar = () => {
    console.log("LeftSidebar: '+' button clicked, calling openCreateProjectModal."); // <<< 添加日志
    openCreateProjectModal(); // 调用 Context 中提供的函数来打开全局模态框
  };

  const getShareIcon = (sharing) => {
    if (!sharing || !sharing.isShared) {
      return null; // 不显示图标，表示私有项目
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

  const getShareIconColor = (sharing) => {
    if (!sharing || !sharing.isShared) {
      return 'transparent';
    }
    switch (sharing.shareLevel) {
      case 'organization':
        return '#28a745'; // 绿色
      case 'public':
        return '#007bff'; // 蓝色
      default:
        return '#6c757d'; // 灰色
    }
  };

  if (loadingProjects && isLeftSidebarOpen) {
    return (
      <nav className={`${styles.leftSidebar} ${isLeftSidebarOpen ? styles.open : styles.collapsed}`}>
        <button
          onClick={toggleLeftSidebar}
          className={styles.toggleButtonInternal}
          aria-label={isLeftSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
        >
          {isLeftSidebarOpen ? <FiChevronLeft /> : <FiChevronRight />}
        </button>
        {isLeftSidebarOpen && (
            <div style={{ padding: '20px', textAlign: 'center', color: '#777' }}>
                Loading projects...
            </div>
        )}
      </nav>
    );
  }

  return (
    <nav className={`${styles.leftSidebar} ${isLeftSidebarOpen ? styles.open : styles.collapsed}`}>
      <button
        onClick={toggleLeftSidebar}
        className={styles.toggleButtonInternal}
        aria-label={isLeftSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
      >
        {isLeftSidebarOpen ? <FiChevronLeft /> : <FiChevronRight />}
      </button>

      {isLeftSidebarOpen && (
        <>
          <div className={styles.sidebarHeaderBranding}>
            <span className={styles.sidebarAppName}>Brain Network</span>
          </div>

          <div className={styles.sidebarSection}>
            <NavLink to="/" className={({isActive}) => `${styles.navItem} ${isActive ? styles.activeLink : ''}`}>
              <FiMessageCircle className={styles.navIcon} />
              <span className={styles.navText}>Chat</span>
            </NavLink>
          </div>

          <hr className={styles.separator} />

          <div className={styles.sidebarSection}>
            <div className={styles.sectionHeader}>
              <NavLink to="/neurocore" className={({isActive}) => `${styles.sectionTitleLink} ${isActive ? styles.activeLinkHeavy : ''}`}>
                NeuroCore
              </NavLink>
              {/* "+" 按钮的 onClick 调用 handleTriggerCreateModalFromSidebar */}
              <button onClick={handleTriggerCreateModalFromSidebar} className={styles.addButton} title="Create new project">
                <FiPlus />
              </button>
            </div>
            {projects && projects.length > 0 ? (
              projects.length > maxProjectsToShow ? (
                <div className={styles.projectListScrollWrapper}>
                  <ul className={styles.projectList}>
                    {projects.map(project => (
                      <li key={project.id}>
                        <NavLink to={`/neurocore/project/${project.id}`} className={({isActive}) => `${styles.navItem} ${styles.projectItem} ${isActive ? styles.activeLink : ''}`}>
                          <span className={styles.projectIcon} style={{ backgroundColor: project.iconColor || '#cccccc' }}></span>
                          <span className={styles.navText}>{project.name}</span>
                          {getShareIcon(project.sharing) && (
                            <span 
                              className={styles.shareStatusIcon}
                              style={{ color: getShareIconColor(project.sharing) }}
                              title={project.sharing.shareLevel === 'organization' ? 'Shared with organization' : 
                                     project.sharing.shareLevel === 'public' ? 'Public project' : 'Shared with users'}
                            >
                              {getShareIcon(project.sharing)}
                            </span>
                          )}
                        </NavLink>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <ul className={styles.projectList}>
                  {projectsToDisplayInUI.map(project => (
                    <li key={project.id}>
                      <NavLink to={`/neurocore/project/${project.id}`} className={({isActive}) => `${styles.navItem} ${styles.projectItem} ${isActive ? styles.activeLink : ''}`}>
                        <span className={styles.projectIcon} style={{ backgroundColor: project.iconColor || '#cccccc' }}></span>
                        <span className={styles.navText}>{project.name}</span>
                        {getShareIcon(project.sharing) && (
                          <span 
                            className={styles.shareStatusIcon}
                            style={{ color: getShareIconColor(project.sharing) }}
                            title={project.sharing.shareLevel === 'organization' ? 'Shared with organization' : 
                                   project.sharing.shareLevel === 'public' ? 'Public project' : 'Shared with users'}
                          >
                            {getShareIcon(project.sharing)}
                          </span>
                        )}
                      </NavLink>
                    </li>
                  ))}
                </ul>
              )
            ) : (
              <p style={{padding: '0 20px', fontSize: '0.9rem', color: '#777'}}>No projects yet. Click '+' to create one.</p>
            )}
          </div>

          <div className={styles.sidebarSection}>
            <NavLink to="/temp" className={({isActive}) => `${styles.navItem} ${isActive ? styles.activeLink : ''}`}>
              <FiArchive className={styles.navIcon} />
              <span className={styles.navText}>Temp</span>
            </NavLink>
          </div>

          <hr className={styles.separator} />

          <div className={styles.sidebarSection}>
            <NavLink to="/agent-settings" className={({isActive}) => `${styles.navItem} ${isActive ? styles.activeLink : ''}`}>
              <FiCpu className={styles.navIcon} />
              <span className={styles.navText}>Agent</span>
            </NavLink>
          </div>

          <div className={`${styles.sidebarSection} ${styles.bottomNav}`}>
            <NavLink to="/profile" className={`${styles.navItem} ${styles.bottomNavItem}`} title="User Profile">
              <FiUser className={styles.navIcon} />
            </NavLink>
            <div className={styles.bottomNavRight}>
              <NavLink to="/community" className={`${styles.navItem} ${styles.bottomNavItemSmall}`} title="Community">
                <FiUsers className={styles.navIcon} />
              </NavLink>
              <NavLink to="/settings" className={`${styles.navItem} ${styles.bottomNavItemSmall}`} title="Settings">
                <FiSettings className={styles.navIcon} />
              </NavLink>
            </div>
          </div>
        </>
      )}
    </nav>
  );
};

export default LeftSidebar;