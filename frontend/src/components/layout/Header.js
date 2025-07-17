// src/components/layout/Header.js
import React from 'react';
import styles from './Header.module.css';
import appLogo from '../../assets/images/app-logo.png'; // 全局应用 logo
// import { useSidebar } from '../../contexts/SidebarContext'; // 不再需要 toggleLeftSidebar

const Header = () => {
  // const { isLeftSidebarOpen } = useSidebar(); // 如果需要根据状态改变头部其他样式可以保留

  return (
    <header className={styles.appHeader}>
      <div className={styles.headerLeft}>
        {/* 伸缩按钮已移除 */}
        <img src={appLogo} alt="Second Brain Logo" className={styles.headerLogo} />
        <span className={styles.headerAppName}>Second Brain</span>
      </div>
      <div className={styles.headerRight}>
        {/* 语言切换等 */}
      </div>
    </header>
  );
};

export default Header;