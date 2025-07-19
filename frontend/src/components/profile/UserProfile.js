// src/components/profile/UserProfile.js (新建文件夹和文件)
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import styles from './ProfileComponents.module.css'; // 我们会创建一个通用的个人中心组件 CSS

const UserProfile = () => {
  const { user, /* updateUser */ } = useAuth(); // 假设 AuthContext 未来有 updateUser 函数
  const [isEditing, setIsEditing] = useState(false);
  const [profileData, setProfileData] = useState({
    username: user.username || 'Test User',
    bio: user.bio || 'Loves to learn and explore new ideas.',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({ ...prev, [name]: value }));
  };

  const handleSave = () => {
    // 调用 context 的 updateUser(profileData);
    console.log("Saving profile data:", profileData);
    alert("Profile saved! (This is a mock-up)");
    setIsEditing(false);
  };

  return (
    <div className={styles.profileSection}>
      <div className={styles.sectionHeader}>
        <h3>Your Profile</h3>
        {!isEditing ? (
          <button onClick={() => setIsEditing(true)} className={styles.actionButton}>Edit</button>
        ) : (
          <div className={styles.editActions}>
            <button onClick={() => setIsEditing(false)} className={`${styles.actionButton} ${styles.cancelButton}`}>Cancel</button>
            <button onClick={handleSave} className={`${styles.actionButton} ${styles.saveButton}`}>Save</button>
          </div>
        )}
      </div>
      <div className={styles.formContent}>
        <div className={styles.formGroup}>
          <label>Username</label>
          {isEditing ? (
            <input type="text" name="username" value={profileData.username} onChange={handleChange} className={styles.inputField} />
          ) : (
            <p className={styles.staticText}>{profileData.username}</p>
          )}
        </div>
        <div className={styles.formGroup}>
          <label>Email</label>
          <p className={styles.staticText}>{user.email} (cannot be changed)</p>
        </div>
        <div className={styles.formGroup}>
          <label>Bio</label>
          {isEditing ? (
            <textarea name="bio" value={profileData.bio} onChange={handleChange} className={styles.textareaField} rows="3" />
          ) : (
            <p className={styles.staticText}>{profileData.bio || 'No bio set.'}</p>
          )}
        </div>
      </div>
    </div>
  );
};
export default UserProfile;