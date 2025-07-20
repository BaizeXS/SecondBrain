// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import NeuroCorePage from './pages/NeuroCorePage';
import ProjectPage from './pages/ProjectPage';
import FileViewPage from './pages/FileViewPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import RegisterPage from './pages/RegisterPage';
import MainLayout from './components/layout/MainLayout';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { SidebarProvider } from './contexts/SidebarContext';
import { ProjectProvider, useProjects } from './contexts/ProjectContext'; // <<< 导入 useProjects
import { ChatProvider } from './contexts/ChatContext'; // 新增：导入ChatProvider
import CreateProjectModal from './components/modals/CreateProjectModal'; // <<< 导入模态框
import TempPage from './pages/TempPage';
import AgentSettingsPage from './pages/AgentSettingsPage';
import { AgentProvider } from './contexts/AgentContext';
import ProfilePage from './pages/ProfilePage';
import SettingsPage from './pages/SettingsPage';
import './styles/global.css';

const ProtectedRoute = ({ children, showAppHeader = true, mainLayoutProps = {} }) => {
  const { isAuthenticated, loading } = useAuth();

  console.log('ProtectedRoute - isAuthenticated:', isAuthenticated, 'loading:', loading);

  if (loading) {
    return <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh'}}>
      Checking authentication...
    </div>;
  }

  if (!isAuthenticated) {
    console.log('User not authenticated, redirecting to login');
    return <Navigate to="/login" replace />;
  }

  console.log('User authenticated, rendering protected content');
  return (
    <MainLayout showAppHeader={showAppHeader} {...mainLayoutProps}>
      {children}
    </MainLayout>
  );
};

const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  console.log('PublicRoute - isAuthenticated:', isAuthenticated, 'loading:', loading);
  
  if (loading) {
    return <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh'}}>
      Checking authentication...
    </div>;
  }
  
  if (isAuthenticated) {
    console.log('User already authenticated, redirecting to home');
    return <Navigate to="/" replace />;
  }
  
  return children;
};

// 一个小的包装组件，用于从 Context 获取模态框状态和控制函数
const GlobalCreateProjectModal = () => {
  const { isCreateProjectModalOpen, closeCreateProjectModal, addProject } = useProjects();
  const navigate = useNavigate(); // 用于创建后导航

  console.log("GlobalCreateProjectModal: Rendering. isCreateProjectModalOpen state from context:", isCreateProjectModalOpen); // <<< 添加日志

  const handleCreateProjectFromModal = (name, description, files /* File[] */) => {
    console.log("GlobalModal: Creating project - ", name, description, files);
    const newProjectData = { name, description, files, createdAt: new Date().toISOString() };
    const createdProject = addProject(newProjectData); // addProject 现在应处理文件并返回创建的项目
    if (createdProject && createdProject.id) {
      navigate(`/neurocore/project/${createdProject.id}`);
    }
  };

  return (
    <CreateProjectModal
      isOpen={isCreateProjectModalOpen}
      onClose={closeCreateProjectModal}
      onCreateProject={handleCreateProjectFromModal}
    />
  );
};

function App() {
  return (
    <Router> {/* React Router v6 推荐 Router 在所有 Context Provider 之外，但也可以在内，只要 Provider 包裹 Routes */}
      <AuthProvider>
        <ProjectProvider> {/* <<< 将 ProjectProvider 移到这里 */}
          <AgentProvider>
            <ChatProvider> {/* 新增：添加ChatProvider */}
              <SidebarProvider>
                <Routes>
                  {/* 公共路由 */}
                  <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
                  <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
                  <Route path="/forgot-password" element={<PublicRoute><ForgotPasswordPage /></PublicRoute>} />

                  {/* 受保护的路由 - 这些路由下的组件会使用 MainLayout，其中 LeftSidebar 会用 useProjects */}
                  <Route
                    path="/neurocore/project/:projectId/file/:fileId" // <<< 更具体的路径
                    element={
                      <ProtectedRoute>
                        <FileViewPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/neurocore/project/:projectId" // <<< 更通用的路径
                    element={<ProtectedRoute><ProjectPage /></ProtectedRoute>}
                  />
                  <Route
                    path="/neurocore"
                    element={<ProtectedRoute><NeuroCorePage /></ProtectedRoute>}
                  />
                  <Route
                    path="/"
                    element={<ProtectedRoute><HomePage /></ProtectedRoute>}
                  />
                  <Route
                    path="/temp" // 定义 temp 页面的路由
                    element={<ProtectedRoute><TempPage /></ProtectedRoute>}
                  />
                  <Route
                    path="/agent-settings" // 或你想要的路径
                    element={<ProtectedRoute><AgentSettingsPage /></ProtectedRoute>}
                  />
                  <Route
                    path="/profile"
                    element={<ProtectedRoute><ProfilePage /></ProtectedRoute>}
                  />
                  <Route
                    path="/settings" // <<< 添加设置页面路由
                    element={<ProtectedRoute><SettingsPage /></ProtectedRoute>}
                  />
                  {/* 其他路由，例如 404 页面或默认重定向 */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </SidebarProvider>
            </ChatProvider> {/* 新增：关闭ChatProvider */}
          </AgentProvider>
          <GlobalCreateProjectModal /> {/* <<< 在这里渲染全局模态框 */}
        </ProjectProvider>
      </AuthProvider>
    </Router >
  );
}

export default App;