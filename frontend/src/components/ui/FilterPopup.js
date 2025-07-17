// src/components/ui/FilterPopup.js (新建文件夹和文件)
import React, { useState, useEffect, useRef } from 'react';
import styles from './FilterPopup.module.css';

const FilterPopup = ({ title, filterGroups, activeFilters, onApplyFilters, onClose }) => {
  const [currentSelections, setCurrentSelections] = useState(activeFilters || {});
  const popupRef = useRef(null);

  useEffect(() => {
    setCurrentSelections(activeFilters || {});
  }, [activeFilters]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (popupRef.current && !popupRef.current.contains(event.target)) {
        onClose();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [onClose]);

  const handleCheckboxChange = (groupKey, optionValue) => {
    setCurrentSelections(prev => {
      const groupSelections = prev[groupKey] ? [...prev[groupKey]] : [];
      const currentIndex = groupSelections.indexOf(optionValue);
      if (currentIndex === -1) {
        groupSelections.push(optionValue);
      } else {
        groupSelections.splice(currentIndex, 1);
      }
      return { ...prev, [groupKey]: groupSelections };
    });
  };

  const handleApply = () => {
    onApplyFilters(currentSelections);
    onClose();
  };

  const handleClearGroup = (groupKey) => {
    setCurrentSelections(prev => ({...prev, [groupKey]: []}));
  };

  const handleClearAll = () => {
    const clearedSelections = {};
    Object.keys(filterGroups).forEach(key => {
        clearedSelections[key] = [];
    });
    setCurrentSelections(clearedSelections);
    // Optionally apply immediately or wait for OK
    // onApplyFilters(clearedSelections);
    // onClose();
  };


  if (!filterGroups) return null;

  return (
    <div className={styles.filterPopupOverlay}> {/* Optional: for dimming background */}
        <div ref={popupRef} className={styles.filterPopup}>
        <div className={styles.popupHeader}>
            <h3>{title || 'Filter Options'}</h3>
            <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>
        <div className={styles.popupContent}>
            {Object.entries(filterGroups).map(([groupKey, groupDetails]) => (
            <div key={groupKey} className={styles.filterGroup}>
                <div className={styles.groupHeader}>
                    <h4>{groupDetails.label}</h4>
                    <button onClick={() => handleClearGroup(groupKey)} className={styles.clearGroupButton}>Clear</button>
                </div>
                <ul className={styles.optionsList}>
                {groupDetails.options.map(option => (
                    <li key={option.value} className={styles.optionItem}>
                    <label>
                        <input
                        type="checkbox"
                        value={option.value}
                        checked={currentSelections[groupKey]?.includes(option.value) || false}
                        onChange={() => handleCheckboxChange(groupKey, option.value)}
                        />
                        {option.label}
                    </label>
                    </li>
                ))}
                </ul>
            </div>
            ))}
        </div>
        <div className={styles.popupFooter}>
            <button onClick={handleClearAll} className={`${styles.footerButton} ${styles.clearAllButton}`}>Clear All</button>
            <button onClick={handleApply} className={`${styles.footerButton} ${styles.applyButton}`}>OK</button>
        </div>
        </div>
    </div>
  );
};

export default FilterPopup;