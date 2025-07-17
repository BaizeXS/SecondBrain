// src/components/modals/CreateProjectModal.js (新建文件夹和文件)
import React, { useState, useRef, useEffect } from 'react';
import styles from './CreateProjectModal.module.css'; // 我们会创建这个 CSS 文件
import { FiX, FiUploadCloud, FiFileText, FiTrash2 } from 'react-icons/fi';

const CreateProjectModal = ({ isOpen, onClose, onCreateProject }) => {
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]); // 存储用户选择的 File 对象
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);
  const modalContentRef = useRef(null);

  console.log("CreateProjectModal: Rendering. isOpen prop:", isOpen); // <<< 添加日志

  useEffect(() => {
    if (isOpen) {
    console.log("CreateProjectModal: isOpen is true, attempting to focus input."); // <<< 添加日志
      setProjectName('');
      setProjectDescription('');
      setSelectedFiles([]);
      setError('');
      // 自动聚焦到项目名称输入框 (可选)
      // setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [isOpen]);

  // 点击模态框外部关闭 (可选)
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (modalContentRef.current && !modalContentRef.current.contains(event.target)) {
        onClose(); // 如果希望点击外部也关闭，取消注释
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose]);


  const handleFileChange = (event) => {
    const files = Array.from(event.target.files);
    // 你可以添加文件大小、类型、数量的校验
    setSelectedFiles(prevFiles => {
      const newFiles = files.filter(nf => !prevFiles.some(pf => pf.name === nf.name && pf.size === nf.size)); // 简单去重
      return [...prevFiles, ...newFiles];
    });
    if (fileInputRef.current) fileInputRef.current.value = ""; // 清空，以便再次选择相同文件
  };

  const removeFile = (fileNameToRemove) => {
    setSelectedFiles(prevFiles => prevFiles.filter(file => file.name !== fileNameToRemove));
  };

  const handleSubmit = () => {
    if (!projectName.trim()) {
      setError('Project name is required.');
      return;
    }
    setError('');
    // 将文件对象直接传递，ProjectContext 的 addProject 再决定如何处理它们
    // (例如，只存元数据，或者如果设计了文件上传服务，则在这里触发上传)
    onCreateProject(projectName.trim(), projectDescription.trim(), selectedFiles);
  };

  if (!isOpen) {
    console.log("CreateProjectModal: isOpen is false, returning null."); // <<< 添加日志
    return null;
  }

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent} ref={modalContentRef}>
        <div className={styles.modalHeader}>
          <h3 className={styles.modalTitle}>Create New Neuro Core</h3>
          <button onClick={onClose} className={styles.closeButtonTop} aria-label="Close modal">
            <FiX />
          </button>
        </div>

        <div className={styles.modalBody}>
          <div className={styles.formGroup}>
            <label htmlFor="newProjectName">Project Name <span className={styles.requiredStar}>*</span></label>
            <input
              type="text"
              id="newProjectName"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="e.g., Quantum Physics Research"
              className={styles.inputField}
            />
            {error && <p className={styles.errorMessage}>{error}</p>}
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="newProjectDescription">Description (Optional)</label>
            <textarea
              id="newProjectDescription"
              value={projectDescription}
              onChange={(e) => setProjectDescription(e.target.value)}
              placeholder="Add a brief description for your project..."
              className={styles.textareaField}
              rows={3}
            />
          </div>

          <div className={styles.formGroup}>
            <label>Attach Files (Optional)</label>
            <div className={styles.fileUploadArea} onClick={() => fileInputRef.current?.click()}>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                style={{ display: 'none' }}
                multiple // 允许选择多个文件
              />
              <FiUploadCloud className={styles.uploadIcon} />
              <p>Click to browse or drag & drop files here</p>
              <span>(Max 10 files, 25MB per file)</span> {/* 示例限制 */}
            </div>
            {selectedFiles.length > 0 && (
              <div className={styles.selectedFilesList}>
                <h4>Selected files:</h4>
                <ul>
                  {selectedFiles.map((file, index) => (
                    <li key={index}>
                      <FiFileText className={styles.fileItemIcon} />
                      <span>{file.name} ({ (file.size / 1024 / 1024).toFixed(2) } MB)</span>
                      <button onClick={() => removeFile(file.name)} className={styles.removeFileButton} title="Remove file">
                        <FiTrash2 />
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        <div className={styles.modalFooter}>
          <button onClick={onClose} className={`${styles.actionButton} ${styles.cancelButton}`}>
            Cancel
          </button>
          <button onClick={handleSubmit} className={`${styles.actionButton} ${styles.createButton}`}>
            Create Project
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateProjectModal;