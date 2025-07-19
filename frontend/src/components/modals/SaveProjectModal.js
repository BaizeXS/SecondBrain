// src/components/modals/SaveProjectModal.js (新建文件夹和文件)
import React, { useState, useRef, useEffect } from 'react';
import styles from './SaveProjectModal.module.css';

const SaveProjectModal = ({ isOpen, onClose, onSave }) => {
  const [projectName, setProjectName] = useState('');
  const [error, setError] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      // 自动聚焦到输入框
      inputRef.current?.focus();
      // 清空上一次的输入和错误
      setProjectName('');
      setError('');
    }
  }, [isOpen]);

  const handleSave = () => {
    if (!projectName.trim()) {
      setError('Project name cannot be empty.');
      return;
    }
    setError('');
    onSave(projectName.trim()); // 将项目名称传递给回调
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && projectName.trim()) {
      handleSave();
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        <button onClick={onClose} className={styles.closeButtonTop}>×</button>
        <h3 className={styles.modalTitle}>Save Current Exploration</h3>
        <p className={styles.modalSubtitle}>
          Would you like to save the current chat and its context as a new project?
        </p>
        <div className={styles.inputGroup}>
          <label htmlFor="projectName">Project Name:</label>
          <input
            ref={inputRef}
            type="text"
            id="projectName"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter a name for your new project"
            className={styles.projectNameInput}
          />
          {error && <p className={styles.errorMessage}>{error}</p>}
        </div>
        <div className={styles.modalActions}>
          <button onClick={onClose} className={`${styles.actionButton} ${styles.cancelButton}`}>
            Cancel
          </button>
          <button onClick={handleSave} className={`${styles.actionButton} ${styles.saveProjectButton}`}>
            Save Project
          </button>
        </div>
      </div>
    </div>
  );
};

export default SaveProjectModal;