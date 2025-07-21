import React from 'react';
import styles from './MessageTimestamp.module.css';

const MessageTimestamp = ({ timestamp, className = '' }) => {
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);

    // 如果是今天
    if (diffInDays === 0) {
      if (diffInMinutes < 1) {
        return '刚刚';
      } else if (diffInMinutes < 60) {
        return `${diffInMinutes}分钟前`;
      } else {
        return `${diffInHours}小时前`;
      }
    }
    
    // 如果是昨天
    if (diffInDays === 1) {
      return `昨天 ${date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      })}`;
    }
    
    // 如果是本周内
    if (diffInDays < 7) {
      const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
      return `周${weekdays[date.getDay()]} ${date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      })}`;
    }
    
    // 更早的日期
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  const getDetailedTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  if (!timestamp) {
    return null;
  }

  return (
    <span 
      className={`${styles.timestamp} ${className}`}
      title={getDetailedTimestamp(timestamp)}
    >
      {formatTimestamp(timestamp)}
    </span>
  );
};

export default MessageTimestamp; 