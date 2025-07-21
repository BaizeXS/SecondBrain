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

  // 🆕 重新构建：简单而可靠的文件处理逻辑
  const processFileForChat = useCallback((file) => {
    console.log(`🔄 ChatContext: Processing file for chat:`, {
      name: file.name,
      id: file.id,
      size: file.size,
      type: file.type,
      hasRawFile: !!file.rawFile,
      hasUrl: !!file.url,
      documentId: file.documentId,
      allKeys: Object.keys(file)
    });

    // 策略1: 优先使用已存在的documentId字段
    if (file.documentId && !isNaN(parseInt(file.documentId)) && parseInt(file.documentId) > 0) {
      const documentId = parseInt(file.documentId);
      console.log(`✅ ChatContext: Using existing document ID ${documentId} for file: ${file.name}`);
      return {
        ...file,
        documentId: documentId,
        readyForChat: true,
        processingResult: 'success',
        processingNote: `Ready with existing document ID: ${documentId}`
      };
    }

    // 策略2: 直接使用有效的数字ID（字符串或数字）
    if (file.id && !isNaN(parseInt(file.id)) && parseInt(file.id) > 0) {
      const documentId = parseInt(file.id);
      console.log(`✅ ChatContext: Using document ID ${documentId} for file: ${file.name}`);
      return {
        ...file,
        documentId: documentId,
        readyForChat: true,
        processingResult: 'success',
        processingNote: `Ready with document ID: ${documentId}`
      };
    }

    // 策略2.5: 处理已上传但上传失败的文件
    if (file.uploadFailed) {
      console.error(`❌ ChatContext: File ${file.name} has upload failure flag`);
      return {
        ...file,
        documentId: null,
        readyForChat: false,
        processingResult: 'failed',
        processingNote: `上传失败：${file.uploadError || '未知错误'}。请重新上传此文件。`
      };
    }

    // 策略3: 处理local-前缀的文件ID，尝试从中提取数字ID
    if (file.id && typeof file.id === 'string' && file.id.startsWith('local-')) {
      console.log(`🔧 ChatContext: Processing local file ID: ${file.id}`);
      
      // 尝试从local ID中提取时间戳或其他数字标识符
      const timestampMatch = file.id.match(/local-.*?-(\d+)/);
      if (timestampMatch && timestampMatch[1]) {
        // 对于local文件，我们将其标记为需要上传，除非它有其他可用数据
        if (file.rawFile && file.rawFile instanceof File) {
          console.log(`📤 ChatContext: Local file ${file.name} has rawFile, will need upload`);
          return {
            ...file,
            documentId: null,
            readyForChat: true,
            needsUpload: true,
            processingResult: 'needs_upload',
            processingNote: 'File will be uploaded when message is sent'
          };
        }
        
        // 如果没有rawFile，但是是local文件，检查是否有其他标识符
        if (file.url && file.url.includes('/documents/')) {
          const urlMatch = file.url.match(/\/documents\/(\d+)/);
          if (urlMatch) {
            const urlDocId = parseInt(urlMatch[1]);
            console.log(`🔧 ChatContext: Recovered document ID ${urlDocId} from URL for local file: ${file.name}`);
            return {
              ...file,
              documentId: urlDocId,
              readyForChat: true,
              processingResult: 'recovered_from_url',
              processingNote: `Recovered document ID from URL: ${urlDocId}`
            };
          }
        }
        
        // 如果是local文件但没有rawFile和有效URL，标记为失败并提供明确的解决方案
        console.error(`❌ ChatContext: Local file ${file.name} has no rawFile or valid URL`);
        return {
          ...file,
          documentId: null,
          readyForChat: false,
          processingResult: 'failed',
          processingNote: '文件数据丢失。解决方案：1) 删除此文件并重新上传；2) 或使用聊天框的回形针按钮重新添加文件'
        };
      }
    }

    // 策略4: 处理有rawFile的本地文件 
    if (file.rawFile && file.rawFile instanceof File) {
      console.log(`📤 ChatContext: File ${file.name} has rawFile, will need upload`);
      return {
        ...file,
        documentId: null,
        readyForChat: true,
        needsUpload: true,
        processingResult: 'needs_upload',
        processingNote: 'File will be uploaded when message is sent'
      };
    }

    // 策略5: 尝试从URL恢复ID
    if (file.url && file.url.includes('/documents/')) {
      const urlMatch = file.url.match(/\/documents\/(\d+)/);
      if (urlMatch) {
        const urlDocId = parseInt(urlMatch[1]);
        console.log(`🔧 ChatContext: Recovered document ID ${urlDocId} from URL for file: ${file.name}`);
        return {
          ...file,
          id: urlDocId.toString(),
          documentId: urlDocId,
          readyForChat: true,
          processingResult: 'recovered_from_url',
          processingNote: `Recovered document ID from URL: ${urlDocId}`
        };
      }
    }

    // 策略6: 无法处理的文件
    console.error(`❌ ChatContext: Cannot process file ${file.name}:`, {
      id: file.id,
      hasRawFile: !!file.rawFile,
      hasUrl: !!file.url,
      url: file.url,
      documentId: file.documentId,
      processingStrategiesTried: [
        'existing_documentId',
        'numeric_id',
        'local_prefix_extraction', 
        'rawFile_upload',
        'url_recovery'
      ]
    });
    
    return {
      ...file,
      documentId: null,
      readyForChat: false,
      processingResult: 'failed',
      processingNote: '文件数据不完整。建议：1) 检查文件是否正确上传到项目；2) 重新上传文件；3) 确认文件在列表中正常显示后再次尝试。'
    };
  }, []);

  // 🆕 重新构建：添加文件到聊天的主函数
  const addFilesToChat = useCallback((files) => {
    if (!files || files.length === 0) {
      console.warn('ChatContext: No files provided to addFilesToChat');
      return;
    }

    console.log('🚀 ChatContext: Adding files to chat, count:', files.length);
    console.log('📋 ChatContext: Input files:', files.map(f => ({
      name: f.name,
      id: f.id,
      size: f.size,
      hasRawFile: !!f.rawFile,
      hasUrl: !!f.url,
      documentId: f.documentId
    })));

    // 处理每个文件
    const processedFiles = files.map(processFileForChat);
    
    // 分类处理结果
    const successfulFiles = processedFiles.filter(f => f.readyForChat);
    const failedFiles = processedFiles.filter(f => !f.readyForChat);
    
    // 进一步细分成功文件
    const readyFiles = successfulFiles.filter(f => 
      f.processingResult === 'success' || 
      f.processingResult === 'recovered_from_url' ||
      f.processingResult === 'needs_upload'
    );
    const alternativeFiles = successfulFiles.filter(f => 
      f.processingResult === 'needs_alternative'
    );
    
    console.log('📊 ChatContext: Processing results:');
    console.log('  ✅ Ready files:', readyFiles.length);
    console.log('  ⚠️ Alternative handling files:', alternativeFiles.length);
    console.log('  ❌ Failed files:', failedFiles.length);
    
    // 添加所有成功处理的文件到聊天（包括需要特殊处理的）
    if (successfulFiles.length > 0) {
      setSelectedFilesForChat(prev => {
        const newFiles = successfulFiles.filter(file => 
          !prev.some(existing => existing.id === file.id)
        );
        const updatedFiles = [...prev, ...newFiles];
        console.log('📁 ChatContext: Updated selectedFilesForChat, total count:', updatedFiles.length);
        return updatedFiles;
      });
    }
    
    // 显示处理结果提示
    if (readyFiles.length > 0 && alternativeFiles.length === 0 && failedFiles.length === 0) {
      // 全部成功，简单提示
      const successNames = readyFiles.map(f => f.name).join(', ');
      setTimeout(() => {
        alert(`✅ 成功添加 ${readyFiles.length} 个文件到聊天中：\n\n${successNames}\n\n现在您可以发送消息了。`);
      }, 100);
    } else if (successfulFiles.length > 0) {
      // 有成功的文件，但也有问题文件，显示详细信息
      let message = '';
      
      if (readyFiles.length > 0) {
        const readyNames = readyFiles.map(f => f.name).join(', ');
        message += `✅ ${readyFiles.length} 个文件添加成功：\n${readyNames}\n\n`;
      }
      
      if (alternativeFiles.length > 0) {
        const altNames = alternativeFiles.map(f => f.name).join(', ');
        message += `⚠️ ${alternativeFiles.length} 个文件需要特殊处理：\n${altNames}\n`;
        message += '这些文件已添加到聊天，但可能无法被AI直接读取。\n建议重新上传这些文件以获得最佳体验。\n\n';
      }
      
      if (failedFiles.length > 0) {
        const failedNames = failedFiles.map(f => f.name).join(', ');
        message += `❌ ${failedFiles.length} 个文件添加失败：\n${failedNames}\n\n`;
        message += '失败原因及解决方案:\n';
        failedFiles.forEach(file => {
          message += `• ${file.name}: ${file.processingNote}\n`;
        });
      }
      
      if (successfulFiles.length > 0) {
        message += '\n您现在可以发送消息了。';
      }
      
      const delay = 100;
      setTimeout(() => alert(message), delay);
    }
    
    // 如果没有任何文件成功，只显示错误信息
    if (successfulFiles.length === 0 && failedFiles.length > 0) {
      const failedNames = failedFiles.map(f => f.name).join(', ');
      console.warn(`❌ ChatContext: All files failed to process: ${failedNames}`);
      
      let errorMessage = `❌ 文件无法添加到聊天\n\n`;
      errorMessage += `文件: ${failedNames}\n\n`;
      errorMessage += '💡 立即解决方案:\n';
      errorMessage += '1️⃣ 删除当前文件：在文件列表中右键点击该文件，选择"删除"\n';
      errorMessage += '2️⃣ 重新上传：点击 "+" 按钮重新上传同一个文件\n';
      errorMessage += '3️⃣ 重新添加：上传成功后，再次添加到聊天\n\n';
      errorMessage += '🔄 或者使用聊天框的回形针按钮直接上传文件';
      
      setTimeout(() => alert(errorMessage), 100);
    }
  }, [processFileForChat]);

  // 🆕 重新构建：添加笔记到聊天
  const addNotesToChat = useCallback((notes) => {
    if (!notes || notes.length === 0) {
      console.warn('ChatContext: No notes provided to addNotesToChat');
      return;
    }

    console.log('🚀 ChatContext: Adding notes to chat, count:', notes.length);
    
    const processedNotes = notes.map(note => ({
      ...note,
      readyForChat: true,
      processingResult: 'success'
    }));
    
    setSelectedNotesForChat(prev => {
      const newNotes = processedNotes.filter(note => 
        !prev.some(existing => existing.id === note.id)
      );
      const updatedNotes = [...prev, ...newNotes];
      console.log('📝 ChatContext: Updated selectedNotesForChat, total count:', updatedNotes.length);
      return updatedNotes;
    });
    
    const noteNames = processedNotes.map(n => n.name).join(', ');
    setTimeout(() => {
      alert(`✅ 成功添加 ${processedNotes.length} 个笔记到聊天中：\n\n${noteNames}\n\n现在您可以发送消息了。`);
    }, 100);
  }, []);

  // 🆕 重新构建：提取文档ID用于API调用  
  const getDocumentIdsForAPI = useCallback(() => {
    const documentIds = [];
    
    selectedFilesForChat.forEach(file => {
      if (file.documentId && !isNaN(parseInt(file.documentId))) {
        documentIds.push(parseInt(file.documentId));
        console.log(`📋 ChatContext: Adding document ID ${file.documentId} for file: ${file.name}`);
      } else if (file.needsUpload) {
        console.log(`📤 ChatContext: File ${file.name} will be uploaded before API call`);
      }
    });
    
    console.log('🎯 ChatContext: Final document IDs for API:', documentIds);
    return documentIds;
  }, [selectedFilesForChat]);

  // 🆕 重新构建：获取需要上传的文件
  const getFilesNeedingUpload = useCallback(() => {
    const filesToUpload = selectedFilesForChat.filter(file => 
      file.needsUpload && file.rawFile instanceof File
    );
    
    console.log('📤 ChatContext: Files needing upload:', filesToUpload.map(f => f.name));
    return filesToUpload;
  }, [selectedFilesForChat]);

  // 移除文件
  const removeFileFromChat = useCallback((fileId) => {
    setSelectedFilesForChat(prev => prev.filter(f => f.id !== fileId));
    console.log('🗑️ ChatContext: Removed file from chat:', fileId);
  }, []);

  // 移除笔记
  const removeNoteFromChat = useCallback((noteId) => {
    setSelectedNotesForChat(prev => prev.filter(n => n.id !== noteId));
    console.log('🗑️ ChatContext: Removed note from chat:', noteId);
  }, []);

  // 清空所有选中的文件和笔记
  const clearChatSelections = useCallback(() => {
    setSelectedFilesForChat([]);
    setSelectedNotesForChat([]);
    console.log('🧹 ChatContext: Cleared all chat selections');
  }, []);

  const value = {
    // 状态
    selectedFilesForChat,
    selectedNotesForChat,
    currentConversation,
    conversations,
    loadingConversations,
    sendingMessage,
    
    // 新的简化API
    addFilesToChat,
    addNotesToChat,
    removeFileFromChat,
    removeNoteFromChat,
    clearChatSelections,
    getDocumentIdsForAPI,
    getFilesNeedingUpload,
    
    // 状态管理
    setCurrentConversation,
    setConversations,
    setLoadingConversations,
    setSendingMessage
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