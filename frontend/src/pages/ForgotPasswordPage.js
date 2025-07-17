// src/pages/ForgotPasswordPage.js
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import styles from './AuthPage.module.css'; // 我们将创建一个通用的 AuthPage 样式
import appLogo from '../assets/images/app-logo.png';
import { MdLanguage, MdEmail } from 'react-icons/md';

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState(''); // 用于显示成功或错误信息
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setIsLoading(true);

    if (!email.trim()) {
      setMessage('Please enter your email address.');
      setIsLoading(false);
      return;
    }
    if (!/\S+@\S+\.\S+/.test(email)) {
        setMessage('Please enter a valid email address.');
        setIsLoading(false);
        return;
    }

    // 模拟 API 调用
    try {
      // 假设的 API 调用: await apiService.sendPasswordResetEmail(email);
      console.log('Password reset email requested for:', email);
      await new Promise(resolve => setTimeout(resolve, 1000)); // 模拟网络延迟

      setMessage('If an account with that email exists, a password reset link has been sent.');
      setEmail(''); // 清空输入框
    } catch (error) {
      setMessage(error.message || 'Failed to send reset email. Please try again.');
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
          <h2 className={styles.formTitle}>忘记密码</h2>
          <p className={styles.formSubtitle}>请输入您的邮箱地址以接收密码重置指引。</p>

          <form onSubmit={handleSubmit} className={styles.authForm}>
            <div className={styles.inputGroup}>
              <label htmlFor="email">邮箱地址</label>
              <div className={styles.inputWithIcon}>
                <MdEmail className={styles.inputIcon} />
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="请输入您的注册邮箱"
                  aria-label="Email Address for password reset"
                />
              </div>
            </div>

            {message && (
              <p className={`${styles.message} ${message.startsWith('If an account') ? styles.successMessage : styles.errorMessage}`}>
                {message}
              </p>
            )}

            <button type="submit" className={styles.submitButton} disabled={isLoading}>
              {isLoading ? '发送中...' : '发送重置邮件'}
            </button>
          </form>

          <p className={styles.authLinkText}>
            记起密码了?{' '}
            <Link to="/login" className={styles.authLink}>
              返回登录
            </Link>
          </p>
        </div>
      </main>

      <footer className={styles.pageFooter}>
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

export default ForgotPasswordPage;