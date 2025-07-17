// src/components/profile/AccountSettings.js (新建文件)
import React, { useState } from 'react';
import styles from './ProfileComponents.module.css'; // 复用之前的 CSS
import { FiKey, FiLink, FiTrash2, FaGoogle, FaApple } from 'react-icons/fi'; // FaGoogle, FaApple for example

const AccountSettings = () => {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  const handleChangePassword = (e) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordError("All password fields are required.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("New passwords do not match.");
      return;
    }
    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters long.");
      return;
    }

    // --- 后端协作点 ---
    // 这里你需要调用一个后端 API 来修改密码
    // const result = await api.changePassword(currentPassword, newPassword);
    // if (result.success) { ... } else { ... }

    // 模拟成功
    console.log("Password change requested for:", { currentPassword, newPassword });
    setPasswordSuccess("Password changed successfully!");
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
  };

  const handleDeleteAccount = () => {
    const confirmationText = "DELETE MY ACCOUNT";
    const userInput = prompt(
      `This action is irreversible and will permanently delete all your projects, files, and data.\n\nPlease type "${confirmationText}" to confirm.`
    );
    if (userInput === confirmationText) {
      // --- 后端协作点 ---
      // 调用后端 API 删除账户
      // await api.deleteAccount();
      // 删除成功后，需要调用 useAuth() 的 logout 并导航到登录页
      alert("Account deletion initiated. (This is a mock-up)");
      // logout(); navigate('/login');
    } else if (userInput !== null) {
      alert("Confirmation text did not match. Account deletion cancelled.");
    }
  };

  return (
    <>
      {/* 修改密码区域 */}
      <div className={styles.profileSection}>
        <div className={styles.sectionHeader}>
          <h3><FiKey /> Change Password</h3>
        </div>
        <form className={styles.formContent} onSubmit={handleChangePassword}>
          <div className={styles.formGroup}>
            <label htmlFor="currentPassword">Current Password</label>
            <input type="password" id="currentPassword" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} className={styles.inputField} />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="newPassword">New Password</label>
            <input type="password" id="newPassword" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className={styles.inputField} />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="confirmPassword">Confirm New Password</label>
            <input type="password" id="confirmPassword" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className={styles.inputField} />
          </div>
          {passwordError && <p className={styles.errorMessage}>{passwordError}</p>}
          {passwordSuccess && <p className={styles.successMessage}>{passwordSuccess}</p>}
          <div className={styles.formActions}>
            <button type="submit" className={`${styles.actionButton} ${styles.saveButton}`}>Update Password</button>
          </div>
        </form>
      </div>

      {/* 关联账户区域 */}
      <div className={styles.profileSection}>
        <div className={styles.sectionHeader}>
          <h3><FiLink /> Connected Accounts</h3>
        </div>
        <div className={styles.formContent}>
          <p className={styles.sectionDescription}>Connect third-party accounts for faster login.</p>
          {/* 这里可以动态渲染已关联和未关联的账户 */}
          <div className={styles.connectedAccountItem}>
            {/* <FaGoogle size="1.5em" color="#DB4437" /> */}
            <span>Google</span>
            <button className={styles.connectButton} disabled>Connected</button>
          </div>
          <div className={styles.connectedAccountItem}>
            {/* <FaApple size="1.5em" /> */}
            <span>Apple</span>
            <button className={styles.connectButton}>Connect</button>
          </div>
        </div>
      </div>

      {/* 删除账户区域 */}
      <div className={`${styles.profileSection} ${styles.dangerZone}`}>
        <div className={styles.sectionHeader}>
          <h3><FiTrash2 /> Danger Zone</h3>
        </div>
        <div className={styles.formContent}>
          <h4>Delete Account</h4>
          <p className={styles.sectionDescription}>Once you delete your account, there is no going back. Please be certain.</p>
          <button onClick={handleDeleteAccount} className={`${styles.actionButton} ${styles.deleteButton}`}>Delete My Account</button>
        </div>
      </div>
    </>
  );
};

export default AccountSettings;