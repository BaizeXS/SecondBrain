// src/components/chat/MessageFileAttachments.js (新建文件)
import React, { useState } from 'react';
import styles from './MessageFileAttachments.module.css'; // 我们将为此创建新的CSS
import { FiFileText, FiEdit3 } from 'react-icons/fi';

const MAX_FILES_PER_ROW = 4;
const MAX_ROWS_BEFORE_COLLAPSE = 1;
const MAX_VISIBLE_FILES_COLLAPSED = MAX_FILES_PER_ROW * MAX_ROWS_BEFORE_COLLAPSE;

const MessageFileAttachments = ({ files = [], notes = [], isAiMessage = false }) => {
  const [showAll, setShowAll] = useState(false);

  // 合并文件和笔记
  const allAttachments = [
    ...files.map(file => ({ ...file, type: 'file' })),
    ...notes.map(note => ({ ...note, type: 'note' }))
  ];

  if (!allAttachments || allAttachments.length === 0) {
    return null;
  }

  const visibleAttachments = showAll ? allAttachments : allAttachments.slice(0, MAX_VISIBLE_FILES_COLLAPSED);
  const needsCollapseButton = allAttachments.length > MAX_VISIBLE_FILES_COLLAPSED && !showAll;

  // 如果附件总数小于等于折叠阈值，或者已经点击了查看全部，则直接显示所有附件
  const attachmentsToDisplay = (allAttachments.length <= MAX_VISIBLE_FILES_COLLAPSED || showAll)
    ? allAttachments
    : allAttachments.slice(0, MAX_VISIBLE_FILES_COLLAPSED - (allAttachments.length > MAX_VISIBLE_FILES_COLLAPSED ? 1 : 0)); // 如果需要按钮，少显示一个附件

  return (
    <div className={`${styles.attachmentsContainer} ${isAiMessage ? styles.aiAttachments : ''}`}>
      {attachmentsToDisplay.map(attachment => (
        <div key={attachment.id || attachment.name} className={`${styles.fileAttachmentCard} ${attachment.type === 'note' ? styles.noteAttachmentCard : ''}`}>
          {attachment.type === 'note' ? (
            <FiEdit3 className={styles.fileIcon} />
          ) : (
            <FiFileText className={styles.fileIcon} />
          )}
          <div className={styles.fileInfo}>
            <span className={styles.fileName}>
              {attachment.name}
            </span>
            <span className={styles.fileMeta}>
              {attachment.type === 'note' 
                ? 'Note' 
                : `${attachment.type?.split('/')[1] || 'File'} · ${(attachment.size / 1024).toFixed(1)} KB`
              }
            </span>
            {attachment.isAiGenerated && (
              <div className={styles.aiGeneratedTag}>
                <span className={styles.aiTagText}>AI</span>
                {attachment.aiAgent && <span className={styles.aiAgentText}>by {attachment.aiAgent}</span>}
              </div>
            )}
            <div className={styles.creatorInfo}>
              <span className={styles.creatorLabel}>Creator:</span>
              <span className={`${styles.creatorValue} ${attachment.isAiGenerated ? styles.creatorAi : styles.creatorUser}`}>
                {attachment.isAiGenerated ? 'AI' : 'User'}
              </span>
            </div>
          </div>
        </div>
      ))}
      {needsCollapseButton && (
        <button
          onClick={() => setShowAll(true)}
          className={`${styles.fileAttachmentCard} ${styles.viewAllButton}`}
        >
          查看所有 ({allAttachments.length})
        </button>
      )}
      {showAll && allAttachments.length > MAX_VISIBLE_FILES_COLLAPSED && ( // 如果展开了且附件确实多，可以加个收起按钮
        <button
          onClick={() => setShowAll(false)}
          className={`${styles.fileAttachmentCard} ${styles.viewAllButton} ${styles.collapseButton}`} // 可以复用样式或新建
        >
          收起
        </button>
      )}
    </div>
  );
};

export default MessageFileAttachments;