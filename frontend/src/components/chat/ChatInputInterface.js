// src/components/chat/ChatInputInterface.js
import React, { useState, useEffect, useRef } from 'react';
import styles from './ChatInputInterface.module.css';
import {
  FiPaperclip, FiSend, FiDownload, FiSave,
  FiX,
  FiFileText
} from 'react-icons/fi';
import { IoSparklesOutline } from "react-icons/io5";

// 假设 formatFileSize 和 mockModelsData 在这里定义或从外部导入
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const numBytes = Number(bytes);
  if (isNaN(numBytes) || numBytes === 0) return '0 Bytes';
  const i = Math.floor(Math.log(numBytes) / Math.log(k));
  return parseFloat((numBytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

const defaultMockModels = [
  { id: 'deepseek', name: 'DeepSeek' },
  { id: 'gpt4', name: 'GPT-4' },
];

const ChatInputInterface = ({
  onSendMessage,
  showSaveButton = false,
  showDownloadButton = false,
  showModelSelector = true,
  showDeepSearchButton = true,
  onDownloadChat,
  onSaveChatAsProject,
  onToggleDeepSearch,
  isDeepSearchActive = false,
  currentSelectedModelId,
  onModelChange,
  availableModels = defaultMockModels,
  placeholderText = "Type your message...",
}) => {
  const [message, setMessage] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  // 确保 currentSelectedModelId 有一个有效的初始值
  const [internalSelectedModel, setInternalSelectedModel] = useState(currentSelectedModelId || availableModels[0]?.id || '');

  useEffect(() => {
    if (currentSelectedModelId) {
      setInternalSelectedModel(currentSelectedModelId);
    }
  }, [currentSelectedModelId]);


  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = 150;
      textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
      textareaRef.current.style.overflowY = scrollHeight > maxHeight ? 'auto' : 'hidden';
    }
  }, [message]);

  const handleInputChange = (e) => setMessage(e.target.value);
  const handleFileTrigger = () => fileInputRef.current?.click();

  const handleFileSelection = (event) => {
    const filesFromInput = Array.from(event.target.files);
    if (filesFromInput.length > 0) {
      const newUniqueFiles = [];
      const duplicateFileNamesInThisBatch = [];

      for (const file of filesFromInput) {
        // --- 核心修改：只检查当前预览区是否已存在 ---
        const isInPreview = selectedFiles.some(
          existing => existing.name === file.name && existing.size === file.size
        );

        // 同时检查本次批次中是否重复
        const isInNewBatch = newUniqueFiles.some(
          newFile => newFile.name === file.name && newFile.size === file.size
        );

        if (isInPreview || isInNewBatch) {
          // 如果用户在同一个文件选择框中选了两次同一个文件，或者它已经在预览区了
          duplicateFileNamesInThisBatch.push(file.name);
        } else {
          newUniqueFiles.push(file);
        }
      }

      // 可以选择性地对单次选择的重复项进行提示，或者也静默处理
      if (duplicateFileNamesInThisBatch.length > 0) {
        // 这里的提示是可选的，符合“同一对话轮次不可以重复引用”
        // 如果希望完全静默，可以移除这个 alert
        alert(`File(s) already in preview and were not added again:\n- ${duplicateFileNamesInThisBatch.join('\n- ')}`);
      }


      if (newUniqueFiles.length > 0) {
        const newFileObjects = newUniqueFiles.map(file => ({
          id: `chatinput-local-${file.name}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          name: file.name, size: file.size, type: file.type,
          rawFile: file, // 保持 rawFile 用于发送
          uploadedAt: new Date().toISOString(),
          preview: `Type: ${file.type || 'unknown'}, Size: ${formatFileSize(file.size)}`
        }));
        setSelectedFiles(prev => [...prev, ...newFileObjects]);
      }
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const removeFileFromPreview = (fileId) => {
    setSelectedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const handleInternalSendMessage = () => {
    if (!message.trim() && selectedFiles.length === 0) return;
    onSendMessage(message.trim(), [...selectedFiles]); // 将预览区的文件传递出去
    setMessage('');
    setSelectedFiles([]); // 发送后清空预览区
  };

  const handleInternalModelChange = (e) => {
    const newModelId = e.target.value;
    setInternalSelectedModel(newModelId);
    if (onModelChange) {
      onModelChange(e); // Propagate the event or just the value
    }
  };

  return (
    <div className={styles.chatInputInterfaceSection}>
      {selectedFiles.length > 0 && (
        <div className={styles.selectedFilesPreviewArea}>
          {selectedFiles.map(file => (
            <div key={file.id} className={styles.filePreviewCard}>
              <FiFileText className={styles.filePreviewIcon} />
              <div className={styles.filePreviewInfo}>
                <span className={styles.filePreviewName}>{file.name}</span>
                <span className={styles.filePreviewMeta}> {file.type || 'File'} · {formatFileSize(file.size)} </span>
              </div>
              <button onClick={() => removeFileFromPreview(file.id)} className={styles.filePreviewRemoveBtn} aria-label={`Remove ${file.name}`}> <FiX /> </button>
            </div>
          ))}
        </div>
      )}

      <div className={styles.chatInputWrapper}>
        <button onClick={handleFileTrigger} className={styles.chatIconButtonTopLeft} title="Attach file"> <FiPaperclip /> </button>
        <input type="file" ref={fileInputRef} onChange={handleFileSelection} style={{ display: 'none' }} multiple />
        <textarea
          ref={textareaRef} value={message} onChange={handleInputChange}
          onKeyPress={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleInternalSendMessage(); } }}
          placeholder={placeholderText}
          className={styles.chatTextarea} rows={1}
        />
        <button onClick={handleInternalSendMessage} className={`${styles.chatIconButton} ${styles.sendButton}`} title="Send message"> <FiSend /> </button>
      </div>

      {(showModelSelector || showDownloadButton || showSaveButton || showDeepSearchButton) && (
        <div className={styles.chatInputActions}>
          <div className={styles.actionGroupLeft}>
            {showModelSelector && availableModels && (
              <select value={internalSelectedModel} onChange={handleInternalModelChange} className={styles.modelSelector}>
                {availableModels.map(model => (<option key={model.id} value={model.id}>{model.name}</option>))}
              </select>
            )}
            {showDownloadButton && onDownloadChat && (
              <button onClick={onDownloadChat} className={styles.inputActionButton} title="Download chat"> <FiDownload /> </button>
            )}
            {showSaveButton && onSaveChatAsProject && (
              <button onClick={onSaveChatAsProject} className={styles.inputActionButton} title="Save chat as project"> <FiSave /> </button>
            )}
          </div>
          <div className={styles.actionGroupRight}>
            {showDeepSearchButton && onToggleDeepSearch && (
              <button onClick={onToggleDeepSearch} className={`${styles.inputActionButton} ${isDeepSearchActive ? styles.deepSearchActive : ''}`} title="Toggle Deep Search"> <IoSparklesOutline /> </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatInputInterface;