// src/pages/FileViewPage.js
import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import styles from './FileViewPage.module.css';
import { useSidebar } from '../contexts/SidebarContext';
import { useProjects } from '../contexts/ProjectContext';
import { FiX, FiEdit, FiGlobe } from 'react-icons/fi';

import { defaultProps } from 'prism-react-renderer';
import { Highlight, themes } from 'prism-react-renderer'; // <<< 导入 Highlight 和 themes
// import vsDark from 'prism-react-renderer/themes/vsDark'; // 另一个选择
import ReactMarkdown from 'react-markdown';
import { Document, Page, pdfjs } from 'react-pdf';

// 设置 react-pdf 的 worker 来源
// 这对于 Create React App (CRA) 是必需的，确保 worker.js 文件能被正确加载
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

// --- Mocking file content and details ---
// 从 RightSidebar.js 移过来或共享，确保 simplify 函数可用
const simplifyFileForContext = f => ({ 
  id: f.id, 
  name: f.name, 
  size: f.size, 
  type: f.type, 
  preview: f.preview, 
  uploadedAt: f.uploadedAt,
  isAiGenerated: f.isAiGenerated,
  aiAgent: f.aiAgent
});
const simplifyNoteForContext = n => ({ 
  id: n.id, 
  name: n.name, 
  preview: n.preview, 
  content: n.content, 
  createdAt: n.createdAt,
  isAiGenerated: n.isAiGenerated,
  aiAgent: n.aiAgent
});

// --- CodeViewer 子组件修改 ---
const CodeViewer = ({ code, language }) => {
  // 使用从 themes 导出的 dracula 主题
  const theme = themes.dracula; // <<< 获取主题
  return (
    // <<< 不再需要 defaultProps >>>
    <Highlight theme={theme} code={code.trim()} language={language}>
      {({ className, style, tokens, getLineProps, getTokenProps }) => (
        <pre className={`${className} ${styles.codePreview}`} style={{ ...style }}> {/* 合并样式 */}
          {tokens.map((line, i) => (
            <div key={i} {...getLineProps({ line, key: i })}>
              <span className={styles.lineNumber}>{i + 1}</span>
              {line.map((token, key) => (
                <span key={key} {...getTokenProps({ token, key })} />
              ))}
            </div>
          ))}
        </pre>
      )}
    </Highlight>
  );
};


