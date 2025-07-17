// src/contexts/AgentContext.js (新建文件和文件夹)
import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { FiMessageSquare, FiBriefcase, FiEdit2, FiTerminal } from 'react-icons/fi';

const AgentContext = createContext();

// 初始默认的 Agents
const defaultAgents = [
  {
    id: 'agent-general',
    name: 'General',
    description: 'A helpful and general-purpose assistant.',
    icon: 'FiMessageSquare', // 存储图标的字符串名称，而不是组件实例
    color: '#4CAF50',
    systemPrompt: 'You are a helpful general-purpose AI assistant. Be clear, concise, and friendly.',
    isSystem: true, // 标记为系统默认，不可删除
    // --- 新增 API 字段 ---
    apiProvider: 'default', // 'default' 表示使用应用的内置模型服务
    apiEndpoint: '',
    apiKey: '',
    modelName: 'gpt-4', // 默认 agent 使用的模型
  },
  {
    id: 'agent-professor',
    name: 'Professor',
    description: 'An expert in academic fields, provides detailed explanations.',
    icon: 'FiBriefcase',
    color: '#FF9800',
    systemPrompt: 'You are an academic professor. Provide detailed, well-structured, and accurate explanations on any given topic. Cite sources if possible.',
    isSystem: true,
    // --- 新增 API 字段 ---
    apiProvider: 'default', // 'default' 表示使用应用的内置模型服务
    apiEndpoint: '',
    apiKey: '',
    modelName: 'gpt-4', // 默认 agent 使用的模型
  },
  {
    id: 'agent-copywriter',
    name: 'Copywriter',
    description: 'Generates creative and persuasive marketing copy.',
    icon: 'FiEdit2',
    color: '#9C27B0',
    systemPrompt: 'You are a professional copywriter. Your goal is to create compelling, persuasive, and engaging content. Use marketing frameworks like AIDA where appropriate.',
    isSystem: true,
    // --- 新增 API 字段 ---
    apiProvider: 'default', // 'default' 表示使用应用的内置模型服务
    apiEndpoint: '',
    apiKey: '',
    modelName: 'gpt-4', // 默认 agent 使用的模型
  },
  {
    id: 'agent-coder',
    name: 'Coder',
    description: 'An expert programmer who provides code and technical help.',
    icon: 'FiTerminal',
    color: '#00BCD4',
    systemPrompt: 'You are an expert programmer. Provide clean, efficient, and well-documented code snippets. Explain the code clearly. Default to JavaScript unless another language is specified.',
    isSystem: true,
    // --- 新增 API 字段 ---
    apiProvider: 'default', // 'default' 表示使用应用的内置模型服务
    apiEndpoint: '',
    apiKey: '',
    modelName: 'gpt-4', // 默认 agent 使用的模型
  },
];

export const AgentProvider = ({ children }) => {
  const [agents, setAgents] = useState([]);
  const [loadingAgents, setLoadingAgents] = useState(true);

  // 加载 Agents (可以从 localStorage 或未来从 API)
  useEffect(() => {
    try {
      const storedAgents = localStorage.getItem('customAgents');
      if (storedAgents) {
        // 合并默认 Agents 和用户自定义的 Agents
        const customAgents = JSON.parse(storedAgents);
        setAgents([...defaultAgents, ...customAgents]);
      } else {
        setAgents(defaultAgents);
      }
    } catch (error) {
      console.error("AgentContext: Error loading custom agents", error);
      setAgents(defaultAgents);
    }
    setLoadingAgents(false);
  }, []);

  // 保存用户自定义的 Agents 到 localStorage
  useEffect(() => {
    if (!loadingAgents) {
      const customAgents = agents.filter(agent => !agent.isSystem);
      localStorage.setItem('customAgents', JSON.stringify(customAgents));
    }
  }, [agents, loadingAgents]);

  const addOrUpdateAgent = useCallback((agentData) => {
    setAgents(prevAgents => {
      const existingIndex = prevAgents.findIndex(a => a.id === agentData.id);
      if (existingIndex > -1) { // 更新
        const updatedAgents = [...prevAgents];
        // 确保所有字段都被更新
        updatedAgents[existingIndex] = { ...updatedAgents[existingIndex], ...agentData };
        return updatedAgents;
      } else { // 添加
        const newAgent = {
          // 为新 Agent 设置默认值，然后用传入的数据覆盖
          apiProvider: 'default', apiEndpoint: '', apiKey: '', modelName: 'gpt-4',
          ...agentData,
          id: `agent-custom-${Date.now()}`,
          isSystem: false,
        };
        return [...prevAgents, newAgent];
      }
    });
  }, []);

  const deleteAgent = useCallback((agentIdToDelete) => {
    setAgents(prevAgents => {
      // 过滤时，我们要保留所有 isSystem 的 agent，
      // 或者所有 id 不等于要删除的 id 的 agent。
      // 这两个条件用 OR (||) 连接。
      const updatedAgents = prevAgents.filter(agent =>
        agent.isSystem || agent.id !== agentIdToDelete
      );
      return updatedAgents;
    });
  }, []); // 依赖项为空，因为 setAgents 是稳定的

  const getAgentById = useCallback((agentId) => {
    return agents.find(a => a.id === agentId);
  }, [agents]);


  const value = { agents, loadingAgents, addOrUpdateAgent, deleteAgent, getAgentById };

  return (
    <AgentContext.Provider value={value}>
      {children}
    </AgentContext.Provider>
  );
};

export const useAgents = () => {
  const context = useContext(AgentContext);
  if (context === undefined) {
    throw new Error('useAgents must be used within an AgentProvider');
  }
  return context;
};

// 用于根据字符串名称获取图标组件的辅助函数
export const getIconComponent = (iconName) => {
  const icons = { FiMessageSquare, FiBriefcase, FiEdit2, FiTerminal };
  return icons[iconName] || FiMessageSquare; // 返回默认图标
};