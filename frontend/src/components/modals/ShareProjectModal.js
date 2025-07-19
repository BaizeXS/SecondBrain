import React, { useState, useEffect, useRef } from 'react';
import styles from './ShareProjectModal.module.css';
import { FiX, FiUsers, FiGlobe, FiUser, FiEdit, FiEye } from 'react-icons/fi';

const ShareProjectModal = ({ isOpen, onClose, projectData, onUpdateSharing }) => {
  const [shareLevel, setShareLevel] = useState('owner');
  const [permissions, setPermissions] = useState('read');
  const [sharedWith, setSharedWith] = useState([]);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [error, setError] = useState('');
  const modalContentRef = useRef(null);

  useEffect(() => {
    if (isOpen && projectData) {
      setShareLevel(projectData.sharing?.shareLevel || 'owner');
      setPermissions(projectData.sharing?.permissions || 'read');
      setSharedWith(projectData.sharing?.sharedWith || []);
      setError('');
    }
  }, [isOpen, projectData]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (modalContentRef.current && !modalContentRef.current.contains(event.target)) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose]);

  const handleAddUser = () => {
    if (!newUserEmail.trim()) {
      setError('Please enter an email address');
      return;
    }
    if (!newUserEmail.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }
    if (sharedWith.some(user => user.email === newUserEmail.trim())) {
      setError('User is already added');
      return;
    }
    
    setSharedWith(prev => [...prev, { 
      email: newUserEmail.trim(), 
      permissions: permissions,
      addedAt: new Date().toISOString() 
    }]);
    setNewUserEmail('');
    setError('');
  };

  const handleRemoveUser = (emailToRemove) => {
    setSharedWith(prev => prev.filter(user => user.email !== emailToRemove));
  };

  const handleUpdateUserPermission = (email, newPermission) => {
    setSharedWith(prev => prev.map(user => 
      user.email === email ? { ...user, permissions: newPermission } : user
    ));
  };

  const handleSave = () => {
    const isShared = shareLevel !== 'owner' || sharedWith.length > 0;
    
    onUpdateSharing({
      isShared,
      shareLevel,
      sharedWith,
      permissions
    });
    
    onClose();
  };

  const getShareLevelIcon = (level) => {
    switch (level) {
      case 'owner': return <FiUser />;
      case 'organization': return <FiUsers />;
      case 'public': return <FiGlobe />;
      default: return <FiUser />;
    }
  };

  const getShareLevelDescription = (level) => {
    switch (level) {
      case 'owner': return 'Owner of the item(s) has access';
      case 'organization': return 'All members of your organization have access';
      case 'public': return 'People outside your organization have access';
      default: return '';
    }
  };

  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent} ref={modalContentRef}>
        <div className={styles.modalHeader}>
          <h3 className={styles.modalTitle}>Share</h3>
          <button onClick={onClose} className={styles.closeButtonTop} aria-label="Close modal">
            <FiX />
          </button>
        </div>

        <div className={styles.modalBody}>
          {/* Set sharing level section */}
          <div className={styles.section}>
            <h4 className={styles.sectionTitle}>Set sharing level</h4>
            <div className={styles.shareLevelOptions}>
              {['owner', 'organization', 'public'].map((level) => (
                <label key={level} className={`${styles.shareLevelOption} ${shareLevel === level ? styles.selected : ''}`}>
                  <input
                    type="radio"
                    name="shareLevel"
                    value={level}
                    checked={shareLevel === level}
                    onChange={(e) => setShareLevel(e.target.value)}
                    className={styles.radioInput}
                  />
                  <div className={styles.optionContent}>
                    <div className={styles.optionIcon}>
                      {getShareLevelIcon(level)}
                    </div>
                    <div className={styles.optionText}>
                      <div className={styles.optionTitle}>
                        {level === 'owner' ? 'Owner' : level === 'organization' ? 'Organization' : 'Everyone (public)'}
                      </div>
                      <div className={styles.optionDescription}>
                        {getShareLevelDescription(level)}
                      </div>
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Set group sharing section */}
          <div className={styles.section}>
            <h4 className={styles.sectionTitle}>Set group sharing</h4>
            <div className={styles.groupSharingArea}>
              {sharedWith.length > 0 && (
                <div className={styles.sharedUsersList}>
                  {sharedWith.map((user, index) => (
                    <div key={index} className={styles.sharedUserItem}>
                      <div className={styles.userAvatar}>
                        {user.email.charAt(0).toUpperCase()}
                      </div>
                      <div className={styles.userInfo}>
                        <span className={styles.userEmail}>{user.email}</span>
                        <div className={styles.userPermissionControls}>
                          <span className={styles.userPermission}>
                            {user.permissions === 'read' ? <FiEye /> : <FiEdit />}
                            {user.permissions === 'read' ? 'Read only' : 'Can edit'}
                          </span>
                          <select
                            value={user.permissions}
                            onChange={(e) => handleUpdateUserPermission(user.email, e.target.value)}
                            className={styles.permissionSelect}
                          >
                            <option value="read">Read only</option>
                            <option value="edit">Can edit</option>
                          </select>
                        </div>
                      </div>
                      <button 
                        onClick={() => handleRemoveUser(user.email)}
                        className={styles.removeUserButton}
                        title="Remove user"
                      >
                        <FiX />
                      </button>
                    </div>
                  ))}
                </div>
              )}
              
              <div className={styles.addUserSection}>
                <div className={styles.addUserInput}>
                  <input
                    type="email"
                    value={newUserEmail}
                    onChange={(e) => setNewUserEmail(e.target.value)}
                    placeholder="Enter email address"
                    className={styles.emailInput}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddUser()}
                  />
                  <select
                    value={permissions}
                    onChange={(e) => setPermissions(e.target.value)}
                    className={styles.permissionSelect}
                  >
                    <option value="read">Read only</option>
                    <option value="edit">Can edit</option>
                  </select>
                  <button onClick={handleAddUser} className={styles.addUserButton}>
                    Add
                  </button>
                </div>
                {error && <p className={styles.errorMessage}>{error}</p>}
              </div>

              <button className={styles.editGroupButton}>
                <FiUsers />
                Edit group sharing
              </button>
            </div>
          </div>
        </div>

        <div className={styles.modalFooter}>
          <button onClick={onClose} className={`${styles.actionButton} ${styles.cancelButton}`}>
            Cancel
          </button>
          <button onClick={handleSave} className={`${styles.actionButton} ${styles.saveButton}`}>
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default ShareProjectModal; 