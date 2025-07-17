// src/components/settings/AppearanceSettings.js
import React, { useState } from 'react';
import styles from './SettingsComponents.module.css'; // 我们将在这个文件中添加新样式
import { FiSun, FiMoon, FiMonitor, FiType, FiSidebar, FiChevronsLeft, FiChevronsRight, FiEye } from 'react-icons/fi';
import { useSidebar } from '../../contexts/SidebarContext'; // 用于侧边栏行为设置

const AppearanceSettings = () => {
  // 实际应用中，这些状态应该来自一个全局的 SettingsContext 或 ThemeContext
  const [theme, setTheme] = useState('system'); // 'light', 'dark', 'system'
  const [fontSize, setFontSize] = useState('medium'); // 'small', 'medium', 'large'
  const [fontFamily, setFontFamily] = useState('system'); // 'system', 'serif', 'sans-serif'
  const [layoutDensity, setLayoutDensity] = useState('comfortable'); // 'comfortable', 'compact'

  const { isLeftSidebarOpen, toggleLeftSidebar } = useSidebar(); // 获取侧边栏状态

  const handleThemeChange = (selectedTheme) => {
    setTheme(selectedTheme);
    console.log("Theme changed to:", selectedTheme);
    // TODO: 调用 context.setTheme(selectedTheme) 来改变整个应用的主题
  };

  const handleFontSizeChange = (e) => {
    const newSize = e.target.value;
    setFontSize(newSize);
    console.log("Font size changed to:", newSize);
    // TODO: 调用 context.setFontSize(newSize)
  };

  const handleFontFamilyChange = (e) => {
    const newFontFamily = e.target.value;
    setFontFamily(newFontFamily);
    console.log("Font family changed to:", newFontFamily);
    // TODO: 调用 context.setFontFamily(newFontFamily)
  };

  return (
    <div className={styles.settingsSection}>
      <div className={styles.sectionHeader}><h3><FiEye /> Appearance</h3></div>
      <div className={styles.sectionContent}>

        {/* --- 主题选择 --- */}
        <div className={styles.settingGroup}>
          <h4 className={styles.settingTitle}>Theme</h4>
          <p className={styles.settingDescription}>Choose how Second Brain looks to you. Select a theme or sync with your system.</p>
          <div className={styles.themeCardsContainer}>
            <div className={`${styles.themeCard} ${styles.lightPreview} ${theme === 'light' ? styles.active : ''}`} onClick={() => handleThemeChange('light')}>
              <div className={styles.themeCardCheck}>✔</div>
              <FiSun /> Light
            </div>
            <div className={`${styles.themeCard} ${styles.darkPreview} ${theme === 'dark' ? styles.active : ''}`} onClick={() => handleThemeChange('dark')}>
              <div className={styles.themeCardCheck}>✔</div>
              <FiMoon /> Dark
            </div>
            <div className={`${styles.themeCard} ${styles.systemPreview} ${theme === 'system' ? styles.active : ''}`} onClick={() => handleThemeChange('system')}>
              <div className={styles.themeCardCheck}>✔</div>
              <FiMonitor /> System
            </div>
          </div>
        </div>

        {/* --- 字体设置 --- */}
        <div className={styles.settingGroup}>
          <h4 className={styles.settingTitle}>Typography</h4>
          <p className={styles.settingDescription}>Adjust the font settings for better readability.</p>
          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label htmlFor="fontSizeSelect"><FiType /> Font Size</label>
              <select id="fontSizeSelect" value={fontSize} onChange={handleFontSizeChange} className={styles.selectField}>
                <option value="small">Small</option>
                <option value="medium">Medium (Default)</option>
                <option value="large">Large</option>
              </select>
            </div>
            <div className={styles.formGroup}>
              <label htmlFor="fontFamilySelect">Content Font</label>
              <select id="fontFamilySelect" value={fontFamily} onChange={handleFontFamilyChange} className={styles.selectField}>
                <option value="system">System Default</option>
                <option value="sans-serif">Sans-Serif</option>
                <option value="serif">Serif</option>
              </select>
            </div>
          </div>
          <div className={`${styles.fontPreview} ${styles[`fontSize-${fontSize}`]} ${styles[`fontFamily-${fontFamily}`]}`}>
            This is how your text will look. The quick brown fox jumps over the lazy dog.
          </div>
        </div>

        {/* --- 布局密度 --- */}
        <div className={styles.settingGroup}>
          <h4 className={styles.settingTitle}><FiSidebar /> Layout Density</h4>
          <p className={styles.settingDescription}>Choose a more spacious or a more compact layout for lists and items.</p>
          <div className={styles.segmentedControl}>
            <button onClick={() => setLayoutDensity('comfortable')} className={layoutDensity === 'comfortable' ? styles.active : ''}>
              Comfortable
            </button>
            <button onClick={() => setLayoutDensity('compact')} className={layoutDensity === 'compact' ? styles.active : ''}>
              Compact
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AppearanceSettings;