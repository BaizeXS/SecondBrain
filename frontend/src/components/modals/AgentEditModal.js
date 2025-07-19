// src/components/modals/AgentEditModal.js (新建文件)
import React, { useState, useEffect, useRef } from 'react';
import styles from './AgentEditModal.module.css'; // 新建对应的 CSS
import { FiX, FiInfo } from 'react-icons/fi';
import { getIconComponent } from '../../contexts/AgentContext'; // 确保路径正确

// 示例图标选项
const iconOptions = ['FiMessageSquare', 'FiBriefcase', 'FiEdit2', 'FiTerminal', 'FiCpu', 'FiFeather'];

const getCustomApisFromStorage = () => {
  try {
    const apis = localStorage.getItem('customApis');
    if (apis) return JSON.parse(apis);
  } catch (e) {}
  return [];
};

const AgentEditModal = ({ isOpen, onClose, onSave, agent: initialAgent }) => {
  const [agentData, setAgentData] = useState({});
  const [error, setError] = useState('');
  const modalContentRef = useRef(null);
  const isCreatingNew = !initialAgent?.id; // 判断是创建还是编辑
  const [customApis, setCustomApis] = useState([]);

  useEffect(() => {
    if (isOpen) {
      // 当模态框打开时，根据传入的 agent 初始化表单
      // 如果 initialAgent 为 null 或没有 id，则为创建新 Agent
      // 如果 initialAgent 存在，则是编辑或克隆
      if (initialAgent) {
        setAgentData(initialAgent);
      } else {
        // 为新 Agent 设置默认值
        setAgentData({
          name: '', description: '', icon: iconOptions[0], color: '#4CAF50',
          systemPrompt: '',
          apiProvider: 'default', // <<< 默认使用内置模型
          modelName: 'gpt-4',
          apiEndpoint: '',
          apiKey: '',
          isSystem: false,
        });
      }
      setError('');
    }
    setCustomApis(getCustomApisFromStorage());
  }, [isOpen, initialAgent]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setAgentData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = () => {
    if (!agentData.name?.trim()) {
      setError('Agent name is required.');
      return;
    }
    setError('');
    onSave(agentData); // 将整个 agentData 对象传递给保存回调
  };

  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        <div className={styles.modalHeader}>
          <h3 className={styles.modalTitle}>{isCreatingNew ? 'Create New Agent' : `Edit Agent: ${initialAgent?.name}`}</h3>
          <button onClick={onClose} className={styles.closeButtonTop} aria-label="Close modal"><FiX /></button>
        </div>
        <div className={styles.modalBody}>
          <div className={styles.formGrid}>
            <div className={styles.formGroup}>
              <label htmlFor="agentName">Agent Name <span className={styles.requiredStar}>*</span></label>
              <input type="text" id="agentName" name="name" value={agentData.name || ''} onChange={handleChange} className={styles.inputField} />
              {error && <p className={styles.errorMessage}>{error}</p>}
            </div>
            <div className={styles.formGroup}>
              <label htmlFor="agentDescription">Description</label>
              <input type="text" id="agentDescription" name="description" value={agentData.description || ''} onChange={handleChange} className={styles.inputField} />
            </div>
          </div>

          <div className={styles.formGroup}>
            <label>Icon & Color</label>
            <div className={styles.iconColorPicker}>
              <div className={styles.iconSelector}>
                {iconOptions.map(iconName => {
                  const IconComponent = getIconComponent(iconName);
                  return (
                    <button
                      key={iconName}
                      className={`${styles.iconOption} ${agentData.icon === iconName ? styles.iconSelected : ''}`}
                      onClick={() => handleChange({ target: { name: 'icon', value: iconName } })}
                    >
                      <IconComponent />
                    </button>
                  );
                })}
              </div>
              <input type="color" name="color" value={agentData.color || '#4CAF50'} onChange={handleChange} className={styles.colorInput} />
            </div>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="systemPrompt">System Prompt (Instructions for the AI)</label>
            <textarea
              id="systemPrompt" name="systemPrompt"
              value={agentData.systemPrompt || ''} onChange={handleChange}
              className={styles.textareaField} rows={6}
              placeholder="e.g., You are a helpful assistant specialized in summarizing scientific papers..."
            />
          </div>
          {/* --- 新增：API 配置区域 --- */}
          <div className={`${styles.formGroup} ${styles.apiConfigSection}`}>
            <h4>Model Configuration</h4>

            <div className={styles.apiProviderToggle}>
              <label>
                <input
                  type="radio" name="apiProvider" value="default"
                  checked={agentData.apiProvider === 'default'}
                  onChange={handleChange}
                />
                Use Default Model
              </label>
              <label>
                <input
                  type="radio" name="apiProvider" value="custom"
                  checked={agentData.apiProvider === 'custom'}
                  onChange={handleChange}
                />
                Use Custom API
              </label>
            </div>

            {/* 根据选择显示不同的配置项 */}
            {agentData.apiProvider === 'default' ? (
              <div className={styles.formSubGroup}>
                <label htmlFor="defaultModelName">Model</label>
                <select
                  id="defaultModelName" name="modelName"
                  value={agentData.modelName || 'gpt-4'}
                  onChange={handleChange}
                  className={styles.selectField}
                >
                  {/* 这里应该是一个预设的模型列表 */}
                  <option value="gpt-4">Default (GPT-4)</option>
                  <option value="deepseek">Default (DeepSeek)</option>
                </select>
                <p className={styles.fieldHint}>Select from the built-in models.</p>
              </div>
            ) : (
              <div className={styles.customApiFields}>
                <div className={styles.formSubGroup}>
                  <label htmlFor="customApiSelect">Select Your Custom API</label>
                  <select
                    id="customApiSelect"
                    className={styles.selectField}
                    value={agentData.apiEndpoint || ''}
                    onChange={e => {
                      const selectedApi = customApis.find(api => api.endpoint === e.target.value);
                      if (selectedApi) {
                        setAgentData(prev => ({
                          ...prev,
                          apiEndpoint: selectedApi.endpoint,
                          apiKey: selectedApi.apiKey || '',
                          modelName: selectedApi.modelName || '',
                        }));
                      } else {
                        setAgentData(prev => ({ ...prev, apiEndpoint: e.target.value }));
                      }
                    }}
                  >
                    <option value="">-- Select from Your Custom APIs --</option>
                    {customApis.map(api => (
                      <option key={api.id} value={api.endpoint}>{api.name} ({api.endpoint})</option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </div>
        </div>
        <div className={styles.modalFooter}>
          <button onClick={onClose} className={`${styles.actionButton} ${styles.cancelButton}`}>Cancel</button>
          <button onClick={handleSubmit} className={`${styles.actionButton} ${styles.saveButton}`}>{isCreatingNew ? 'Create' : 'Save Changes'}</button>
        </div>
      </div>
    </div >
  );
};
export default AgentEditModal;