// --- PdfViewer 子组件修改 (如果需要) ---
const PdfViewer = ({ file }) => {
  const [numPages, setNumPages] = useState(null);
  function onDocumentLoadSuccess({ numPages: nextNumPages }) {
    setNumPages(nextNumPages);
  }
  const fileToLoad = file.rawFile || file.url || file;

  return (
    <div className={styles.pdfViewerContainer}>
      <Document file={fileToLoad} onLoadSuccess={onDocumentLoadSuccess}>
        {Array.from(new Array(numPages || 0), (el, index) => ( // <<< 添加 || 0 避免 numPages 为 null 时出错
          <Page
            key={`page_${index + 1}`}
            pageNumber={index + 1}
            // 新版本中，这两个 prop 可能已不再需要或默认开启
            // renderTextLayer={true}
            // renderAnnotationLayer={true}
            width={Math.min(window.innerWidth * 0.8, 800)}
          />
        ))}
      </Document>
    </div>
  );
};
const FileViewPage = () => {
  const { projectId, fileId } = useParams();
  const navigate = useNavigate();
  const { openRightSidebarWithView, isRightSidebarOpen, rightSidebarView, closeRightSidebar } = useSidebar();
  const { getProjectById, updateProject, loadingProjects, projects } = useProjects(); // <<< 获取 updateProject

  const [currentFile, setCurrentFile] = useState(null);
  const [loading, setLoading] = useState(true);

  // --- 核心修改：重写回调函数，使其不依赖本地 state ---
  const handleUpdateProjectFiles = useCallback((updatedSimplifiedFiles) => {
    // 这个回调被调用时，直接从 context 获取最新项目数据
    const currentProjectInContext = getProjectById(projectId);
    if (!currentProjectInContext || !updateProject) {
      console.error("FileViewPage callback: Cannot update files, project not found in context or updateProject is missing.");
      return;
    }
    // 注意：这里的 updatedSimplifiedFiles 是 RightSidebar 基于旧的 projectData.files prop 和新文件合并的
    // 所以，这里应该只包含新的文件
    // 我们需要重新思考 RightSidebar 的逻辑，但先让这个回调正确工作
    // 假设 updatedSimplifiedFiles 是一个包含了所有文件（旧+新）的列表
    console.log("FileViewPage: handleUpdateProjectFiles called with:", updatedSimplifiedFiles);
    // 直接调用 updateProject 更新
    updateProject(projectId, { files: updatedSimplifiedFiles });
  }, [projectId, updateProject, getProjectById]); // 依赖项现在是稳定的

  const handleUpdateProjectNotes = useCallback((updatedSimplifiedNotes) => {
    const currentProjectInContext = getProjectById(projectId);
    if (!currentProjectInContext || !updateProject) {
      console.error("FileViewPage callback: Cannot update notes, project not found in context or updateProject is missing.");
      return;
    }
    console.log("FileViewPage: handleUpdateProjectNotes called with:", updatedSimplifiedNotes);
    updateProject(projectId, { notes: updatedSimplifiedNotes });
  }, [projectId, updateProject, getProjectById]);


  useEffect(() => {
    console.log(`FileViewPage Effect: Fired. ProjectId: ${projectId}, ContextLoading: ${loadingProjects}`);
    if (loadingProjects) {
      if (!loading) setLoading(true);
      return;
    }

    const foundProject = getProjectById(projectId);

    if (foundProject) {
      const fileData = foundProject.files?.find(f => f.id === fileId);

      if (fileData) {
        setCurrentFile(fileData);

        // 如果侧边栏是打开的，就用最新的数据和回调去更新它
        if (isRightSidebarOpen) {
          const sidebarDataPayload = {
            currentFileId: fileId,
            currentFileName: fileData.name,
            projectId: projectId,
            projectFiles: (foundProject.files || []).map(simplifyFileForContext),
            projectNotes: (foundProject.notes || []).map(simplifyNoteForContext),
            onUpdateProjectFiles: handleUpdateProjectFiles, // <<< 传递新的、更稳定的回调
            onUpdateProjectNotes: handleUpdateProjectNotes, // <<< 传递新的、更稳定的回调
          };

          // 只有在视图类型或核心数据真正改变时才更新，避免不必要的重渲染
          if (
            rightSidebarView?.type !== 'FILE_DETAILS' ||
            rightSidebarView.data?.currentFileId !== fileId ||
            JSON.stringify(rightSidebarView.data?.projectFiles) !== JSON.stringify(sidebarDataPayload.projectFiles) ||
            JSON.stringify(rightSidebarView.data?.projectNotes) !== JSON.stringify(sidebarDataPayload.projectNotes)
          ) {
            openRightSidebarWithView({
              type: 'FILE_DETAILS',
              data: sidebarDataPayload,
              activeTab: rightSidebarView?.activeTab // 保持当前tab，不自动切换
            });
          }
        }
      }
      // 如果 isRightSidebarOpen 是 false，我们什么都不做，尊重用户的关闭操作。

      if (loading) setLoading(false); // 在数据设置完成后解除加载状态
    } else {
      // 项目未找到
      console.error(`FileViewPage: Project with ID ${projectId} not found.`);
      navigate(`/neurocore`, { replace: true });
      if (loading) setLoading(false);
    }
  }, [
    projectId, fileId, projects, // <<< 直接依赖 context 的 projects 数组
    loadingProjects, isRightSidebarOpen, rightSidebarView,
    getProjectById, navigate, openRightSidebarWithView,
    handleUpdateProjectFiles, handleUpdateProjectNotes, loading
  ]);

  const handleCloseFile = () => {
    navigate(`/neurocore/project/${projectId}`);
  };

  if (loading || loadingProjects) {
    return <div className={styles.loadingState}>Loading file...</div>;
  }
  if (!currentFile) {
    // 这个状态通常在加载完成但文件未找到时短暂显示，然后就会被 navigate 走
    return <div className={styles.errorState}>File not found. Redirecting...</div>;
  }

  // --- 文件内容渲染器 (占位符) ---
  const renderFileContent = () => {
    if (!currentFile.content && !currentFile.rawFile && !currentFile.url) {
      return <p>No content available for this file.</p>;
    }
    // 根据文件扩展名或 MIME 类型判断
    const fileName = currentFile.name.toLowerCase();

    if (fileName.endsWith('.js') || fileName.endsWith('.jsx') || fileName.endsWith('.ts') || fileName.endsWith('.tsx')) {
      return <CodeViewer code={currentFile.content || ''} language="jsx" />;
    }
    if (fileName.endsWith('.css')) {
      return <CodeViewer code={currentFile.content || ''} language="css" />;
    }
    if (fileName.endsWith('.json')) {
      return <CodeViewer code={currentFile.content || ''} language="json" />;
    }
    if (fileName.endsWith('.md')) {
      return <div className={styles.markdownPreview}><ReactMarkdown>{currentFile.content || ''}</ReactMarkdown></div>;
    }
    if (fileName.endsWith('.pdf') || currentFile.type === 'application/pdf') {
      return <PdfViewer file={currentFile} />;
    }
    if (currentFile.type?.startsWith('text/')) {
      return <pre className={styles.textPreview}>{currentFile.content || ''}</pre>;
    }

    return <p><em>Preview for file type "{currentFile.type}" is not yet available.</em></p>;
  };

  return (
    <div className={styles.fileViewPage}>
      <div className={styles.fileContentWrapper}>
        <div className={styles.contentHeader}>
          <h1 className={styles.fileName}>{currentFile.name}</h1>
          <div className={styles.contentActions}>
            <button className={styles.actionButton}><FiGlobe /> Translate</button>
            <button className={styles.actionButton}><FiEdit /> Edit</button>
            <button onClick={handleCloseFile} className={styles.closeButton} title="Close file view">×</button>
          </div>
        </div>
        <div className={styles.fileContentArea}>
          {renderFileContent()}
        </div>
      </div>
    </div>
  );
};

export default FileViewPage;