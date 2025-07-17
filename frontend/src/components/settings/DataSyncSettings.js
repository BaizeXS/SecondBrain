// src/components/settings/DataSyncSettings.js (新建文件)
import React, { useRef } from 'react';
import styles from './SettingsComponents.module.css'; // 复用通用样式
import { useProjects } from '../../contexts/ProjectContext'; // 用于导出
import { useAgents } from '../../contexts/AgentContext'; // 用于导出
import { FiDownload, FiUpload, FiShare2, FiCloud } from 'react-icons/fi';

const DataSyncSettings = () => {
  const { projects } = useProjects();
  const { agents } = useAgents();
  const importInputRef = useRef(null);

  const handleExportData = () => {
    try {
      const dataToExport = {
        version: "1.0",
        exportDate: new Date().toISOString(),
        projects: projects,
        customAgents: agents.filter(a => !a.isSystem), // 只导出自定义的
        // 未来可以添加其他设置
      };
      const dataStr = JSON.stringify(dataToExport, null, 2); // 格式化 JSON
      const blob = new Blob([dataStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.download = `second_brain_backup_${new Date().toISOString().split('T')[0]}.json`;
      link.href = url;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      alert("Data exported successfully!");
    } catch (error) {
      console.error("Failed to export data:", error);
      alert("An error occurred while exporting your data.");
    }
  };

  const handleTriggerImport = () => {
    importInputRef.current?.click();
  };

  const handleImportData = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importedData = JSON.parse(e.target.result);
        // --- 后端/Context 协作点 ---
        // 这里需要调用一个 context 函数来处理导入的数据，
        // 例如：importData(importedData)
        // 这个函数需要处理合并、覆盖、版本兼容等复杂逻辑。
        console.log("Imported data:", importedData);
        alert(`Successfully read file "${file.name}".\nData import functionality needs to be fully implemented in the context.`);
        // projectContext.importProjects(importedData.projects);
        // agentContext.importAgents(importedData.customAgents);
      } catch (error) {
        console.error("Failed to parse or import data:", error);
        alert("The selected file is not a valid Second Brain backup file.");
      }
    };
    reader.readAsText(file);
    if (importInputRef.current) importInputRef.current.value = ""; // 清空以便再次选择
  };

  return (
    <div className={styles.settingsSection}>
      <div className={styles.sectionHeader}><h3><FiCloud /> Data & Sync</h3></div>
      <div className={styles.sectionContent}>

        {/* 导出数据 */}
        <div className={styles.subSection}>
          <h4>Export Data</h4>
          <p className={styles.sectionDescription}>
            Download a backup of all your projects, agents, and settings as a single JSON file. Keep it safe!
          </p>
          <button onClick={handleExportData} className={`${styles.actionButton} ${styles.primaryButton}`}>
            <FiDownload /> Export All Data
          </button>
        </div>

        {/* 导入数据 */}
        <div className={styles.subSection}>
          <h4>Import Data</h4>
          <p className={styles.sectionDescription}>
            Import data from a previously exported `second_brain_backup.json` file. This may overwrite existing data.
          </p>
          <input
            type="file"
            accept="application/json"
            ref={importInputRef}
            onChange={handleImportData}
            style={{ display: 'none' }}
          />
          <button onClick={handleTriggerImport} className={styles.actionButton}>
            <FiUpload /> Import from File...
          </button>
        </div>

        {/* 云同步 (未来功能占位符) */}
        <div className={styles.subSection}>
          <h4>Cloud Sync (Coming Soon)</h4>
          <p className={styles.sectionDescription}>
            Automatically sync your Second Brain across all your devices.
          </p>
          <button className={styles.actionButton} disabled>
            <FiShare2 /> Connect to Cloud
          </button>
        </div>

      </div>
    </div>
  );
};

export default DataSyncSettings;