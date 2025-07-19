// src/components/settings/AboutSection.js (新建文件)
import React from 'react';
import styles from './SettingsComponents.module.css';
import { FiInfo } from 'react-icons/fi';

const AboutSection = () => {
  // package.json 中的版本号可以通过环境变量注入
  const appVersion = process.env.REACT_APP_VERSION || '1.0.0';

  return (
    <div className={styles.settingsSection}>
      <div className={styles.sectionHeader}><h3><FiInfo /> About Second Brain</h3></div>
      <div className={styles.sectionContent}>
        <div className={styles.aboutInfo}>
          <p><strong>Version:</strong> {appVersion}</p>
          <p><strong>Second Brain</strong> is your intelligent partner for knowledge management and creative exploration, powered by cutting-edge AI.</p>
          <p>This application is built with passion using modern web technologies. For help, feedback, or support, please visit our community or contact us directly.</p>
          <div className={styles.aboutLinks}>
            <a href="/help" target="_blank" rel="noopener noreferrer">Help Center</a>
            <a href="/privacy" target="_blank" rel="noopener noreferrer">Privacy Policy</a>
            <a href="/terms" target="_blank" rel="noopener noreferrer">Terms of Service</a>
          </div>
          <p className={styles.copyright}>© {new Date().getFullYear()} Second Brain. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
};
export default AboutSection;