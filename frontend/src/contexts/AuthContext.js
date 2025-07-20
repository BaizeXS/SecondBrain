// src/contexts/AuthContext.js
import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { authAPI, userAPI } from '../services/apiService';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // 检查token是否有效
  const checkAuthStatus = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setIsAuthenticated(false);
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      // 尝试获取当前用户信息来验证token
      const userData = await userAPI.getCurrentUser();
      setIsAuthenticated(true);
      setUser(userData);
      console.log("AuthContext: Token validation successful, user authenticated");
    } catch (error) {
      console.error('Token validation failed:', error);
      // Token无效，清除本地存储
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  const login = useCallback(async (username, password) => {
    try {
      setLoading(true);
      const response = await authAPI.login({ username, password });
      
      // 确保 token 已经保存（authAPI.login 中已经保存了）
      if (response.access_token) {
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('refresh_token', response.refresh_token);
      }
      
      // 保存用户信息到localStorage
      const userInfo = response.user || { username };
      localStorage.setItem('user', JSON.stringify(userInfo));
      
      setIsAuthenticated(true);
      setUser(userInfo);
      
      console.log("AuthContext: User logged in successfully.");
      
      // 不要页面刷新，直接返回成功
      // window.location.reload(); // 删除这行
      
      return { success: true, user: userInfo };
    } catch (error) {
      console.error("AuthContext: Login failed.", error);
      return { success: false, error: error.message };
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (userData) => {
    try {
      setLoading(true);
      const response = await authAPI.register(userData);
      
      // 注册成功后自动登录
      const loginResponse = await authAPI.login({
        username: userData.username,
        password: userData.password
      });
      
      const userInfo = loginResponse.user || { username: userData.username };
      localStorage.setItem('user', JSON.stringify(userInfo));
      setIsAuthenticated(true);
      setUser(userInfo);
      
      console.log("AuthContext: User registered and logged in successfully.");
      return { success: true, user: userInfo };
    } catch (error) {
      console.error("AuthContext: Registration failed.", error);
      return { success: false, error: error.message };
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error("Logout API call failed:", error);
    } finally {
      // 无论API调用是否成功，都清除本地状态
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      setIsAuthenticated(false);
      setUser(null);
      console.log("AuthContext: User logged out.");
    }
  }, []);

  const refreshToken = useCallback(async () => {
    try {
      const response = await authAPI.refreshToken();
      console.log("AuthContext: Token refreshed successfully.");
      return { success: true };
    } catch (error) {
      console.error("AuthContext: Token refresh failed.", error);
      // 刷新失败，清除认证状态
      await logout();
      return { success: false, error: error.message };
    }
  }, [logout]);

  const changePassword = useCallback(async (oldPassword, newPassword) => {
    try {
      await authAPI.changePassword({
        old_password: oldPassword,
        new_password: newPassword
      });
      console.log("AuthContext: Password changed successfully.");
      return { success: true };
    } catch (error) {
      console.error("AuthContext: Password change failed.", error);
      return { success: false, error: error.message };
    }
  }, []);

  const resetPassword = useCallback(async (email) => {
    try {
      await authAPI.resetPassword(email);
      console.log("AuthContext: Password reset email sent.");
      return { success: true };
    } catch (error) {
      console.error("AuthContext: Password reset failed.", error);
      return { success: false, error: error.message };
    }
  }, []);

  const confirmResetPassword = useCallback(async (token, newPassword) => {
    try {
      await authAPI.confirmResetPassword(token, newPassword);
      console.log("AuthContext: Password reset confirmed successfully.");
      return { success: true };
    } catch (error) {
      console.error("AuthContext: Password reset confirmation failed.", error);
      return { success: false, error: error.message };
    }
  }, []);

  return (
    <AuthContext.Provider value={{ 
      isAuthenticated, 
      user, 
      login, 
      logout, 
      register,
      refreshToken,
      changePassword,
      resetPassword,
      confirmResetPassword,
      loading 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};