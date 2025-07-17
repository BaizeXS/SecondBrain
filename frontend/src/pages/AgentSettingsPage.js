// src/pages/AgentSettingsPage.js (新建文件)
import React, { useState } from 'react';
import styles from './AgentSettingsPage.module.css'; // 新建 CSS
import { useAgents, getIconComponent } from '../contexts/AgentContext';
import { FiPlusSquare, FiTrash2, FiCopy, FiEdit, FiCpu } from 'react-icons/fi';
import AgentEditModal from '../components/modals/AgentEditModal';

const AgentSettingsPage = () => {
  const { agents, loadingAgents, addOrUpdateAgent, deleteAgent } = useAgents();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState(null);

  const handleCreateAgent = () => {
    setEditingAgent(null); // 传递 null 表示创建新 Agent
    setIsModalOpen(true);
  };

  const handleEditAgent = (agent) => {
    setEditingAgent(agent); // 传递要编辑的 Agent 对象
    setIsModalOpen(true);
  };

  const handleCloneAgent = (agent) => {
    // 创建一个 agent 副本，清空 id 并修改 name
    const clonedAgent = { ...agent, name: `${agent.name} (Copy)`, id: null, isSystem: false };
    setEditingAgent(clonedAgent);
    setIsModalOpen(true);
  };

  const handleDeleteAgent = (event, agent) => {
    event.stopPropagation();
    if (agent.isSystem) { alert("System agents cannot be deleted."); return; }
    if (window.confirm(`Are you sure you want to delete the agent "${agent.name}"?`)) {
      deleteAgent(agent.id);
    }
  };

  const handleSaveFromModal = (agentData) => {
    addOrUpdateAgent(agentData); // 调用 context 的函数来保存或更新
    setIsModalOpen(false); // 关闭模态框
  };

  if (loadingAgents) {
    return <div className={styles.loadingState}>Loading Agents...</div>;
  }

  return (
    <div className={styles.agentSettingsPage}>
      <div className={styles.pageHeader}>
        <FiCpu /> <h1>Agent Management</h1>
      </div>
      <p className={styles.pageDescription}>
        View, customize, and create your own AI agents.
      </p>

      <div className={styles.agentCardsContainer}>
        <div className={`${styles.agentCard} ${styles.createAgentCard}`} onClick={handleCreateAgent}>
          <FiPlusSquare className={styles.createIcon} />
          <h3>Create New Agent</h3>
          <p>Define a new role and personality.</p>
        </div>

        {agents.map(agent => {
          const IconComponent = getIconComponent(agent.icon);
          return (
            <div key={agent.id} className={styles.agentCard} onClick={() => handleEditAgent(agent)}>
              <div className={styles.cardHeader}>
                <div className={styles.iconWrapper} style={{ backgroundColor: agent.color }}> <IconComponent /> </div>
                <h3 className={styles.agentName}>{agent.name}</h3>
                {agent.isSystem && <span className={styles.systemTag}>System</span>}
              </div>
              <p className={styles.agentDescription}>{agent.description}</p>
              <div className={styles.cardActions}>
                <button onClick={(e) => { e.stopPropagation(); handleCloneAgent(agent); }} title="Clone Agent"> <FiCopy /> Clone </button>
                {!agent.isSystem && (
                  <button onClick={(e) => handleDeleteAgent(e, agent)} className={styles.deleteButton} title="Delete Agent"> <FiTrash2 /> </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <AgentEditModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveFromModal}
        agent={editingAgent} // 传递当前正在编辑/创建的 agent 数据
      />
    </div>
  );
};
export default AgentSettingsPage;