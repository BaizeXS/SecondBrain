// src/components/profile/UsageStats.js (新建文件)
import React from 'react';
import { useProjects } from '../../contexts/ProjectContext';
import { useAgents } from '../../contexts/AgentContext';
import styles from './ProfileComponents.module.css';
import { FiGrid, FiFileText, FiEdit3, FiCpu } from 'react-icons/fi';

const UsageStats = () => {
  const { projects } = useProjects();
  const { agents } = useAgents();

  const totalFiles = projects.reduce((sum, p) => sum + (p.files?.length || 0), 0);
  const totalNotes = projects.reduce((sum, p) => sum + (p.notes?.length || 0), 0);
  const customAgentsCount = agents.filter(a => !a.isSystem).length;

  return (
    <div className={styles.profileSection}>
      <div className={styles.sectionHeader}>
        <h3>Your Second Brain at a Glance</h3>
      </div>
      <div className={styles.statsGrid}>
        <div className={styles.statCard}><FiGrid /> <h4>{projects.length}</h4> <p>Projects Created</p></div>
        <div className={styles.statCard}><FiFileText /> <h4>{totalFiles}</h4> <p>Files Stored</p></div>
        <div className={styles.statCard}><FiEdit3 /> <h4>{totalNotes}</h4> <p>Notes Taken</p></div>
        <div className={styles.statCard}><FiCpu /> <h4>{customAgentsCount}</h4> <p>Custom Agents</p></div>
      </div>
      <div className={styles.heatmapPlaceholder}>
        <h4>Activity Heatmap</h4>
        <p>Your learning and exploration activity over the past year will be visualized here.</p>
        <div className={styles.heatmapGrid}>
          {/* Placeholder for actual heatmap */}
        </div>
      </div>
    </div>
  );
};
export default UsageStats;