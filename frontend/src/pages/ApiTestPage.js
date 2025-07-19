import React, { useState, useEffect } from 'react';
import { authAPI, spaceAPI, documentAPI, chatAPI } from '../services/apiService';
import { useAuth } from '../contexts/AuthContext';
import './ApiTestPage.module.css';

const ApiTestPage = () => {
  const { isAuthenticated, user, login, logout } = useAuth();
  const [testResults, setTestResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loginForm, setLoginForm] = useState({
    username: '',
    password: ''
  });

  const addTestResult = (testName, success, message, data = null) => {
    setTestResults(prev => [...prev, {
      id: Date.now(),
      testName,
      success,
      message,
      data,
      timestamp: new Date().toISOString()
    }]);
  };

  const clearResults = () => {
    setTestResults([]);
  };

  // 测试API连接
  const testApiConnection = async () => {
    try {
      setLoading(true);
      addTestResult('API连接测试', true, 'API服务连接正常');
    } catch (error) {
      addTestResult('API连接测试', false, `连接失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 测试认证
  const testAuth = async () => {
    try {
      setLoading(true);
      const result = await login(loginForm.username, loginForm.password);
      if (result.success) {
        addTestResult('用户认证测试', true, '登录成功', { user: result.user });
      } else {
        addTestResult('用户认证测试', false, `登录失败: ${result.error}`);
      }
    } catch (error) {
      addTestResult('用户认证测试', false, `认证错误: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 测试空间API
  const testSpaceAPI = async () => {
    try {
      setLoading(true);
      const spaces = await spaceAPI.getSpaces({ limit: 5 });
      addTestResult('空间API测试', true, `获取到 ${spaces.spaces?.length || 0} 个空间`, spaces);
    } catch (error) {
      addTestResult('空间API测试', false, `空间API错误: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 测试文档API
  const testDocumentAPI = async () => {
    try {
      setLoading(true);
      const documents = await documentAPI.getDocuments({ limit: 5 });
      addTestResult('文档API测试', true, `获取到 ${documents.documents?.length || 0} 个文档`, documents);
    } catch (error) {
      addTestResult('文档API测试', false, `文档API错误: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 测试聊天API
  const testChatAPI = async () => {
    try {
      setLoading(true);
      const conversations = await chatAPI.getConversations({ limit: 5 });
      addTestResult('聊天API测试', true, `获取到 ${conversations.conversations?.length || 0} 个对话`, conversations);
    } catch (error) {
      addTestResult('聊天API测试', false, `聊天API错误: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 运行所有测试
  const runAllTests = async () => {
    clearResults();
    await testApiConnection();
    if (isAuthenticated) {
      await testSpaceAPI();
      await testDocumentAPI();
      await testChatAPI();
    } else {
      addTestResult('认证状态', false, '用户未登录，跳过需要认证的API测试');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    await testAuth();
  };

  const handleLogout = async () => {
    try {
      await logout();
      addTestResult('用户登出', true, '登出成功');
    } catch (error) {
      addTestResult('用户登出', false, `登出失败: ${error.message}`);
    }
  };

  return (
    <div className="api-test-page">
      <div className="header">
        <h1>API连接测试</h1>
        <p>测试前后端API连接和功能</p>
      </div>

      <div className="test-section">
        <h2>认证测试</h2>
        {!isAuthenticated ? (
          <form onSubmit={handleLogin} className="login-form">
            <div className="form-group">
              <label>用户名:</label>
              <input
                type="text"
                value={loginForm.username}
                onChange={(e) => setLoginForm(prev => ({ ...prev, username: e.target.value }))}
                placeholder="输入用户名"
                required
              />
            </div>
            <div className="form-group">
              <label>密码:</label>
              <input
                type="password"
                value={loginForm.password}
                onChange={(e) => setLoginForm(prev => ({ ...prev, password: e.target.value }))}
                placeholder="输入密码"
                required
              />
            </div>
            <button type="submit" disabled={loading}>
              {loading ? '登录中...' : '登录'}
            </button>
          </form>
        ) : (
          <div className="user-info">
            <p>当前用户: {user?.username || '未知'}</p>
            <button onClick={handleLogout}>登出</button>
          </div>
        )}
      </div>

      <div className="test-section">
        <h2>API测试</h2>
        <div className="test-buttons">
          <button onClick={testApiConnection} disabled={loading}>
            测试API连接
          </button>
          <button onClick={testSpaceAPI} disabled={loading || !isAuthenticated}>
            测试空间API
          </button>
          <button onClick={testDocumentAPI} disabled={loading || !isAuthenticated}>
            测试文档API
          </button>
          <button onClick={testChatAPI} disabled={loading || !isAuthenticated}>
            测试聊天API
          </button>
          <button onClick={runAllTests} disabled={loading}>
            运行所有测试
          </button>
          <button onClick={clearResults}>
            清除结果
          </button>
        </div>
      </div>

      <div className="test-section">
        <h2>测试结果</h2>
        <div className="test-results">
          {testResults.length === 0 ? (
            <p>暂无测试结果</p>
          ) : (
            testResults.map(result => (
              <div key={result.id} className={`test-result ${result.success ? 'success' : 'error'}`}>
                <div className="result-header">
                  <span className="test-name">{result.testName}</span>
                  <span className="result-status">
                    {result.success ? '✅ 成功' : '❌ 失败'}
                  </span>
                  <span className="timestamp">
                    {new Date(result.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="result-message">{result.message}</div>
                {result.data && (
                  <details className="result-data">
                    <summary>查看数据</summary>
                    <pre>{JSON.stringify(result.data, null, 2)}</pre>
                  </details>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="test-section">
        <h2>API状态</h2>
        <div className="status-info">
          <p><strong>认证状态:</strong> {isAuthenticated ? '已登录' : '未登录'}</p>
          <p><strong>当前用户:</strong> {user?.username || '无'}</p>
          <p><strong>API基础URL:</strong> {process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1'}</p>
          <p><strong>测试结果数量:</strong> {testResults.length}</p>
        </div>
      </div>
    </div>
  );
};

export default ApiTestPage; 