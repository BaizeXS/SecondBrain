// src/components/modals/ApiEditModal.js (新建文件)
import React, { useState, useEffect, useRef } from 'react';
import styles from './AgentEditModal.module.css'; // 我们可以复用 AgentEditModal 的样式
import { FiX, FiInfo } from 'react-icons/fi';

const ApiEditModal = ({ isOpen, onClose, onSave, api: initialApi }) => {
  const [apiData, setApiData] = useState({});
  const [error, setError] = useState('');
  const isCreatingNew = !initialApi?.id;

  useEffect(() => {
    if (isOpen) {
      if (initialApi) {
        setApiData(initialApi);
      } else {
        // 为新的自定义 API 设置默认/空值
        setApiData({
          name: '',
          endpoint: '',
          apiKey: '',
          modelName: '',
        });
      }
      setError('');
    }
  }, [isOpen, initialApi]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setApiData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = () => {
    if (!apiData.name?.trim() || !apiData.endpoint?.trim()) {
      setError('API Name and Endpoint URL are required.');
      return;
    }
    setError('');
    onSave(apiData); // 将整个 apiData 对象传递给保存回调
  };

  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        <div className={styles.modalHeader}>
          <h3 className={styles.modalTitle}>{isCreatingNew ? 'Add Custom API' : 'Edit Custom API'}</h3>
          <button onClick={onClose} className={styles.closeButtonTop} aria-label="Close modal"><FiX /></button>
        </div>
        <div className={styles.modalBody}>
          <div className={styles.formGroup}>
            <label htmlFor="apiName">API Name <span className={styles.requiredStar}>*</span></label>
            <input type="text" id="apiName" name="name" value={apiData.name || ''} onChange={handleChange} className={styles.inputField} placeholder="e.g., My Personal Groq API" />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="apiEndpoint">API Endpoint URL <span className={styles.requiredStar}>*</span></label>
            <input type="text" id="apiEndpoint" name="endpoint" value={apiData.endpoint || ''} onChange={handleChange} className={styles.inputField} placeholder="https://api.groq.com/openai/v1/chat/completions" />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="apiKey">API Key (Optional but Recommended)</label>
            <input type="password" id="apiKey" name="apiKey" value={apiData.apiKey || ''} onChange={handleChange} className={styles.inputField} placeholder="Enter your secret API key (will be stored locally)" />
            <p className={styles.fieldHint}><FiInfo size="0.9em" /> Your key is stored only in your browser's local storage.</p>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="modelName">Model Name (if required by API)</label>
            <input type="text" id="modelName" name="modelName" value={apiData.modelName || ''} onChange={handleChange} className={styles.inputField} placeholder="e.g., llama3-8b-8192, gemma-7b-it" />
          </div>

          {error && <p className={styles.errorMessage}>{error}</p>}
        </div>
        <div className={styles.modalFooter}>
          <button onClick={onClose} className={`${styles.actionButton} ${styles.cancelButton}`}>Cancel</button>
          <button onClick={handleSubmit} className={`${styles.actionButton} ${styles.saveButton}`}>{isCreatingNew ? 'Add API' : 'Save Changes'}</button>
        </div>
      </div>
    </div>
  );
};
export default ApiEditModal;