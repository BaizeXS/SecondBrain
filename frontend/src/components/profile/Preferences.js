// src/components/profile/Preferences.js (新建文件)
import React, { useState } from 'react';
import styles from './ProfileComponents.module.css';
import { FiSun, FiMoon, FiMonitor, FiGlobe, FiSettings } from 'react-icons/fi';

const Preferences = () => {
  // 实际应用中，这些状态应该来自一个全局的 ThemeContext 或 SettingsContext
  const [theme, setTheme] = useState('system'); // 'light', 'dark', 'system'
  const [language, setLanguage] = useState('en'); // 'en', 'zh', etc.

  const handleThemeChange = (selectedTheme) => {
    setTheme(selectedTheme);
    // 这里会调用 context 的 setTheme(selectedTheme) 来改变整个应用的主题
    // 并且将选择保存到 localStorage
    console.log("Theme changed to:", selectedTheme);
    // document.documentElement.setAttribute('data-theme', selectedTheme); // 一种实现主题切换的方式
  };

  return (
    <div className={styles.profileSection}>
      <div className={styles.sectionHeader}>
        <h3><FiSettings /> Appearance & Language</h3>
      </div>
      <div className={styles.formContent}>
        {/* 主题选择 */}
        <div className={styles.formGroup}>
          <label>Theme</label>
          <div className={styles.themeSelector}>
            <button
              onClick={() => handleThemeChange('light')}
              className={`${styles.themeOption} ${theme === 'light' ? styles.active : ''}`}
            >
              <FiSun /> Light
            </button>
            <button
              onClick={() => handleThemeChange('dark')}
              className={`${styles.themeOption} ${theme === 'dark' ? styles.active : ''}`}
            >
              <FiMoon /> Dark
            </button>
            <button
              onClick={() => handleThemeChange('system')}
              className={`${styles.themeOption} ${theme === 'system' ? styles.active : ''}`}
            >
              <FiMonitor /> System
            </button>
          </div>
        </div>

        {/* 语言选择 */}
        <div className={styles.formGroup}>
          <label htmlFor="languageSelect"><FiGlobe /> Language</label>
          <select
            id="languageSelect"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className={styles.selectField}
          >
            <option value="en">English</option>
            <option value="zh">简体中文</option>
            {/* ... other languages */}
          </select>
        </div>
      </div>
    </div>
  );
};

export default Preferences;