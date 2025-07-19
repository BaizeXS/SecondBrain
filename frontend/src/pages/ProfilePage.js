// src/pages/ProfilePage.js (新建文件)
import React, { useState } from 'react';
import styles from './ProfilePage.module.css'; // 新建 CSS
import UserProfile from '../components/profile/UserProfile';
import UsageStats from '../components/profile/UsageStats';
import { useAuth } from '../contexts/AuthContext';
import { FiUser, FiShield, FiSettings } from 'react-icons/fi';
import AccountSettings from '../components/profile/AccountSettings';

// 临时占位符组件
const PlaceholderComponent = ({ title }) => (
  <div style={{ padding: '20px', border: '1px dashed #ccc', borderRadius: '8px' }}>
    <h2>{title}</h2>
    <p>Content for this section will be implemented here.</p>
  </div>
);


const ProfilePage = () => {
  const { user } = useAuth(); // 从 AuthContext 获取用户信息
  const [activeTab, setActiveTab] = useState('profile'); // 'profile', 'account', 'preferences'

  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
        return (
          <>
            <UserProfile />
            <UsageStats />
          </>
        );
      case 'account':
        return <AccountSettings />; // <<< 使用新组件
      default:
        return (
          <>
            <UserProfile />
            <UsageStats />
          </>
        );
    }
  };

  if (!user) {
    return <div className={styles.loading}>Loading user data...</div>;
  }

  return (
    <div className={styles.profilePage}>
      {/* 顶部用户概览 */}
      <header className={styles.profileHeader}>
        <div className={styles.avatarContainer}>
          <img src={`https://i.pravatar.cc/100?u=${user.id}`} alt="User Avatar" className={styles.avatar} />
          {/* 未来这里可以添加一个上传按钮 */}
        </div>
        <div className={styles.userInfo}>
          <h1 className={styles.username}>{user.username || 'Test User'}</h1>
          <p className={styles.email}>{user.email}</p>
          {/* <p className={styles.memberSince}>Member since January 2024</p> */}
        </div>
      </header>

      {/* 标签页导航 */}
      <nav className={styles.profileNav}>
        <button
          onClick={() => setActiveTab('profile')}
          className={`${styles.navButton} ${activeTab === 'profile' ? styles.active : ''}`}
        >
          <FiUser /> Profile & Stats
        </button>
        <button
          onClick={() => setActiveTab('account')}
          className={`${styles.navButton} ${activeTab === 'account' ? styles.active : ''}`}
        >
          <FiShield /> Account
        </button>
      </nav>

      {/* 标签页内容区 */}
      <main className={styles.profileContent}>
        {renderContent()}
      </main>
    </div>
  );
};

export default ProfilePage;