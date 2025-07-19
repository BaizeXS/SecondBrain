// src/pages/TempPage.js (新建文件)
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './TempPage.module.css'; // 新建对应的 CSS
import { useProjects } from '../contexts/ProjectContext'; // 用于“保存为项目”
import SaveProjectModal from '../components/modals/SaveProjectModal'; // 复用保存项目弹窗
import { FiMessageSquare, FiFileText, FiEdit3, FiRotateCcw, FiSave, FiTrash2 } from 'react-icons/fi';

const TempPage = () => {
  const [tempSession, setTempSession] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const navigate = useNavigate();
  const { addProject } = useProjects();

  useEffect(() => {
    try {
      const savedTempSession = localStorage.getItem('tempChatSession');
      if (savedTempSession) {
        setTempSession(JSON.parse(savedTempSession));
      }
    } catch (error) {
      console.error("Failed to load temporary session on TempPage:", error);
    }
    setIsLoading(false);
  }, []);

  const handleResumeSession = () => {
    if (!tempSession) return;

    // 1. 将临时会话数据放入 sessionStorage，以便 HomePage 加载
    // 我们直接使用 tempSession state 中的数据
    sessionStorage.setItem('sessionToRestore', JSON.stringify(tempSession));

    // 2. 导航到 HomePage
    navigate('/');
  };

  const handleSaveAsProject = (projectName) => {
    if (!tempSession) return;
    const projectData = {
      name: projectName,
      description: `Saved from a temporary session on ${new Date().toLocaleDateString()}`,
      chatHistory: tempSession.chatHistory || [],
      files: tempSession.filesMeta || [], // 使用保存的元数据
      notes: tempSession.notes || [],
      createdAt: tempSession.lastUpdatedAt || new Date().toISOString(),
    };
    const savedProject = addProject(projectData);
    if (savedProject && savedProject.id) {
      alert(`Project "${projectName}" saved successfully!`);
      localStorage.removeItem('tempChatSession'); // 清除临时会话
      setTempSession(null); // 清空当前页面的显示
      navigate(`/neurocore/project/${savedProject.id}`);
    } else {
      alert("Failed to save project.");
    }
    setIsSaveModalOpen(false);
  };

  const handleDiscardSession = () => {
    if (window.confirm("Are you sure you want to discard this unsaved session? This action cannot be undone.")) {
      localStorage.removeItem('tempChatSession');
      setTempSession(null);
      // 可以选择导航回主页
      // navigate('/');
    }
  };

  if (isLoading) {
    return <div className={styles.tempPage}><h2>Loading...</h2></div>;
  }

  if (!tempSession) {
    return (
      <div className={styles.tempPage}>
        <div className={styles.emptyState}>
          <h2>No Unsaved Session</h2>
          <p>Your previous chat session was saved or empty. You can start a new exploration on the Chat page.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.tempPage}>
      <div className={styles.header}>
        <h1>Last Unsaved Session</h1>
        <p>Last activity on: {new Date(tempSession.lastUpdatedAt).toLocaleString()}</p>
      </div>

      <div className={styles.actions}>
        <button onClick={handleResumeSession} className={styles.actionButton}>
          <FiRotateCcw /> Resume Session
        </button>
        <button onClick={() => setIsSaveModalOpen(true)} className={`${styles.actionButton} ${styles.saveButton}`}>
          <FiSave /> Save as Project
        </button>
        <button onClick={handleDiscardSession} className={`${styles.actionButton} ${styles.discardButton}`}>
          <FiTrash2 /> Discard Session
        </button>
      </div>

      <div className={styles.previewContainer}>
        <div className={styles.previewSection}>
          <h4><FiMessageSquare /> Chat Preview (Last 3 messages)</h4>
          <ul className={styles.previewList}>
            {(tempSession.chatHistory || []).slice(-3).map((msg, index) => (
              <li key={index}><strong>{msg.sender}:</strong> {msg.text.substring(0, 100)}...</li>
            ))}
          </ul>
        </div>
        <div className={styles.previewSection}>
          <h4><FiFileText /> Attached Files ({(tempSession.filesMeta || []).length})</h4>
          <ul className={styles.previewList}>
            {(tempSession.filesMeta || []).map(file => <li key={file.id}>{file.name}</li>)}
          </ul>
        </div>
        <div className={styles.previewSection}>
          <h4><FiEdit3 /> Context Notes ({(tempSession.notes || []).length})</h4>
          <ul className={styles.previewList}>
            {(tempSession.notes || []).map(note => <li key={note.id}>{note.name}</li>)}
          </ul>
        </div>
      </div>

      <SaveProjectModal
        isOpen={isSaveModalOpen}
        onClose={() => setIsSaveModalOpen(false)}
        onSave={handleSaveAsProject}
      />
    </div>
  );
};

export default TempPage;