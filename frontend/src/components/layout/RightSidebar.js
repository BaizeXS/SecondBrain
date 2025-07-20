// src/components/layout/RightSidebar.js
import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Link, useParams } from 'react-router-dom';
import styles from './RightSidebar.module.css';
import { useSidebar } from '../../contexts/SidebarContext';
// <<< 导入 useProjects, useAgents, getIconComponent >>>
import { useProjects } from '../../contexts/ProjectContext';
import { useAgents } from '../../contexts/AgentContext'; // 确保路径正确
import { useChat } from '../../contexts/ChatContext'; // 新增：导入ChatContext
import apiService from '../../services/apiService'; // 添加apiService导入
import {
  FiFileText, FiEdit3, FiSearch, FiFilter, FiPlus, FiMessageSquare,
  FiChevronsRight, FiChevronsLeft, FiDownload, FiTrash2, FiX,
  // 确保 ChatInputInterface 和 MessageFileAttachments 需要的图标也在这里
  FiPaperclip, FiSend, FiUpload, FiCheck
} from 'react-icons/fi';
import ContextMenu from '../ui/ContextMenu';
import FilterPopup from '../ui/FilterPopup';
import ChatInputInterface from '../chat/ChatInputInterface'; // <<< 导入 ChatInputInterface
import MessageFileAttachments from '../chat/MessageFileAttachments'; // <<< 导入 MessageFileAttachments

