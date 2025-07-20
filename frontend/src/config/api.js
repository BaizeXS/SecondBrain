// src/config/api.js

// API基础配置
const API_CONFIG = {
  // 开发环境
  development: {
    BASE_URL: process.env.REACT_APP_API_URL || '/api/v1',
    TIMEOUT: 30000,
    RETRY_ATTEMPTS: 3,
  },
  
  // 生产环境
  production: {
    BASE_URL: process.env.REACT_APP_API_URL || '/api/v1',
    TIMEOUT: 30000,
    RETRY_ATTEMPTS: 3,
  },
  
  // 测试环境
  test: {
    BASE_URL: 'http://localhost:8000/api/v1',
    TIMEOUT: 10000,
    RETRY_ATTEMPTS: 1,
  },
};

// 获取当前环境
const getCurrentEnvironment = () => {
  if (process.env.NODE_ENV === 'production') {
    return 'production';
  } else if (process.env.NODE_ENV === 'test') {
    return 'test';
  } else {
    return 'development';
  }
};

// 获取当前环境的配置
const getCurrentApiConfig = () => {
  const env = getCurrentEnvironment();
  return API_CONFIG[env];
};

// 获取API基础URL
export const getApiBaseUrl = () => {
  return getCurrentApiConfig().BASE_URL;
};

// 获取请求超时时间
export const getApiTimeout = () => {
  return getCurrentApiConfig().TIMEOUT;
};

// 获取重试次数
export const getApiRetryAttempts = () => {
  return getCurrentApiConfig().RETRY_ATTEMPTS;
};

// 获取完整的API配置
export const getApiConfig = () => {
  return getCurrentApiConfig();
};

// 默认导出
export default {
  getApiBaseUrl,
  getApiTimeout,
  getApiRetryAttempts,
  getApiConfig,
}; 