import React, { useState, useEffect } from 'react';
import { FiX, FiTrash2, FiRefreshCw, FiAlertTriangle, FiSearch, FiFilter } from 'react-icons/fi';
import styles from './ManageProjectsModal.module.css';

const ManageProjectsModal = ({ isOpen, onClose, projects, onDeleteProjects, onRefreshProjects }) => {
  const [selectedProjects, setSelectedProjects] = useState(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [showAutoCreated, setShowAutoCreated] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // 过滤项目
  const filteredProjects = projects.filter(project => {
    const matchesSearch = project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (project.description || '').toLowerCase().includes(searchTerm.toLowerCase());
    
    const isAutoCreated = project.name.includes('研究:') || project.name.startsWith('Deep Research') ||
                         project.tags?.includes('deep_research') || project.tags?.includes('auto-created');
    
    if (showAutoCreated) {
      return matchesSearch && isAutoCreated;
    }
    
    return matchesSearch;
  });

  const handleSelectProject = (projectId) => {
    const newSelected = new Set(selectedProjects);
    if (newSelected.has(projectId)) {
      newSelected.delete(projectId);
    } else {
      newSelected.add(projectId);
    }
    setSelectedProjects(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedProjects.size === filteredProjects.length) {
      setSelectedProjects(new Set());
    } else {
      setSelectedProjects(new Set(filteredProjects.map(p => p.id)));
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedProjects.size === 0) return;
    
    const projectNames = Array.from(selectedProjects)
      .map(id => projects.find(p => p.id === id)?.name)
      .filter(Boolean);
    
    const confirmMessage = `确定要删除以下 ${selectedProjects.size} 个项目吗？\n\n` +
      projectNames.slice(0, 5).join('\n') +
      (projectNames.length > 5 ? `\n... 还有 ${projectNames.length - 5} 个项目` : '') +
      '\n\n此操作无法撤销！';
    
    if (!window.confirm(confirmMessage)) return;
    
    setIsDeleting(true);
    try {
      await onDeleteProjects(Array.from(selectedProjects));
      setSelectedProjects(new Set());
    } catch (error) {
      console.error('批量删除失败:', error);
      alert(`删除失败: ${error.message}`);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleQuickDeleteAutoCreated = async () => {
    const autoCreatedProjects = projects.filter(project => 
      project.name.includes('研究:') || project.name.startsWith('Deep Research') ||
      project.tags?.includes('deep_research') || project.tags?.includes('auto-created')
    );
    
    if (autoCreatedProjects.length === 0) {
      alert('没有找到自动创建的研究项目');
      return;
    }
    
    const confirmMessage = `发现 ${autoCreatedProjects.length} 个自动创建的研究项目，确定要全部删除吗？\n\n` +
      autoCreatedProjects.slice(0, 3).map(p => p.name).join('\n') +
      (autoCreatedProjects.length > 3 ? `\n... 还有 ${autoCreatedProjects.length - 3} 个项目` : '') +
      '\n\n此操作无法撤销！';
    
    if (!window.confirm(confirmMessage)) return;
    
    setIsDeleting(true);
    try {
      const idsToDelete = autoCreatedProjects.map(p => p.id);
      await onDeleteProjects(idsToDelete);
      setSelectedProjects(new Set());
    } catch (error) {
      console.error('批量删除失败:', error);
      alert(`删除失败: ${error.message}`);
    } finally {
      setIsDeleting(false);
    }
  };

  // 重置状态
  useEffect(() => {
    if (!isOpen) {
      setSelectedProjects(new Set());
      setSearchTerm('');
      setShowAutoCreated(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const autoCreatedCount = projects.filter(project => 
    project.name.includes('研究:') || project.name.startsWith('Deep Research') ||
    project.tags?.includes('deep_research') || project.tags?.includes('auto-created')
  ).length;

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        <div className={styles.modalHeader}>
          <h3 className={styles.modalTitle}>项目管理</h3>
          <button onClick={onClose} className={styles.closeButton}>
            <FiX />
          </button>
        </div>

        <div className={styles.modalBody}>
          {/* 工具栏 */}
          <div className={styles.toolbar}>
            <div className={styles.searchBox}>
              <FiSearch className={styles.searchIcon} />
              <input
                type="text"
                placeholder="搜索项目..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={styles.searchInput}
              />
            </div>
            
            <div className={styles.filters}>
              <label className={styles.filterLabel}>
                <input
                  type="checkbox"
                  checked={showAutoCreated}
                  onChange={(e) => setShowAutoCreated(e.target.checked)}
                />
                只显示自动创建的项目 ({autoCreatedCount})
              </label>
            </div>
          </div>

          {/* 批量操作按钮 */}
          <div className={styles.batchActions}>
            <div className={styles.selectActions}>
              <button
                onClick={handleSelectAll}
                className={styles.actionButton}
                disabled={filteredProjects.length === 0}
              >
                {selectedProjects.size === filteredProjects.length ? '取消全选' : '全选'}
              </button>
              
              <button
                onClick={onRefreshProjects}
                className={styles.actionButton}
                disabled={isDeleting}
              >
                <FiRefreshCw className={isDeleting ? styles.spinning : ''} />
                刷新
              </button>
            </div>

            <div className={styles.deleteActions}>
              {autoCreatedCount > 0 && (
                <button
                  onClick={handleQuickDeleteAutoCreated}
                  className={`${styles.actionButton} ${styles.warningButton}`}
                  disabled={isDeleting}
                >
                  <FiTrash2 />
                  删除所有自动创建的项目 ({autoCreatedCount})
                </button>
              )}
              
              <button
                onClick={handleDeleteSelected}
                className={`${styles.actionButton} ${styles.dangerButton}`}
                disabled={selectedProjects.size === 0 || isDeleting}
              >
                <FiTrash2 />
                删除选中的项目 ({selectedProjects.size})
              </button>
            </div>
          </div>

          {/* 项目列表 */}
          <div className={styles.projectsList}>
            {filteredProjects.length === 0 ? (
              <div className={styles.emptyState}>
                <p>没有找到匹配的项目</p>
              </div>
            ) : (
              filteredProjects.map(project => {
                const isAutoCreated = project.name.includes('研究:') || 
                                    project.name.startsWith('Deep Research') ||
                                    project.tags?.includes('deep_research') || 
                                    project.tags?.includes('auto-created');
                
                return (
                  <div
                    key={project.id}
                    className={`${styles.projectItem} ${isAutoCreated ? styles.autoCreated : ''}`}
                  >
                    <div className={styles.projectCheckbox}>
                      <input
                        type="checkbox"
                        checked={selectedProjects.has(project.id)}
                        onChange={() => handleSelectProject(project.id)}
                      />
                    </div>
                    
                    <div className={styles.projectInfo}>
                      <div className={styles.projectName}>
                        {project.name}
                        {isAutoCreated && (
                          <span className={styles.autoCreatedBadge}>
                            <FiAlertTriangle />
                            自动创建
                          </span>
                        )}
                      </div>
                      <div className={styles.projectMeta}>
                        <span>创建时间: {new Date(project.createdAt).toLocaleString()}</span>
                        {project.description && (
                          <span>描述: {project.description}</span>
                        )}
                        {project.tags && project.tags.length > 0 && (
                          <span>标签: {project.tags.join(', ')}</span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        <div className={styles.modalFooter}>
          <p className={styles.footerText}>
            总共 {projects.length} 个项目，其中 {autoCreatedCount} 个自动创建，{filteredProjects.length} 个匹配筛选条件
          </p>
          <button onClick={onClose} className={styles.cancelButton}>
            关闭
          </button>
        </div>
      </div>
    </div>
  );
};

export default ManageProjectsModal; 