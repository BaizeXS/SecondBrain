import React, { createContext, useState, useContext, useCallback } from 'react';

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const [selectedFilesForChat, setSelectedFilesForChat] = useState([]);
  const [selectedNotesForChat, setSelectedNotesForChat] = useState([]);

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

  const value = {
    selectedFilesForChat,
    selectedNotesForChat,
    addFilesToChat,
    addNotesToChat,
    removeFileFromChat,
    removeNoteFromChat,
    clearChatSelections,
    getAllSelectedItems,
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