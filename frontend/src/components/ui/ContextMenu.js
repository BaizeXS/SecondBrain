// src/components/ui/ContextMenu.js (新建文件夹和文件)
import React, { useEffect, useRef } from 'react';
import styles from './ContextMenu.module.css';

const ContextMenu = ({ menuItems, position, onClose, targetId }) => {
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        onClose();
      }
    };
    // Bind the event listener
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      // Unbind the event listener on clean up
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [onClose]);

  if (!menuItems || menuItems.length === 0 || !position) {
    return null;
  }

  const handleItemClick = (itemAction) => {
    if (itemAction) {
      itemAction(targetId); // 将目标ID传递给action
    }
    onClose();
  };

  return (
    <div
      ref={menuRef}
      className={styles.contextMenu}
      style={{ top: position.y, left: position.x }}
    >
      <ul>
        {menuItems.map((item, index) => (
          <li key={index} onClick={() => handleItemClick(item.action)} className={styles.menuItem}>
            {item.icon && <span className={styles.menuItemIcon}>{item.icon}</span>}
            {item.label}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ContextMenu;