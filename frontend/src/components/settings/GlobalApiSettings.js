// src/components/settings/GlobalApiSettings.js
import React, { useState, useEffect } from 'react';
import styles from './SettingsComponents.module.css'; // 我们将在这个文件中添加新样式
import { FiSave, FiInfo, FiPlus, FiEdit, FiTrash2, FiZap } from 'react-icons/fi';
import ApiEditModal from '../modals/ApiEditModal';

// 模拟数据
const platformModels = [
  { id: 'sb-basic', name: 'Second Brain Basic', description: 'Good for general Q&A and daily tasks.', plan: 'Free', active: true },
  { id: 'openai-gpt4', name: 'OpenAI GPT-4 Turbo', description: 'Powerful, top-tier model for complex reasoning.', plan: 'Pro', active: false },
  { id: 'anthropic-claude3', name: 'Anthropic Claude 3 Opus', description: 'Excellent for creative writing and long-context tasks.', plan: 'Pro', active: false },
  { id: 'google-gemini', name: 'Google Gemini Pro', description: 'Versatile model with strong multi-modal capabilities.', plan: 'Enterprise', active: false },
];

// <<< 修复点1：initialUserApis 变量名错误，应该是 initialCustomApis，或者直接用在 useState 中 >>>
const initialCustomApis = [
  { id: 'custom-1', name: 'My Local Llama', endpoint: 'http://localhost:11434/...' },
  { id: 'custom-2', name: 'Groq API Key', endpoint: 'https://api.groq.com/...' },
];

const GlobalApiSettings = () => {
  // <<< 修复点2：添加所有缺失的 useState 声明 >>>
  const [currentDefault, setCurrentDefault] = useState('sb-basic');
  const [customApis, setCustomApis] = useState(initialCustomApis);
  const [isApiModalOpen, setIsApiModalOpen] = useState(false);
  const [editingApi, setEditingApi] = useState(null);

  // --- 事件处理器 ---
  const handleAddCustomApi = () => {
    setEditingApi(null);
    setIsApiModalOpen(true);
  };

  const handleEditCustomApi = (api) => {
    setEditingApi(api);
    setIsApiModalOpen(true);
  };

  const handleDeleteCustomApi = (apiId, apiName) => {
    if (window.confirm(`Are you sure you want to delete the custom API "${apiName}"?`)) {
      setCustomApis(prev => prev.filter(api => api.id !== apiId));
      if (currentDefault === apiId) {
        setCurrentDefault('sb-basic');
      }
    }
  };

  const handleSaveFromModal = (apiData) => {
    if (apiData.id) {
      setCustomApis(prev => prev.map(api => api.id === apiData.id ? apiData : api));
    } else {
      const newApi = { ...apiData, id: `custom-${Date.now()}` };
      setCustomApis(prev => [...prev, newApi]);
    }
    setIsApiModalOpen(false);
  };

  const handleActivatePlatformModel = (modelId) => {
    const model = platformModels.find(m => m.id === modelId);
    if (model.plan !== 'Free' /* && !user.isPro */) {
      alert(`Upgrade to Pro to use ${model.name}!`);
      return;
    }
    setCurrentDefault(modelId);
  };

  useEffect(() => {
    localStorage.setItem('customApis', JSON.stringify(customApis));
  }, [customApis]);

  return (
    <div className={styles.settingsSection}>
      <div className={styles.sectionHeader}>
        <h3>Default AI Model API</h3>
      </div>
      <div className={styles.sectionContent}>
        <p className={styles.sectionDescription}>
          Choose the default model for all agents that don't have a specific API configured. This setting acts as your global fallback.
        </p>

        {/* --- 平台集成模型 --- */}
        <h4>Platform Integrated Models</h4>
        <div className={styles.apiCardsContainer}>
          {platformModels.map(model => (
            <div key={model.id} className={`${styles.apiCard} ${currentDefault === model.id ? styles.activeApiCard : ''}`}>
              <div className={styles.apiCardHeader}>
                <h5>{model.name}</h5>
                <span className={`${styles.planTag} ${styles[model.plan.toLowerCase()]}`}>{model.plan}</span>
              </div>
              <p className={styles.apiCardDescription}>{model.description}</p>
              <div className={styles.apiCardFooter}>
                {currentDefault === model.id ? (
                  <span className={styles.activeStatus}><FiZap /> Active</span>
                ) : (
                  <button onClick={() => handleActivatePlatformModel(model.id)} className={styles.activateButton}>
                    {model.plan === 'Free' ? 'Activate' : 'Upgrade & Activate'}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* --- 用户自定义 API 部分，onClick 事件已更新 --- */}
        <h4 style={{ marginTop: '30px' }}>Your Custom APIs</h4>
        <div className={styles.customApiList}>
          {customApis.map(api => (
            <div key={api.id} className={`${styles.customApiItem} ${currentDefault === api.id ? styles.activeApiCard : ''}`}>
              <div className={styles.apiInfo}>
                <span className={styles.apiName}>{api.name}</span>
                <span className={styles.apiEndpoint}>{api.endpoint}</span>
              </div>
              <div className={styles.apiActions}>
                {currentDefault === api.id ? (
                  <span className={styles.activeStatus}><FiZap /> Active</span>
                ) : (
                  <button onClick={() => setCurrentDefault(api.id)} className={styles.activateButton}>Activate</button>
                )}
                <button onClick={() => handleEditCustomApi(api)} className={styles.iconButton} title="Edit"><FiEdit /></button>
                <button onClick={() => handleDeleteCustomApi(api.id, api.name)} className={`${styles.iconButton} ${styles.deleteIconButton}`} title="Delete"><FiTrash2 /></button>
              </div>
            </div>
          ))}
          <button onClick={handleAddCustomApi} className={styles.addApiButton}>
            <FiPlus /> Add Custom API
          </button>
        </div>

      </div>

      {/* --- 新增：渲染模态框 --- */}
      <ApiEditModal
        isOpen={isApiModalOpen}
        onClose={() => setIsApiModalOpen(false)}
        onSave={handleSaveFromModal}
        api={editingApi}
      />
    </div>
  );
};
export default GlobalApiSettings;