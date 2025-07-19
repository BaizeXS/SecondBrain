// src/pages/SettingsPage.js (新建文件)
import React, { useState } from 'react';
import styles from './SettingsPage.module.css'; // 新建 CSS
import GlobalApiSettings from '../components/settings/GlobalApiSettings';
import { FiCloud, FiCpu, FiMonitor, FiInfo } from 'react-icons/fi';
import DataSyncSettings from '../components/settings/DataSyncSettings';
import AppearanceSettings from '../components/settings/AppearanceSettings';
import AboutSection from '../components/settings/AboutSection';

// 临时占位符组件
const PlaceholderSettingsComponent = ({ title }) => (
  <div className={styles.contentSection}>
    <h2>{title}</h2>
    <p>Settings and options for this category will be available here soon.</p>
  </div>
);


const SettingsPage = () => {
  const [activeTab, setActiveTab] = useState('api'); // 'api', 'data', 'appearance', 'about'

  // 左侧导航菜单项
  const navItems = [
    { key: 'api', label: 'Global API', icon: <FiCpu /> },
    { key: 'data', label: 'Data & Sync', icon: <FiCloud /> },
    { key: 'appearance', label: 'Appearance', icon: <FiMonitor /> },
    { key: 'about', label: 'About', icon: <FiInfo /> },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'api':
        return <GlobalApiSettings />;
      case 'data':
        return <DataSyncSettings />;
      case 'appearance':
        return <AppearanceSettings />;
      case 'about':
        return <AboutSection />;
      default:
        return <GlobalApiSettings />;
    }
  };

  return (
    <div className={styles.settingsPage}>
      <h1 className={styles.pageTitle}>Settings</h1>
      <div className={styles.settingsLayout}>
        {/* 左侧导航栏 */}
        <aside className={styles.settingsNav}>
          {navItems.map(item => (
            <button
              key={item.key}
              onClick={() => setActiveTab(item.key)}
              className={`${styles.navItem} ${activeTab === item.key ? styles.active : ''}`}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </aside>

        {/* 右侧内容区 */}
        <main className={styles.settingsContent}>
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default SettingsPage;