// --- 辅助函数：格式化文件大小 ---
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const numBytes = Number(bytes);
  if (isNaN(numBytes) || numBytes === 0) return '0 Bytes';
  const i = Math.floor(Math.log(numBytes) / Math.log(k));
  return parseFloat((numBytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

// --- 筛选器配置 ---
const fileFilterGroups = {
  fileType: {
    label: 'File Type',
    options: [
      { label: 'PDF', value: 'application/pdf' },
      { label: 'DOCX', value: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' },
      { label: 'Word (DOC)', value: 'application/msword' },
      { label: 'XLSX', value: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' },
      { label: 'Excel (XLS)', value: 'application/vnd.ms-excel' },
      { label: 'JPEG', value: 'image/jpeg' },
      { label: 'PNG', value: 'image/png' },
      { label: 'MP4', value: 'video/mp4' },
    ],
  },
  uploadDate: {
    label: 'Upload Date',
    options: [
      { label: 'Last 3 days', value: '3days' }, { label: 'Last week', value: '7days' },
      { label: 'Last month', value: '30days' }, { label: 'Last 3 months', value: '90days' },
      { label: 'Older than 3 months', value: 'older' },
    ],
  },
};
const noteFilterGroups = {
  creationDate: {
    label: 'Creation Date',
    options: [
      { label: 'Last 3 days', value: '3days' }, { label: 'Last week', value: '7days' },
      { label: 'Last month', value: '30days' }, { label: 'Last 3 months', value: '90days' },
      { label: 'Older than 3 months', value: 'older' },
    ],
  },
};

// --- 日期筛选辅助函数 ---
const isWithinDateRange = (isoDateString, rangeValue) => {
  if (!isoDateString) return false;
  const date = new Date(isoDateString);
  if (isNaN(date.getTime())) return false;
  const now = new Date();
  let rangeStartDate = new Date(now);
  switch (rangeValue) {
    case '3days': rangeStartDate.setDate(now.getDate() - 3); break;
    case '7days': rangeStartDate.setDate(now.getDate() - 7); break;
    case '30days': rangeStartDate.setMonth(now.getMonth() - 1); break;
    case '90days': rangeStartDate.setMonth(now.getMonth() - 3); break;
    case 'older':
      const threeMonthsAgo = new Date(new Date().setMonth(now.getMonth() - 3)); // Ensure 'now' is not mutated for this check
      return date < threeMonthsAgo;
    default: return true;
  }
  return date >= rangeStartDate;
};

const sidebarMockModels = [
  { id: 'deepseek-sidebar', name: 'DeepSeek' },
  { id: 'gpt4-sidebar', name: 'GPT-4' },
];

// --- 简化数据的辅助函数，用于回调 ---
const simplifyFileForCallback = f => ({ 
  id: f.id, 
  name: f.name, 
  size: f.size, 
  type: f.type, 
  preview: f.preview, 
  uploadedAt: f.uploadedAt,
  isAiGenerated: f.isAiGenerated,
  aiAgent: f.aiAgent
});
const simplifyNoteForCallback = n => ({ 
  id: n.id, 
  name: n.name, 
  preview: n.preview, 
  content: n.content, 
  createdAt: n.createdAt,
  isAiGenerated: n.isAiGenerated,
  aiAgent: n.aiAgent
});

// --- FilesListView 组件 ---
const FilesListView = ({ files: initialFiles }) => {
  const fileInputRef = useRef(null);
  const searchInputRef = useRef(null);
  const { rightSidebarView } = useSidebar();
  const { addFilesToChat } = useChat(); // 新增：使用ChatContext
  
  // 根据视图类型选择回调
  const onUpdateFilesCallback =
    rightSidebarView?.type === 'PROJECT_DETAILS' || rightSidebarView?.type === 'FILE_DETAILS'
      ? rightSidebarView.data?.onUpdateProjectFiles
      : rightSidebarView.data?.onUpdateChatFiles;

  const [displayedItems, setDisplayedItems] = useState(initialFiles || []);
  const [contextMenuVisible, setContextMenuVisible] = useState(false);
  const [contextMenuPosition, setContextMenuPosition] = useState({ x: 0, y: 0 });
  const [contextMenuTargetId, setContextMenuTargetId] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilterPopup, setShowFilterPopup] = useState(false);
  const [activeFilters, setActiveFilters] = useState({});
  
  // 新增：选择模式相关状态
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [selectedItems, setSelectedItems] = useState(new Set());

  useEffect(() => {
    let processedFiles = initialFiles || [];
    console.log("FilesListView: initialFiles prop updated. Count:", processedFiles.length); // <<< 添加日志
    const hasActiveFilterSelections = Object.values(activeFilters).some(arr => arr && arr.length > 0);
    if (hasActiveFilterSelections) {
      processedFiles = processedFiles.filter(file => {
        let typeMatch = true;
        if (activeFilters.fileType && activeFilters.fileType.length > 0) {
          typeMatch = file.type && activeFilters.fileType.includes(file.type);
        }
        let dateMatch = true;
        if (activeFilters.uploadDate && activeFilters.uploadDate.length > 0) {
          dateMatch = activeFilters.uploadDate.some(range => isWithinDateRange(file.uploadedAt, range));
        }
        return typeMatch && dateMatch;
      });
    }
    if (searchQuery.trim() !== '') {
      const lowerCaseQuery = searchQuery.toLowerCase();
      processedFiles = processedFiles.filter(file => file.name.toLowerCase().includes(lowerCaseQuery));
    }
    setDisplayedItems(processedFiles);
  }, [initialFiles, searchQuery, activeFilters]);

  useEffect(() => { if (isSearching && searchInputRef.current) searchInputRef.current.focus(); }, [isSearching]);

  const handleAddFileClick = () => fileInputRef.current?.click();
  const handleFileSelected = (event) => {
    const selectedRawFiles = event.target.files;
    if (selectedRawFiles && selectedRawFiles.length > 0) {
      const currentFiles = initialFiles || [];
      const newUniqueFiles = [];
      const duplicateFileNames = [];

      for (const file of Array.from(selectedRawFiles)) {
        // 检查是否已存在于当前上下文/项目中
        const isDuplicate = currentFiles.some(
          existingFile => existingFile.name === file.name && existingFile.size === file.size
        );

        if (isDuplicate) {
          duplicateFileNames.push(file.name);
        } else {
          // 检查本次选择的文件批次中自身是否有重复
          if (!newUniqueFiles.some(newFile => newFile.name === file.name && newFile.size === file.size)) {
            newUniqueFiles.push(file);
          }
        }
      }

      // <<< 关键：在这里进行弹窗提示 >>>
      if (duplicateFileNames.length > 0) {
        alert(`The following file(s) already exist and were not added:\n- ${duplicateFileNames.join('\n- ')}`);
      }

      // 只处理不重复的新文件
      if (newUniqueFiles.length > 0) {
        const newFileObjects = newUniqueFiles.map(f => ({
          id: `local-${f.name}-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
          name: f.name, size: f.size, type: f.type, rawFile: f,
          preview: `Type: ${f.type || 'unknown'}, Size: ${formatFileSize(f.size)}`,
          uploadedAt: new Date().toISOString(),
        }));
        const updatedFullFileList = [...(initialFiles || []), ...newFileObjects];
        if (typeof onUpdateFilesCallback === 'function') { // onUpdateFilesCallback 是根据视图类型选择的
          onUpdateFilesCallback(updatedFullFileList.map(simplifyFileForCallback));
        } else {
          console.warn(`FilesListView: onUpdateFilesCallback not available for view type "${rightSidebarView?.type}".`);
        }
      }
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // 新增：选择模式相关函数
  const handleToggleSelectionMode = () => {
    setIsSelectionMode(!isSelectionMode);
    if (isSelectionMode) {
      setSelectedItems(new Set()); // 退出选择模式时清空选择
    }
  };

  const handleItemSelect = (itemId) => {
    const newSelectedItems = new Set(selectedItems);
    if (newSelectedItems.has(itemId)) {
      newSelectedItems.delete(itemId);
    } else {
      newSelectedItems.add(itemId);
    }
    setSelectedItems(newSelectedItems);
  };

  const handleConfirmSelection = () => {
    const selectedFiles = displayedItems.filter(item => selectedItems.has(item.id));
    // 使用ChatContext添加文件到聊天框
    addFilesToChat(selectedFiles);
    console.log('Selected files added to chat:', selectedFiles);
    
    // 退出选择模式
    setIsSelectionMode(false);
    setSelectedItems(new Set());
  };

  const handleFileContextMenu = (event, fileId) => { event.preventDefault(); setContextMenuPosition({ x: event.clientX, y: event.clientY }); setContextMenuTargetId(fileId); setContextMenuVisible(true); };
  const closeContextMenu = () => { setContextMenuVisible(false); setContextMenuTargetId(null); };
  const handleDownloadFile = (fileId) => {
    const fileToDownload = (initialFiles || []).find(f => f.id === fileId);
    if (fileToDownload && fileToDownload.rawFile instanceof File) {
      const url = URL.createObjectURL(fileToDownload.rawFile);
      const a = document.createElement('a'); a.href = url; a.download = fileToDownload.name;
      document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);
    } else if (fileToDownload) { alert(`Download for "${fileToDownload.name}" needs server URL.`); }
    closeContextMenu();
  };
  const handleDeleteFile = (fileId) => {
    const updatedFullFileList = (initialFiles || []).filter(f => f.id !== fileId);
    if (typeof onUpdateFilesCallback === 'function') {
      onUpdateFilesCallback(updatedFullFileList.map(simplifyFileForCallback));
    } else { console.warn(`FilesListView: onUpdateFilesCallback not available for view type "${rightSidebarView?.type}". Unable to delete file from source.`); }
    closeContextMenu();
  };
  const contextMenuItems = [{ label: 'Download', icon: <FiDownload />, action: handleDownloadFile }, { label: 'Delete', icon: <FiTrash2 />, action: handleDeleteFile }];
  const handleSearchIconClick = () => setIsSearching(true);
  const handleCloseSearch = () => { setIsSearching(false); setSearchQuery(''); };
  const handleSearchInputChange = (e) => setSearchQuery(e.target.value);
  const handleSearchKeyDown = (e) => { if (e.key === 'Escape') handleCloseSearch(); };
  const handleFilterIconClick = () => setShowFilterPopup(true);
  const handleCloseFilterPopup = () => setShowFilterPopup(false);
  const handleApplyFilters = (newFilters) => setActiveFilters(newFilters);

  return (
    <div className={styles.viewContentWrapper}>
      <div className={styles.actionBar}>
        {isSearching ? (
          <div className={styles.searchBarContainer}>
            <FiSearch className={styles.searchBarIconInternal} />
            <input ref={searchInputRef} type="text" placeholder="Search files..." value={searchQuery} onChange={handleSearchInputChange} onKeyDown={handleSearchKeyDown} className={styles.searchInput} />
            <button onClick={handleCloseSearch} className={styles.clearSearchButton} title="Close search"><FiX /></button>
          </div>
        ) : (
          <>
            <div className={styles.actionBarLeft}>
              <button onClick={handleSearchIconClick} className={styles.actionButtonIcon} title="Search files"><FiSearch /></button>
              <button onClick={handleFilterIconClick} className={`${styles.actionButtonIcon} ${Object.values(activeFilters).some(arr => arr?.length > 0) ? styles.filterActive : ''}`} title="Filter files"> <FiFilter /> </button>
              <button 
                onClick={handleToggleSelectionMode} 
                className={`${styles.actionButtonIcon} ${isSelectionMode ? styles.selectionModeActive : ''}`} 
                title={isSelectionMode ? "Exit selection mode" : "Select files to add to chat"}
              >
                <FiUpload />
              </button>
            </div>
            <input type="file" ref={fileInputRef} style={{ display: 'none' }} onChange={handleFileSelected} multiple />
            <button onClick={handleAddFileClick} className={styles.actionButtonIcon} title="Add files"><FiPlus /></button>
          </>
        )}
      </div>
      {displayedItems.length > 0 ? (
        <ul className={styles.itemList}>
          {displayedItems.map(file => {
            // 获取当前项目的 ID
            const currentProjectId = rightSidebarView?.data?.projectId;
            const isSelected = selectedItems.has(file.id);
            
            return (
              <li key={file.id} className={`${styles.itemCard} ${isSelectionMode ? styles.selectionMode : ''} ${isSelected ? styles.selectedItem : ''}`} onContextMenu={(e) => handleFileContextMenu(e, file.id)}>
                {isSelectionMode && (
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => handleItemSelect(file.id)}
                    className={styles.itemCheckbox}
                  />
                )}
                <FiFileText className={styles.itemTypeIcon} />
                <div className={styles.itemInfo}>
                  {/* <<< 用 Link 包裹文件名 >>> */}
                  {currentProjectId ? (
                    <Link to={`/neurocore/project/${currentProjectId}/file/${file.id}`} className={styles.itemNameLink}>
                      <span className={styles.itemName}>
                        {file.name}
                      </span>
                    </Link>
                  ) : (
                    <span className={styles.itemName}>
                      {file.name}
                    </span>
                  )}
                  <p className={styles.itemPreview}>{file.preview}</p>
                  {/* 新增：AI生成标签 */}
                  {file.isAiGenerated && (
                    <div className={styles.aiGeneratedTag}>
                      <span className={styles.aiTagText}>AI</span>
                      {file.aiAgent && <span className={styles.aiAgentText}>by {file.aiAgent}</span>}
                    </div>
                  )}
                  {/* 新增：创建者信息 */}
                  <div className={styles.creatorInfo}>
                    <span className={styles.creatorLabel}>Creator:</span>
                    <span className={`${styles.creatorValue} ${file.isAiGenerated ? styles.creatorAi : styles.creatorUser}`}>
                      {file.isAiGenerated ? 'AI' : 'User'}
                    </span>
                  </div>
                </div>
                {!isSelectionMode && (
                  <button onClick={(e) => { e.stopPropagation(); handleDeleteFile(file.id); }} className={styles.deleteItemButton} title="Delete file"><FiTrash2 /></button>
                )}
              </li>
            );
          })}
        </ul>
      ) : (<p className={styles.emptyStateText}>{searchQuery || Object.values(activeFilters).some(arr => arr?.length > 0) ? `No files match your criteria.` : 'No files yet. Click "+" to add some.'}</p>)}
      
      {/* 新增：选择模式下的确认按钮 */}
      {isSelectionMode && selectedItems.size > 0 && (
        <div className={styles.selectionConfirmBar}>
          <span className={styles.selectionCount}>{selectedItems.size} file(s) selected</span>
          <button onClick={handleConfirmSelection} className={styles.confirmSelectionButton}>
            <FiCheck />
            Add to Chat
          </button>
        </div>
      )}
      
      {showFilterPopup && <FilterPopup title="Filter Files" filterGroups={fileFilterGroups} activeFilters={activeFilters} onApplyFilters={handleApplyFilters} onClose={handleCloseFilterPopup} />}
      {contextMenuVisible && <ContextMenu items={contextMenuItems} position={contextMenuPosition} onClose={closeContextMenu} onItemClick={(action) => action(contextMenuTargetId)} />}
    </div>
  );
};

// --- NotesListView 组件 ---
const NotesListView = ({ notes: initialNotes }) => {
  const searchInputRef = useRef(null);
  const { rightSidebarView } = useSidebar();
  const { addNotesToChat } = useChat(); // 新增：使用ChatContext
  
  // 根据视图类型选择回调
  const onUpdateNotesCallback =
    rightSidebarView?.type === 'PROJECT_DETAILS' || rightSidebarView?.type === 'FILE_DETAILS'
      ? rightSidebarView.data?.onUpdateProjectNotes
      : rightSidebarView.data?.onUpdateChatNotes;

  const [displayedItems, setDisplayedItems] = useState(initialNotes || []);
  const [isEditing, setIsEditing] = useState(false);
  const [currentNoteTitle, setCurrentNoteTitle] = useState('');
  const [currentNoteContent, setCurrentNoteContent] = useState('');
  const [editingNoteId, setEditingNoteId] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilterPopup, setShowFilterPopup] = useState(false);
  const [activeFilters, setActiveFilters] = useState({});
  
  // 新增：选择模式相关状态
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [selectedItems, setSelectedItems] = useState(new Set());

  useEffect(() => {
    let processedNotes = initialNotes || [];
    const hasActiveFilterSelections = Object.values(activeFilters).some(arr => arr && arr.length > 0);
    if (hasActiveFilterSelections) {
      processedNotes = processedNotes.filter(note => {
        let dateMatch = true;
        if (activeFilters.creationDate && activeFilters.creationDate.length > 0) {
          dateMatch = activeFilters.creationDate.some(range => isWithinDateRange(note.createdAt, range));
        }
        return dateMatch;
      });
    }
    if (searchQuery.trim() !== '') {
      const lowerCaseQuery = searchQuery.toLowerCase();
      processedNotes = processedNotes.filter(note =>
        (note.name && note.name.toLowerCase().includes(lowerCaseQuery)) ||
        (note.preview && note.preview.toLowerCase().includes(lowerCaseQuery)) ||
        (note.content && note.content.toLowerCase().includes(lowerCaseQuery))
      );
    }
    setDisplayedItems(processedNotes);
  }, [initialNotes, searchQuery, activeFilters]);

  useEffect(() => { if (isSearching && searchInputRef.current) searchInputRef.current.focus(); }, [isSearching]);

  // 新增：选择模式相关函数
  const handleToggleSelectionMode = () => {
    setIsSelectionMode(!isSelectionMode);
    if (isSelectionMode) {
      setSelectedItems(new Set()); // 退出选择模式时清空选择
    }
  };

  const handleItemSelect = (itemId) => {
    const newSelectedItems = new Set(selectedItems);
    if (newSelectedItems.has(itemId)) {
      newSelectedItems.delete(itemId);
    } else {
      newSelectedItems.add(itemId);
    }
    setSelectedItems(newSelectedItems);
  };

  const handleConfirmSelection = () => {
    const selectedNotes = displayedItems.filter(item => selectedItems.has(item.id));
    // 使用ChatContext添加笔记到聊天框
    addNotesToChat(selectedNotes);
    console.log('Selected notes added to chat:', selectedNotes);
    
    // 退出选择模式
    setIsSelectionMode(false);
    setSelectedItems(new Set());
  };

  const handleAddNoteClick = () => { setIsEditing(true); setCurrentNoteTitle(''); setCurrentNoteContent(''); setEditingNoteId(null); };
  const handleCancelEdit = () => { setIsEditing(false); setCurrentNoteTitle(''); setCurrentNoteContent(''); setEditingNoteId(null); };
  const handleEditNoteClick = (note) => { setIsEditing(true); setCurrentNoteTitle(note.name); setCurrentNoteContent(note.content || ''); setEditingNoteId(note.id); };

  const handleSaveNote = async () => {
    if (!currentNoteTitle.trim() && !currentNoteContent.trim()) { alert("Note is empty."); return; }
    
    try {
      // 获取当前的 space_id（如果在项目视图中）
      const spaceId = rightSidebarView?.data?.projectId || rightSidebarView?.data?.space_id;
      
      let savedNote;
      const currentNotes = initialNotes || [];
      
      if (editingNoteId) {
        // 编辑现有笔记
        const noteId = editingNoteId.toString().replace('note-', '');
        
        // 如果有 space_id，则保存到后端
        if (spaceId && !editingNoteId.startsWith('note-temp-')) {
          savedNote = await apiService.note.updateNote(noteId, {
            title: currentNoteTitle.trim() || "Untitled",
            content: currentNoteContent,
            space_id: parseInt(spaceId)
          });
        }
        
        // 更新本地列表
        const updatedNote = savedNote ? {
          id: savedNote.id.toString(),
          name: savedNote.title,
          preview: savedNote.content?.substring(0, 50) + "...",
          content: savedNote.content,
          createdAt: savedNote.created_at,
          updatedAt: savedNote.updated_at
        } : {
          id: editingNoteId,
          name: currentNoteTitle.trim() || "Untitled",
          preview: currentNoteContent.substring(0, 50) + "...",
          content: currentNoteContent,
          createdAt: new Date().toISOString()
        };
        
        const updatedFullNoteList = currentNotes.map(n =>
          n.id === editingNoteId ? updatedNote : n
        );
        
        if (typeof onUpdateNotesCallback === 'function') {
          onUpdateNotesCallback(updatedFullNoteList.map(simplifyNoteForCallback));
        }
      } else {
        // 创建新笔记
        if (spaceId) {
          // 保存到后端
          savedNote = await apiService.note.createNote({
            title: currentNoteTitle.trim() || "Untitled Note",
            content: currentNoteContent,
            space_id: parseInt(spaceId)
          });
          
          const newNote = {
            id: savedNote.id.toString(),
            name: savedNote.title,
            preview: savedNote.content?.substring(0, 50) + "...",
            content: savedNote.content,
            createdAt: savedNote.created_at,
            updatedAt: savedNote.updated_at
          };
          
          const updatedFullNoteList = [...currentNotes, newNote];
          
          if (typeof onUpdateNotesCallback === 'function') {
            onUpdateNotesCallback(updatedFullNoteList.map(simplifyNoteForCallback));
          }
        } else {
          // 如果没有 space_id，只保存到本地
          const newNote = {
            id: `note-temp-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
            name: currentNoteTitle.trim() || "Untitled Note",
            preview: currentNoteContent.substring(0, 50) + "...",
            content: currentNoteContent,
            createdAt: new Date().toISOString(),
          };
          
          const updatedFullNoteList = [...currentNotes, newNote];
          
          if (typeof onUpdateNotesCallback === 'function') {
            onUpdateNotesCallback(updatedFullNoteList.map(simplifyNoteForCallback));
          }
        }
      }
      
      handleCancelEdit();
    } catch (error) {
      console.error("Error saving note:", error);
      alert("Failed to save note: " + error.message);
    }
  };

  const handleDeleteNote = async (noteIdToDelete) => {
    try {
      // 获取当前的 space_id（如果在项目视图中）
      const spaceId = rightSidebarView?.data?.projectId || rightSidebarView?.data?.space_id;
      
      // 如果有 space_id 且不是临时笔记，则从后端删除
      if (spaceId && !noteIdToDelete.startsWith('note-temp-')) {
        const noteId = noteIdToDelete.toString().replace('note-', '');
        await apiService.note.deleteNote(noteId);
      }
      
      // 更新本地列表
      const updatedFullNoteList = (initialNotes || []).filter(note => note.id !== noteIdToDelete);
      if (typeof onUpdateNotesCallback === 'function') {
        onUpdateNotesCallback(updatedFullNoteList.map(simplifyNoteForCallback));
      } else {
        console.warn(`NotesListView: onUpdateNotesCallback not available for view type "${rightSidebarView?.type}". Unable to delete note from source.`);
      }
      
      if (isEditing && editingNoteId === noteIdToDelete) handleCancelEdit();
    } catch (error) {
      console.error("Error deleting note:", error);
      alert("Failed to delete note: " + error.message);
    }
  };

  const handleSearchIconClick = () => setIsSearching(true);
  const handleCloseSearch = () => { setIsSearching(false); setSearchQuery(''); };
  const handleSearchInputChange = (e) => setSearchQuery(e.target.value);
  const handleSearchKeyDown = (e) => { if (e.key === 'Escape') handleCloseSearch(); };
  const handleFilterIconClick = () => { setShowFilterPopup(true); };
  const handleCloseFilterPopup = () => setShowFilterPopup(false);
  const handleApplyFilters = (newFilters) => setActiveFilters(newFilters);

  if (isEditing) {
    return (
      <div className={styles.noteEditorWrapper}>
        <input type="text" placeholder="Note Title" value={currentNoteTitle} onChange={(e) => setCurrentNoteTitle(e.target.value)} className={styles.noteTitleInput} />
        <textarea placeholder="Type your note here..." value={currentNoteContent} onChange={(e) => setCurrentNoteContent(e.target.value)} className={styles.noteContentTextarea} rows={10} />
        <div className={styles.editorActions}>
          <button onClick={handleSaveNote} className={`${styles.actionButtonSolid} ${styles.saveButton}`}>Save Note</button>
          <button onClick={handleCancelEdit} className={`${styles.actionButtonOutline} ${styles.cancelButton}`}>Cancel</button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.viewContentWrapper}>
      <div className={styles.actionBar}>
        {isSearching ? (
          <div className={styles.searchBarContainer}>
            <FiSearch className={styles.searchBarIconInternal} />
            <input ref={searchInputRef} type="text" placeholder="Search notes..." value={searchQuery} onChange={handleSearchInputChange} onKeyDown={handleSearchKeyDown} className={styles.searchInput} />
            <button onClick={handleCloseSearch} className={styles.clearSearchButton} title="Close search"><FiX /></button>
          </div>
        ) : (
          <>
            <div className={styles.actionBarLeft}>
              <button onClick={handleSearchIconClick} className={styles.actionButtonIcon} title="Search notes"><FiSearch /></button>
              <button onClick={handleFilterIconClick} className={`${styles.actionButtonIcon} ${Object.values(activeFilters).some(arr => arr?.length > 0) ? styles.filterActive : ''}`} title="Filter notes"> <FiFilter /> </button>
              <button 
                onClick={handleToggleSelectionMode} 
                className={`${styles.actionButtonIcon} ${isSelectionMode ? styles.selectionModeActive : ''}`} 
                title={isSelectionMode ? "Exit selection mode" : "Select notes to add to chat"}
              >
                <FiUpload />
              </button>
            </div>
            <button onClick={handleAddNoteClick} className={styles.actionButtonIcon} title="Add new note"><FiPlus /></button>
          </>
        )}
      </div>
      {displayedItems.length > 0 ? (
        <ul className={styles.itemList}>
          {displayedItems.map(note => {
            const isSelected = selectedItems.has(note.id);
            
            return (
              <li key={note.id} className={`${styles.itemCard} ${isSelectionMode ? styles.selectionMode : ''} ${isSelected ? styles.selectedItem : ''}`} title="Click to edit note">
                {isSelectionMode && (
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => handleItemSelect(note.id)}
                    className={styles.itemCheckbox}
                  />
                )}
                <FiEdit3 className={styles.itemTypeIcon} />
                <div className={styles.itemInfo} onClick={() => !isSelectionMode && handleEditNoteClick(note)} style={{ cursor: isSelectionMode ? 'default' : 'pointer', flexGrow: 1 }}>
                  <span className={styles.itemName}>
                    {note.name}
                  </span>
                  <p className={styles.itemPreview}>{note.preview}</p>
                  {/* 新增：AI生成标签 */}
                  {note.isAiGenerated && (
                    <div className={styles.aiGeneratedTag}>
                      <span className={styles.aiTagText}>AI</span>
                      {note.aiAgent && <span className={styles.aiAgentText}>by {note.aiAgent}</span>}
                    </div>
                  )}
                  {/* 新增：创建者信息 */}
                  <div className={styles.creatorInfo}>
                    <span className={styles.creatorLabel}>Creator:</span>
                    <span className={`${styles.creatorValue} ${note.isAiGenerated ? styles.creatorAi : styles.creatorUser}`}>
                      {note.isAiGenerated ? 'AI' : 'User'}
                    </span>
                  </div>
                </div>
                {!isSelectionMode && (
                  <button onClick={(e) => { e.stopPropagation(); handleDeleteNote(note.id); }} className={styles.deleteItemButton} title="Delete note"><FiTrash2 /></button>
                )}
              </li>
            );
          })}
        </ul>
      ) : (<p className={styles.emptyStateText}>{searchQuery || Object.values(activeFilters).some(arr => arr?.length > 0) ? `No notes match your criteria.` : 'No notes yet. Click "+" to create one.'}</p>)}
      
      {/* 新增：选择模式下的确认按钮 */}
      {isSelectionMode && selectedItems.size > 0 && (
        <div className={styles.selectionConfirmBar}>
          <span className={styles.selectionCount}>{selectedItems.size} note(s) selected</span>
          <button onClick={handleConfirmSelection} className={styles.confirmSelectionButton}>
            <FiCheck />
            Add to Chat
          </button>
        </div>
      )}
      
      {showFilterPopup && <FilterPopup title="Filter Notes" filterGroups={noteFilterGroups} activeFilters={activeFilters} onApplyFilters={handleApplyFilters} onClose={handleCloseFilterPopup} />}
    </div>
  );
};

// --- FileSpecificChatView 组件 (核心修改区域) ---
const FileSpecificChatView = ({ data }) => {
  const { updateProject, getProjectById } = useProjects();
  const { agents, loadingAgents } = useAgents();

  const [messages, setMessages] = useState([]);
  const [activeAgentId, setActiveAgentId] = useState(null);
  const chatMessagesAreaRef = useRef(null);
  const [selectedModelId, setSelectedModelId] = useState(sidebarMockModels[0].id);

  useEffect(() => {
    const project = getProjectById(data.projectId);
    if (project) {
      const fileChatHistory = project.fileChats?.[data.currentFileId]?.messages || [];
      setMessages(fileChatHistory);
    }
  }, [data.currentFileId, data.projectId, getProjectById]);

  useEffect(() => {
    if (!loadingAgents && agents.length > 0 && !activeAgentId) {
      const defaultAgent = agents.find(a => a.name === 'General') || agents[0];
      if (defaultAgent) setActiveAgentId(defaultAgent.id);
    }
  }, [agents, loadingAgents, activeAgentId]);

  useEffect(() => {
    if (chatMessagesAreaRef.current) {
      chatMessagesAreaRef.current.scrollTop = chatMessagesAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = (messageText, filesFromInput, notesFromInput = []) => {
    if (!data.projectId || !updateProject || !getProjectById) return;

    const activeAgent = agents.find(a => a.id === activeAgentId);
    const agentName = activeAgent ? activeAgent.name : 'default';
    const currentModel = sidebarMockModels.find(m => m.id === selectedModelId);
    const modelName = currentModel ? currentModel.name : 'default model';

    const newUserMessage = {
      id: `filechat-user-${Date.now()}`, sender: 'user', text: messageText,
      timestamp: new Date().toISOString(),
      files: filesFromInput.map(f => ({ id: f.id, name: f.name, size: f.size, type: f.type, preview: f.preview, uploadedAt: f.uploadedAt })),
      notes: notesFromInput.map(n => ({ id: n.id, name: n.name, content: n.content, createdAt: n.createdAt, preview: n.preview })) // 新增：添加笔记
    };

    const aiResponse = {
      id: `filechat-ai-${Date.now()}`, sender: 'ai',
      text: `AI response about "${data.currentFileName}" (using ${agentName} agent)...`,
      timestamp: new Date().toISOString(), files: []
    };

    const newMessages = [...messages, newUserMessage, aiResponse];
    setMessages(newMessages);

    const project = getProjectById(data.projectId);
    if (!project) return;

    const updatedFileChats = { ...(project.fileChats || {}) };
    updatedFileChats[data.currentFileId] = {
      ...(updatedFileChats[data.currentFileId] || { startTime: new Date().toISOString() }),
      messages: newMessages,
      lastUpdatedAt: new Date().toISOString(),
    };

    let updatedProjectFiles = [...(project.files || [])];
    if (filesFromInput.length > 0) {
      // ChatInputInterface 内部的去重只针对预览区，这里我们进行全局去重
      const newFilesToAddToProject = filesFromInput.filter(
        newFile => !updatedProjectFiles.some(
          existing => existing.name === newFile.name && existing.size === newFile.size
        )
      );
      if (newFilesToAddToProject.length > 0) {
        const newSimplifiedFiles = newFilesToAddToProject.map(simplifyFileForCallback);
        updatedProjectFiles = [...updatedProjectFiles, ...newSimplifiedFiles];
      }
    }

    // 新增：处理笔记
    let updatedProjectNotes = [...(project.notes || [])];
    if (notesFromInput.length > 0) {
      const newNotesToAddToProject = notesFromInput.filter(
        newNote => !updatedProjectNotes.some(
          existing => existing.id === newNote.id
        )
      );
      if (newNotesToAddToProject.length > 0) {
        const newSimplifiedNotes = newNotesToAddToProject.map(simplifyNoteForCallback);
        updatedProjectNotes = [...updatedProjectNotes, ...newSimplifiedNotes];
      }
    }

    updateProject(data.projectId, { fileChats: updatedFileChats, files: updatedProjectFiles, notes: updatedProjectNotes });
  };

  const handleModelChange = (e) => {
    setSelectedModelId(e.target.value);
  };

  return (
    <div className={styles.viewContentWrapper}>
      <div className={styles.chatInterfaceHeader}>
        <p className={styles.chatViewTitle}>Chat about: <strong>{data.currentFileName}</strong></p>
      </div>
      <div className={styles.chatMessagesAreaSidebar} ref={chatMessagesAreaRef}>
        {messages.length > 0 ? (
          messages.map(msg => (
            // --- 核心修改在这里 ---
            // 1. 外层 div 使用 .sidebarChatMessage 和动态的 .user 或 .ai
            <div key={msg.id || msg.timestamp} className={`${styles.sidebarChatMessage} ${styles[msg.sender]}`}>
              {/* 2. 内层 div 作为气泡体，应用 .messageBubbleContent */}
              <div className={styles.messageBubbleContent}>
                <p>{msg.text}</p>
                {/* 消息内的文件附件（如果需要） */}
                {((msg.files && msg.files.length > 0) || (msg.notes && msg.notes.length > 0)) && (
                  <MessageFileAttachments files={msg.files || []} notes={msg.notes || []} isAiMessage={msg.sender === 'ai'} />
                )}
              </div>
            </div>
          ))
        ) : (
          <p className={styles.emptyStateText}>Ask anything about this file...</p>
        )}
      </div>
      <div className={styles.chatInputContainerSidebar}>
        {/* --- 核心修改：将 Agent 和 Model 选择器放在一起 --- */}
        <div className={styles.sidebarSelectorsWrapper}>
          <select
            value={activeAgentId || ''}
            onChange={(e) => setActiveAgentId(e.target.value)}
            className={styles.sidebarAgentSelector}
            disabled={loadingAgents}
          >
            {loadingAgents ? <option>Loading...</option> : agents.map(agent => (
              <option key={agent.id} value={agent.id}>{agent.name}</option>
            ))}
          </select>

          <select
            value={selectedModelId}
            onChange={handleModelChange}
            className={styles.sidebarModelSelector} // <<< 新的 CSS 类
          >
            {sidebarMockModels.map(model => (
              <option key={model.id} value={model.id}>{model.name}</option>
            ))}
          </select>
        </div>
        <ChatInputInterface
          onSendMessage={handleSendMessage}
          existingFilesForDedupe={(getProjectById(data.projectId) || {}).files || []} // 传递当前项目的文件列表用于去重
          showSaveButton={false} showDownloadButton={false} showModelSelector={false} showDeepSearchButton={false}
          placeholderText="Ask..."
        />
      </div>
    </div>
  );
};

// --- RightSidebar 主组件 ---
const RightSidebar = () => {
  const {
    isRightSidebarOpen,
    rightSidebarView,
    lastClosedRightSidebarView,
    setRightSidebarViewTab,
    closeRightSidebar,
    openRightSidebarWithView,
  } = useSidebar();

  const handleCollapseSidebar = () => {
    console.log("RightSidebar: Collapse button clicked."); // 添加日志
    closeRightSidebar();
  };
  const handleExpandSidebar = () => {
    if (lastClosedRightSidebarView) {
      openRightSidebarWithView(lastClosedRightSidebarView);
    } else {
      openRightSidebarWithView({
        type: 'CHAT_CONTEXT_INFO',
        data: {
          files: [], notes: [],
          onUpdateChatFiles: () => console.warn("onUpdateChatFiles not fully initialized by HomePage yet."),
          onUpdateChatNotes: () => console.warn("onUpdateChatNotes not fully initialized by HomePage yet."),
        },
        activeTab: 'files'
      });
    }
  };

  console.log("RightSidebar MAIN RENDER: rightSidebarView type:", rightSidebarView?.type);
  if (rightSidebarView?.data) {
    console.log("RightSidebar MAIN RENDER: rightSidebarView.data.files count:", (rightSidebarView.data.files || rightSidebarView.data.projectFiles || []).length);
    console.log("RightSidebar MAIN RENDER: rightSidebarView.data.notes count:", (rightSidebarView.data.notes || rightSidebarView.data.projectNotes || []).length);
  }

  const [sidebarWidth, setSidebarWidth] = useState(320); // 初始宽度
  const sidebarRef = useRef(null);

  // 拖拽逻辑
  const handleMouseDown = (e) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = sidebarWidth;
    const onMouseMove = (moveEvent) => {
      const newWidth = Math.min(
        600, // 最大宽度
        Math.max(240, startWidth + (startX - moveEvent.clientX))
      );
      setSidebarWidth(newWidth);
    };
    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  };

  if (!isRightSidebarOpen) {
    return (<button onClick={handleExpandSidebar} className={`${styles.rightSidebar} ${styles.collapsedPullTab}`} title="Show Details" aria-label="Expand details sidebar"> <FiChevronsLeft /> </button>);
  }
  if (!rightSidebarView || !rightSidebarView.data) {
    return (<aside className={`${styles.rightSidebar} ${styles.open}`} style={{ width: sidebarWidth }}>
      <div className={styles.sidebarResizer} onMouseDown={handleMouseDown} />
      <div className={styles.sidebarTopControls}> <button onClick={handleCollapseSidebar} className={styles.collapseButtonInternal} title="Collapse Sidebar"><FiChevronsRight /></button> </div> <div className={styles.sidebarContent}> <p className={styles.emptyStateText}>Loading view data...</p> </div> </aside>);
  }

  let contentToRender = null;
  const availableTabs = [];
  const filesForTabs = Array.isArray(rightSidebarView.data.files) ? rightSidebarView.data.files : (Array.isArray(rightSidebarView.data.projectFiles) ? rightSidebarView.data.projectFiles : []);
  const notesForTabs = Array.isArray(rightSidebarView.data.notes) ? rightSidebarView.data.notes : (Array.isArray(rightSidebarView.data.projectNotes) ? rightSidebarView.data.projectNotes : []);

  // 根据视图类型决定数据来源和 Tab 结构
  if (rightSidebarView.type === 'FILE_DETAILS') {
    // <<< 文件浏览视图，有3个Tab >>>
    availableTabs.push({ key: 'chat', label: 'Chat' });
    availableTabs.push({ key: 'files', label: `Files (${rightSidebarView.data.projectFiles?.length || 0})` });
    availableTabs.push({ key: 'notes', label: `Notes (${rightSidebarView.data.projectNotes?.length || 0})` });
  } else if (rightSidebarView.type === 'PROJECT_DETAILS') {
    // <<< 项目仪表盘/聊天视图，有2个Tab >>>
    if (rightSidebarView.data.files !== undefined || rightSidebarView.data.projectFiles !== undefined) {
      const filesCount = (rightSidebarView.data.files || rightSidebarView.data.projectFiles || []).length;
      availableTabs.push({ key: 'files', label: `Files (${filesCount})` });
    }
    if (rightSidebarView.data.notes !== undefined || rightSidebarView.data.projectNotes !== undefined) {
      const notesCount = (rightSidebarView.data.notes || rightSidebarView.data.projectNotes || []).length;
      availableTabs.push({ key: 'notes', label: `Notes (${notesCount})` });
    }
  } else if (rightSidebarView.type === 'CHAT_CONTEXT_INFO') {
    // <<< 主聊天视图，有2个Tab >>>
    if (rightSidebarView.data.files !== undefined) {
      availableTabs.push({ key: 'files', label: `Files (${rightSidebarView.data.files.length})` });
    }
    if (rightSidebarView.data.notes !== undefined) {
      availableTabs.push({ key: 'notes', label: `Notes (${rightSidebarView.data.notes.length})` });
    }
  }

  const activeTabKey = rightSidebarView.activeTab || (availableTabs.length > 0 ? availableTabs[0].key : null);

  if (activeTabKey === 'files') {
    console.log("RightSidebar rendering FilesListView with files count:", filesForTabs.length); // <<< 添加日志
    contentToRender = <FilesListView files={filesForTabs} />;
  } else if (activeTabKey === 'notes') {
    contentToRender = <NotesListView notes={notesForTabs} />;
  } else if (activeTabKey === 'chat' && rightSidebarView.type === 'FILE_DETAILS') {
    contentToRender = <FileSpecificChatView data={rightSidebarView.data} />;
  } else {
    contentToRender = <p className={styles.emptyStateText}>Select a tab or no content for this view.</p>;
  }
  const handleTabChange = (tabKey) => setRightSidebarViewTab(tabKey);

  return (
    <aside
      ref={sidebarRef}
      className={`${styles.rightSidebar} ${styles.open}`}
      style={{ width: sidebarWidth }}
    >
      <div className={styles.sidebarResizer} onMouseDown={handleMouseDown} />
      <div className={styles.sidebarTopControls}>
        <button onClick={handleCollapseSidebar} className={styles.collapseButtonInternal} title="Collapse Sidebar"> <FiChevronsRight /> </button>
        {availableTabs.length > 0 && (
          <div className={styles.tabsContainerInternal}>
            {availableTabs.map(tab => (<button key={tab.key} onClick={() => handleTabChange(tab.key)} className={`${styles.tabButton} ${activeTabKey === tab.key ? styles.activeTab : ''}`}> {tab.label} </button>))}
          </div>
        )}
      </div>
      <div className={styles.sidebarContent}> {contentToRender} </div>
    </aside>
  );
};
export default RightSidebar;