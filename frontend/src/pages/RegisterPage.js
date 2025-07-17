// src/pages/RegisterPage.js
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import styles from './AuthPage.module.css'; // 复用 AuthPage 样式
import appLogo from '../assets/images/app-logo.png';
import { MdLanguage, MdEmail, MdLockOutline, MdPersonOutline } from 'react-icons/md'; // MdLockOutline for confirm password

const RegisterPage = () => {
  const [username, setUsername] = useState(''); // 可选的用户名
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    if (!email.trim() || !password.trim() || !confirmPassword.trim()) {
      setError('All fields (Email, Password, Confirm Password) are required.');
      setIsLoading(false);
      return;
    }
    if (!/\S+@\S+\.\S+/.test(email)) {
        setError('Please enter a valid email address.');
        setIsLoading(false);
        return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      setIsLoading(false);
      return;
    }
    if (password.length < 6) { // 简单密码长度校验
        setError('Password must be at least 6 characters long.');
        setIsLoading(false);
        return;
    }

    // 模拟 API 调用
    try {
      // 假设的 API 调用: await apiService.registerUser({ username, email, password });
      console.log('Registering user:', { username, email, password });
      await new Promise(resolve => setTimeout(resolve, 1500));

      // 注册成功后通常会跳转到登录页，或自动登录并跳转到首页
      alert('Registration successful! Please login.'); // 简单提示
      navigate('/login');
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLanguageChange = () => {
    alert('Language change functionality to be implemented!');
  };

  return (
    <div className={styles.pageWrapper}>
       <header className={styles.pageHeader}>
        <div className={styles.logoContainer}>
          <img src={appLogo} alt="Second Brain Logo" className={styles.appLogoIcon} />
          <span className={styles.appNameGlobal}>Second Brain</span>
        </div>
        <button onClick={handleLanguageChange} className={styles.languageButton}>
          <MdLanguage className={styles.languageIcon}/> 中文 (简体)
        </button>
      </header>

      <main className={styles.authPageContainer}>
        <div className={styles.authFormWrapper}>
          <h2 className={styles.formTitle}>创建您的账户</h2>
          <p className={styles.formSubtitle}>加入 Second Brain，开启智能学习之旅。</p>

          <form onSubmit={handleSubmit} className={styles.authForm}>
            <div className={styles.inputGroup}>
              <label htmlFor="username">用户名 (可选)</label>
              <div className={styles.inputWithIcon}>
                <MdPersonOutline className={styles.inputIcon} />
                <input
                  type="text"
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="请输入用户名"
                  aria-label="Username"
                />
              </div>
            </div>

            <div className={styles.inputGroup}>
              <label htmlFor="email">邮箱地址</label>
              <div className={styles.inputWithIcon}>
                <MdEmail className={styles.inputIcon} />
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="请输入邮箱地址"
                  aria-label="Email Address"
                />
              </div>
            </div>

            <div className={styles.inputGroup}>
              <label htmlFor="password">密码</label>
              <div className={styles.inputWithIcon}>
                <MdLockOutline className={styles.inputIcon} /> {/* 使用不同的图标 */}
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="请输入密码 (至少6位)"
                  aria-label="Password"
                />
              </div>
            </div>

            <div className={styles.inputGroup}>
              <label htmlFor="confirmPassword">确认密码</label>
              <div className={styles.inputWithIcon}>
                <MdLockOutline className={styles.inputIcon} />
                <input
                  type="password"
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="请再次输入密码"
                  aria-label="Confirm Password"
                />
              </div>
            </div>

            {error && <p className={styles.errorMessage}>{error}</p>}

            <button type="submit" className={styles.submitButton} disabled={isLoading}>
              {isLoading ? '注册中...' : '立即注册'}
            </button>
          </form>

          <p className={styles.authLinkText}>
            已经有账户了?{' '}
            <Link to="/login" className={styles.authLink}>
              立即登录
            </Link>
          </p>
        </div>
      </main>
      <footer className={styles.pageFooter}>
         {/* ... 页脚内容同上 ... */}
        <p>© 2024 Second Brain. 保留所有权利</p>
        <nav className={styles.footerLinks}>
          <Link to="/help">帮助中心</Link>
          <Link to="/privacy">隐私政策</Link>
          <Link to="/terms">服务条款</Link>
        </nav>
      </footer>
    </div>
  );
};

export default RegisterPage;