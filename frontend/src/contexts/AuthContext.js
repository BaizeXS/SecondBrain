// src/contexts/AuthContext.js
import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false); // 初始为 false
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // <--- 初始为 true

  useEffect(() => {
    console.log("AuthContext: Checking local storage for authentication...");
    const storedAuth = localStorage.getItem('isAuthenticated') === 'true';
    const storedUser = localStorage.getItem('user');

    if (storedAuth) {
      console.log("AuthContext: User was authenticated from local storage.");
      setIsAuthenticated(true);
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch (e) {
          console.error("AuthContext: Failed to parse user from local storage", e);
          localStorage.removeItem('user'); // 清除无效的用户数据
        }
      }
    } else {
      console.log("AuthContext: No authentication found in local storage.");
    }
    setLoading(false); // <--- 检查完毕后，设置 loading 为 false
  }, []); // 空依赖数组，只在组件挂载时运行一次

  const login = useCallback(async (email, password) => {
    // ... (你的登录逻辑，它会 setIsAuthenticated(true) 和 setLoading(false) 如果需要)
    // 确保登录成功后 setIsAuthenticated(true)
    // 在这个模拟版本中，我们假设登录成功后 localStorage 会被设置，下次刷新时 useEffect 会处理
    return new Promise((resolve) => {
      setTimeout(() => {
        if (email === 'lchhku@hku.com' && password === '123456') {
          const userData = { id: 'user1', username: 'lchhku', email: 'lchhku@hku.com' };
          localStorage.setItem('isAuthenticated', 'true');
          localStorage.setItem('user', JSON.stringify(userData));
          setIsAuthenticated(true);
          setUser(userData);
          console.log("AuthContext: User logged in.");
          resolve(true);
        } else {
          console.log("AuthContext: Login failed.");
          resolve(false);
        }
      }, 500);
    });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
    setUser(null);
    console.log("AuthContext: User logged out.");
    // 导航到登录页通常在组件层面处理，比如在 Header 的登出按钮点击后
  }, []);

  // 如果初始认证状态还在加载中，可以显示一个加载界面或什么都不渲染
  // 这可以防止在 loading 为 true 时子组件（如路由）过早渲染和判断
  if (loading) {
    // 你可以返回一个全局的加载指示器，或者 null
    // 返回 null 会导致页面暂时空白，直到 loading 变为 false
    return <div>Loading Application...</div>; // 或者一个更美观的 Spinner
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};