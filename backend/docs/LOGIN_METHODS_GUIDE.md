# Second Brain 登录方式说明

## 重要：后端支持多种登录方式

后端的登录接口支持**用户名和邮箱**两种登录方式，前端可以根据需要选择。

## 登录端点

### 1. Form-data格式登录（推荐用于Web表单）
- **端点**: `POST /api/v1/auth/login`
- **Content-Type**: `application/x-www-form-urlencoded`

### 2. JSON格式登录（推荐用于现代前端框架）
- **端点**: `POST /api/v1/auth/login/json`
- **Content-Type**: `application/json`

## 登录方式

### 方式1：使用用户名登录
```javascript
// Form-data格式
const formData = new FormData();
formData.append('username', 'demo_user');
formData.append('password', 'Demo123456!');

// 或 JSON格式
const response = await fetch('/api/v1/auth/login/json', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'demo_user',
    password: 'Demo123456!'
  })
});
```

### 方式2：使用邮箱登录（推荐）
```javascript
// Form-data格式
const formData = new FormData();
formData.append('username', 'demo@example.com');  // 注意：字段名仍然是username
formData.append('password', 'Demo123456!');

// 或 JSON格式
const response = await fetch('/api/v1/auth/login/json', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'demo@example.com',  // 注意：字段名仍然是username
    password: 'Demo123456!'
  })
});
```

## 前端实现建议

### 1. 统一的登录组件（支持邮箱/用户名）
```jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from './api';

function LoginForm() {
  const [credential, setCredential] = useState(''); // 可以是邮箱或用户名
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/auth/login/json', {
        username: credential,  // 后端会自动识别是邮箱还是用户名
        password: password
      });

      const { access_token, refresh_token } = response.data;
      
      // 保存tokens
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      // 跳转到主页
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || '登录失败，请检查邮箱/用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <div>
        <label>邮箱或用户名</label>
        <input
          type="text"
          value={credential}
          onChange={(e) => setCredential(e.target.value)}
          placeholder="输入邮箱地址或用户名"
          required
        />
      </div>
      
      <div>
        <label>密码</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="输入密码"
          required
        />
      </div>
      
      {error && <div className="error">{error}</div>}
      
      <button type="submit" disabled={loading}>
        {loading ? '登录中...' : '登录'}
      </button>
    </form>
  );
}
```

### 2. 自动检测输入类型（可选）
```javascript
function isEmail(input) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(input);
}

// 在登录表单中显示提示
const inputType = isEmail(credential) ? '邮箱' : '用户名';
console.log(`使用${inputType}登录`);
```

### 3. 登录服务封装
```javascript
class AuthService {
  /**
   * 登录方法，支持邮箱和用户名
   * @param {string} credential - 邮箱或用户名
   * @param {string} password - 密码
   * @returns {Promise<{access_token: string, refresh_token: string}>}
   */
  static async login(credential, password) {
    try {
      // 使用JSON格式登录端点
      const response = await api.post('/auth/login/json', {
        username: credential,  // 后端会自动识别
        password: password
      });
      
      return response.data;
    } catch (error) {
      if (error.response?.status === 401) {
        throw new Error('邮箱/用户名或密码错误');
      }
      throw error;
    }
  }
  
  /**
   * 使用社交账号登录（如果实现）
   */
  static async socialLogin(provider, token) {
    // 预留接口
  }
}

// 使用示例
try {
  // 可以传入邮箱
  const tokens = await AuthService.login('user@example.com', 'password123');
  
  // 也可以传入用户名
  const tokens = await AuthService.login('username', 'password123');
} catch (error) {
  console.error('登录失败:', error.message);
}
```

## 注册时的注意事项

用户注册时需要同时提供用户名和邮箱：
```javascript
const registerData = {
  username: "uniqueusername",    // 必须唯一
  email: "user@example.com",      // 必须唯一
  password: "SecurePass123!",
  full_name: "用户全名"
};
```

这样用户注册后可以使用用户名或邮箱任意一种方式登录。

## API响应格式

无论使用哪种方式登录，成功后的响应格式都是相同的：
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## 错误处理

登录失败时会返回：
```json
{
  "detail": "用户名或密码错误",
  "status_code": 401,
  "timestamp": 12345.678,
  "path": "/api/v1/auth/login"
}
```

## 总结

1. **后端已完全支持邮箱和用户名登录**
2. **前端只需在`username`字段传递邮箱或用户名即可**
3. **推荐使用JSON格式的登录端点（`/auth/login/json`）**
4. **用户体验建议：使用一个输入框，标签为"邮箱或用户名"**

这样的设计让用户可以灵活选择自己习惯的登录方式，提升用户体验。