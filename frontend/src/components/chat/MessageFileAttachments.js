// src/components/chat/MessageFileAttachments.js (新建文件)
import React, { useState } from 'react';
import styles from './MessageFileAttachments.module.css'; // 我们将为此创建新的CSS
import { FiFileText } from 'react-icons/fi';

const MAX_FILES_PER_ROW = 4;
const MAX_ROWS_BEFORE_COLLAPSE = 1;
const MAX_VISIBLE_FILES_COLLAPSED = MAX_FILES_PER_ROW * MAX_ROWS_BEFORE_COLLAPSE;

const MessageFileAttachments = ({ files, isAiMessage = false }) => {
  const [showAll, setShowAll] = useState(false);

  if (!files || files.length === 0) {
    return null;
  }

  const visibleFiles = showAll ? files : files.slice(0, MAX_VISIBLE_FILES_COLLAPSED);
  const needsCollapseButton = files.length > MAX_VISIBLE_FILES_COLLAPSED && !showAll;

  // 如果文件总数小于等于折叠阈值，或者已经点击了查看全部，则直接显示所有文件
  const filesToDisplay = (files.length <= MAX_VISIBLE_FILES_COLLAPSED || showAll)
    ? files
    : files.slice(0, MAX_VISIBLE_FILES_COLLAPSED - (files.length > MAX_VISIBLE_FILES_COLLAPSED ? 1 : 0)); // 如果需要按钮，少显示一个文件

  return (
    <div className={`${styles.attachmentsContainer} ${isAiMessage ? styles.aiAttachments : ''}`}>
      {filesToDisplay.map(file => (
        <div key={file.id || file.name} className={styles.fileAttachmentCard}>
          <FiFileText className={styles.fileIcon} />
          <div className={styles.fileInfo}>
            <span className={styles.fileName}>{file.name}</span>
            <span className={styles.fileMeta}>
              {file.type?.split('/')[1] || 'File'} · {(file.size / 1024).toFixed(1)} KB
            </span>
          </div>
        </div>
      ))}
      {needsCollapseButton && (
        <button
          onClick={() => setShowAll(true)}
          className={`${styles.fileAttachmentCard} ${styles.viewAllButton}`}
        >
          查看所有 ({files.length})
        </button>
      )}
      {showAll && files.length > MAX_VISIBLE_FILES_COLLAPSED && ( // 如果展开了且文件确实多，可以加个收起按钮
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