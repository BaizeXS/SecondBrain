import React, { useState } from 'react';
import { FiCopy, FiCheck, FiRefreshCw, FiThumbsUp, FiThumbsDown, FiMoreHorizontal } from 'react-icons/fi';
import styles from './MessageActions.module.css';

const MessageActions = ({ 
  message, 
  onCopy, 
  onRegenerate, 
  onFeedback,
  isAiMessage = false,
  isLastMessage = false,
  className = ''
}) => {
  const [copied, setCopied] = useState(false);
  const [showActions, setShowActions] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.text);
      if (onCopy) onCopy(message);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy message:', error);
    }
  };

  const handleRegenerate = () => {
    if (onRegenerate) onRegenerate(message);
  };

  const handleFeedback = (type) => {
    if (onFeedback) onFeedback(message, type);
  };

  return (
    <div className={`${styles.messageActions} ${className}`}>
      {/* 主要操作按钮 */}
      <div className={styles.primaryActions}>
        <button
          className={styles.actionButton}
          onClick={handleCopy}
          title="复制消息"
        >
          {copied ? <FiCheck className={styles.successIcon} /> : <FiCopy />}
        </button>

        {isAiMessage && isLastMessage && (
          <button
            className={styles.actionButton}
            onClick={handleRegenerate}
            title="重新生成"
          >
            <FiRefreshCw />
          </button>
        )}

        {isAiMessage && (
          <>
            <button
              className={styles.actionButton}
              onClick={() => handleFeedback('like')}
              title="点赞"
            >
              <FiThumbsUp />
            </button>
            <button
              className={styles.actionButton}
              onClick={() => handleFeedback('dislike')}
              title="点踩"
            >
              <FiThumbsDown />
            </button>
          </>
        )}

        <button
          className={styles.actionButton}
          onClick={() => setShowActions(!showActions)}
          title="更多操作"
        >
          <FiMoreHorizontal />
        </button>
      </div>

      {/* 扩展操作菜单 */}
      {showActions && (
        <div className={styles.extendedActions}>
          <div className={styles.actionMenu}>
            <button
              className={styles.menuItem}
              onClick={() => {
                // TODO: 实现编辑功能
                setShowActions(false);
              }}
            >
              编辑消息
            </button>
            <button
              className={styles.menuItem}
              onClick={() => {
                // TODO: 实现分享功能
                setShowActions(false);
              }}
            >
              分享消息
            </button>
            <button
              className={styles.menuItem}
              onClick={() => {
                // TODO: 实现删除功能
                setShowActions(false);
              }}
            >
              删除消息
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageActions; 