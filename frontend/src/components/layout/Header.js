// src/components/layout/Header.js
import React from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './Header.module.css';
import appLogo from '../../assets/images/app-logo.png'; // 全局应用 logo
import { useAuth } from '../../contexts/AuthContext';
import { FiUser, FiLogOut } from 'react-icons/fi';

const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleProfileClick = () => {
    navigate('/profile');
  };

  return (
    <header className={styles.appHeader}>
      <div className={styles.headerLeft}>
        {/* 伸缩按钮已移除 */}
        <img src={appLogo} alt="Second Brain Logo" className={styles.headerLogo} />
        <span className={styles.headerAppName}>Second Brain</span>
      </div>
      <div className={styles.headerRight}>
        {user && (
          <div className={styles.userSection}>
            <button 
              className={styles.userButton}
              onClick={handleProfileClick}
              title="Profile"
            >
              <FiUser />
              <span className={styles.username}>{user.username || user.email}</span>
            </button>
            <button 
              className={styles.logoutButton}
              onClick={handleLogout}
              title="Logout"
            >
              <FiLogOut />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;