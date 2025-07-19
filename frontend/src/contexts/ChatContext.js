import React, { createContext, useState, useContext, useCallback } from 'react';
import { chatAPI } from '../services/apiService';

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const [selectedFilesForChat, setSelectedFilesForChat] = useState([]);
  const [selectedNotesForChat, setSelectedNotesForChat] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [loadingConversations, setLoadingConversations] = useState(false);
  const [sendingMessage, setSendingMessage] = useState(false);

  // 加载对话列表
  const loadConversations = useCallback(async (spaceId = null) => {
    try {
      setLoadingConversations(true);
      const response = await chatAPI.getConversations({ space_id: spaceId });
      const conversationsList = response.conversations || [];
      setConversations(conversationsList);
      return conversationsList;
    } catch (error) {
      console.error("ChatContext: Error loading conversations", error);
      return [];
    } finally {
      setLoadingConversations(false);
    }
  }, []);

  // 创建新对话
  const createConversation = useCallback(async (conversationData) => {
    try {
      const newConversation = await chatAPI.createConversation(conversationData);
      setConversations(prev => [newConversation, ...prev]);
      setCurrentConversation(newConversation);
      return newConversation;
    } catch (error) {
      console.error("ChatContext: Error creating conversation", error);
      throw error;
    }
  }, []);

  // 获取对话详情
  const loadConversation = useCallback(async (conversationId, messageLimit = 50) => {
    try {
      const conversation = await chatAPI.getConversation(conversationId, messageLimit);
      setCurrentConversation(conversation);
      return conversation;
    } catch (error) {
      console.error("ChatContext: Error loading conversation", error);
      throw error;
    }
  }, []);

  // 发送消息
  const sendMessage = useCallback(async (conversationId, messageContent, files = []) => {
    try {
      setSendingMessage(true);
      
      const messageData = {
        content: messageContent,
        model: 'gpt-3.5-turbo', // 默认模型，可以从设置中获取
      };

      const response = await chatAPI.sendMessage(conversationId, messageData, files);
      
      // 更新当前对话的消息列表
      if (currentConversation && currentConversation.id === conversationId) {
        setCurrentConversation(prev => ({
          ...prev,
          messages: [...(prev.messages || []), response]
        }));
      }

      return response;
    } catch (error) {
      console.error("ChatContext: Error sending message", error);
      throw error;
    } finally {
      setSendingMessage(false);
    }
  }, [currentConversation]);

  // 重新生成消息
  const regenerateMessage = useCallback(async (conversationId, messageId, params = {}) => {
    try {
      const response = await chatAPI.regenerateMessage(conversationId, messageId, params);
      
      // 更新当前对话的消息
      if (currentConversation && currentConversation.id === conversationId) {
        setCurrentConversation(prev => ({
          ...prev,
          messages: prev.messages.map(msg => 
            msg.id === messageId ? response : msg
          )
        }));
      }

      return response;
    } catch (error) {
      console.error("ChatContext: Error regenerating message", error);
      throw error;
    }
  }, [currentConversation]);

  // 删除对话
  const deleteConversation = useCallback(async (conversationId) => {
    try {
      await chatAPI.deleteConversation(conversationId);
      setConversations(prev => prev.filter(conv => conv.id !== conversationId));
      
      if (currentConversation && currentConversation.id === conversationId) {
        setCurrentConversation(null);
      }
    } catch (error) {
      console.error("ChatContext: Error deleting conversation", error);
      throw error;
    }
  }, [currentConversation]);

  // 更新对话
  const updateConversation = useCallback(async (conversationId, updateData) => {
    try {
      const updatedConversation = await chatAPI.updateConversation(conversationId, updateData);
      
      setConversations(prev => 
        prev.map(conv => conv.id === conversationId ? updatedConversation : conv)
      );
      
      if (currentConversation && currentConversation.id === conversationId) {
        setCurrentConversation(updatedConversation);
      }

      return updatedConversation;
    } catch (error) {
      console.error("ChatContext: Error updating conversation", error);
      throw error;
    }
  }, [currentConversation]);

  // 添加文件到聊天框
  const addFilesToChat = useCallback((files) => {
    setSelectedFilesForChat(prev => {
      const newFiles = files.filter(file => 
        !prev.some(existing => existing.id === file.id)
      );
      return [...prev, ...newFiles];
    });
  }, []);

  // 添加笔记到聊天框
  const addNotesToChat = useCallback((notes) => {
    setSelectedNotesForChat(prev => {
      const newNotes = notes.filter(note => 
        !prev.some(existing => existing.id === note.id)
      );
      return [...prev, ...newNotes];
    });
  }, []);

  // 移除文件
  const removeFileFromChat = useCallback((fileId) => {
    setSelectedFilesForChat(prev => prev.filter(f => f.id !== fileId));
  }, []);

  // 移除笔记
  const removeNoteFromChat = useCallback((noteId) => {
    setSelectedNotesForChat(prev => prev.filter(n => n.id !== noteId));
  }, []);

  // 清空所有选择
  const clearChatSelections = useCallback(() => {
    setSelectedFilesForChat([]);
    setSelectedNotesForChat([]);
  }, []);

  // 获取所有选中的项目
  const getAllSelectedItems = useCallback(() => {
    return [...selectedFilesForChat, ...selectedNotesForChat];
  }, [selectedFilesForChat, selectedNotesForChat]);

  // 分支相关功能
  const branchAPI = {
    // 创建分支
    createBranch: useCallback(async (conversationId, branchData) => {
      try {
        const response = await chatAPI.branches.createBranch(conversationId, branchData);
        return response;
      } catch (error) {
        console.error("ChatContext: Error creating branch", error);
        throw error;
      }
    }, []),

    // 获取分支列表
    getBranches: useCallback(async (conversationId) => {
      try {
        const response = await chatAPI.branches.getBranches(conversationId);
        return response;
      } catch (error) {
        console.error("ChatContext: Error getting branches", error);
        throw error;
      }
    }, []),

    // 切换分支
    switchBranch: useCallback(async (conversationId, switchData) => {
      try {
        await chatAPI.branches.switchBranch(conversationId, switchData);
        // 重新加载对话以获取分支切换后的状态
        await loadConversation(conversationId);
      } catch (error) {
        console.error("ChatContext: Error switching branch", error);
        throw error;
      }
    }, [loadConversation]),

    // 合并分支
    mergeBranch: useCallback(async (conversationId, mergeData) => {
      try {
        const response = await chatAPI.branches.mergeBranch(conversationId, mergeData);
        // 重新加载对话以获取合并后的状态
        await loadConversation(conversationId);
        return response;
      } catch (error) {
        console.error("ChatContext: Error merging branch", error);
        throw error;
      }
    }, [loadConversation]),

    // 删除分支
    deleteBranch: useCallback(async (conversationId, branchName) => {
      try {
        await chatAPI.branches.deleteBranch(conversationId, branchName);
      } catch (error) {
        console.error("ChatContext: Error deleting branch", error);
        throw error;
      }
    }, []),
  };

  const value = {
    // 状态
    selectedFilesForChat,
    selectedNotesForChat,
    currentConversation,
    conversations,
    loadingConversations,
    sendingMessage,
    
    // 对话管理
    loadConversations,
    createConversation,
    loadConversation,
    sendMessage,
    regenerateMessage,
    deleteConversation,
    updateConversation,
    
    // 文件管理
    addFilesToChat,
    addNotesToChat,
    removeFileFromChat,
    removeNoteFromChat,
    clearChatSelections,
    getAllSelectedItems,
    
    // 分支管理
    branches: branchAPI,
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}; 