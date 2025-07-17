// src/components/layout/MainLayout.js
import React from 'react';
import Header from './Header'; // 你应该有这个文件
import LeftSidebar from './LeftSidebar'; // 你应该有这个文件
import RightSidebar from './RightSidebar'; // 你应该有这个文件
import { useSidebar } from '../../contexts/SidebarContext';
import styles from './MainLayout.module.css';

const MainLayout = ({ children, showAppHeader = true }) => {
  const { isLeftSidebarOpen, isRightSidebarOpen } = useSidebar();

  let mainContentClasses = [styles.mainContent];
  if (isLeftSidebarOpen) {
    mainContentClasses.push(styles.leftSidebarOpen);
  }
  if (isRightSidebarOpen) {
    mainContentClasses.push(styles.rightSidebarOpen);
  }


  return (
    <div className={styles.mainLayout}>
      {showAppHeader && <Header />} {/* Header 组件负责自己的伸缩按钮逻辑 */}
      <div className={styles.contentArea}>
        <LeftSidebar /> {/* LeftSidebar 组件自身根据 isLeftSidebarOpen 决定展开或收起样式 */}
        <main className={mainContentClasses.join(' ')}>
          {children}
        </main>
        <RightSidebar />
      </div>
    </div>
  );
};

export default MainLayout;