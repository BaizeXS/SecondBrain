// src/pages/LoginPage.js
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import styles from './LoginPage.module.css'; // 假设这是你之前创建并正在使用的 AuthPage 通用样式
import appLogo from '../assets/images/app-logo.png';
import loginPageImage from '../assets/images/login-image.jpg';
import { useAuth } from '../contexts/AuthContext';
import { FaEnvelope, FaLock, FaGoogle, FaApple, FaWeibo, FaEye, FaEyeSlash } from 'react-icons/fa'; // 引入眼睛图标
import { MdLanguage } from 'react-icons/md';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false); // <--- 新增状态
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleLogin = async (e) => {
    // ... (登录逻辑保持不变) ...
    e.preventDefault();
    setError('');
    setIsLoading(true);

    if (!email.trim() || !password.trim()) {
      setError('Email and password cannot be empty!');
      setIsLoading(false);
      return;
    }
    if (!/\S+@\S+\.\S+/.test(email)) {
        setError('Please enter a valid email address.');
        setIsLoading(false);
        return;
    }

    try {
      const loggedInSuccessfully = await login(email, password);
      if (loggedInSuccessfully) {
        navigate('/');
      } else {
        setError('Invalid email or password.');
      }
    } catch (err) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLanguageChange = () => {
    alert('Language change functionality to be implemented!');
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword); // <--- 切换密码可见性状态
  };

  return (
    <div className={styles.pageWrapper}> {/* 使用你定义的通用 pageWrapper 或 LoginPage 专属的 */}
      <header className={styles.pageHeader}>
        {/* ... (页眉内容保持不变) ... */}
        <div className={styles.logoContainer}>
          <img src={appLogo} alt="Second Brain Logo" className={styles.appLogoIcon} />
          <span className={styles.appNameGlobal}>Second Brain</span>
        </div>
        <button onClick={handleLanguageChange} className={styles.languageButton}>
          <MdLanguage className={styles.languageIcon}/> 中文 (简体)
        </button>
      </header>

      <main className={styles.loginPageContainer}>
        <div className={styles.leftPanel}>
          {/* ... (左侧栏内容保持不变) ... */}
          <img src={loginPageImage} alt="Learning Community" className={styles.panelImage} />
          <h1 className={styles.leftPanelTitle}>加入我们的学习社区</h1>
          <p className={styles.leftPanelText}>开启你的学习之旅，发现无限可能</p>
        </div>

        <div className={styles.rightPanel}>
          <h2 className={styles.welcomeTitle}>欢迎回来</h2>
          <p className={styles.welcomeSubtitle}>请登录你的账号</p>

          <form onSubmit={handleLogin} className={styles.loginForm}>
            <div className={styles.inputGroup}>
              <label htmlFor="email">邮箱地址</label>
              <div className={styles.inputWithIcon}>
                <FaEnvelope className={styles.inputIcon} />
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
              <div className={`${styles.inputWithIcon} ${styles.passwordInputContainer}`}> {/* 添加一个容器类 */}
                <FaLock className={styles.inputIcon} />
                <input
                  type={showPassword ? "text" : "password"} // <--- 根据状态切换 type
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="请输入密码"
                  aria-label="Password"
                />
                <button
                  type="button" // <--- 重要：设为 type="button" 防止触发表单提交
                  onClick={togglePasswordVisibility}
                  className={styles.passwordVisibilityToggle}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <FaEyeSlash /> : <FaEye />} {/* <--- 根据状态显示不同图标 */}
                </button>
              </div>
            </div>

            <div className={styles.formOptions}>
              {/* ... (记住我和忘记密码保持不变) ... */}
              <label htmlFor="rememberMe" className={styles.rememberMeLabel}>
                <input
                  type="checkbox"
                  id="rememberMe"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                记住我
              </label>
              <Link to="/forgot-password" className={styles.forgotPasswordLink}>
                忘记密码?
              </Link>
            </div>

            {error && <p className={styles.errorMessage}>{error}</p>}

            <button type="submit" className={styles.loginButton} disabled={isLoading}>
              {isLoading ? '登录中...' : '登录'}
            </button>
          </form>

          {/* ... (第三方登录和注册链接保持不变) ... */}
          <div className={styles.separator}>
            <span>或</span>
          </div>
          <div className={styles.socialLogin}>
            <button className={styles.socialButton} aria-label="Login with Google">
              <FaGoogle />
            </button>
            <button className={styles.socialButton} aria-label="Login with Apple">
              <FaApple />
            </button>
            <button className={styles.socialButton} aria-label="Login with Weibo">
              <FaWeibo />
            </button>
          </div>
          <p className={styles.signUpText}>
            还没有账号?{' '}
            <Link to="/register" className={styles.signUpLink}>
              立即注册
            </Link>
          </p>
        </div>
      </main>

      <footer className={styles.pageFooter}>
        {/* ... (页脚内容保持不变) ... */}
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

export default LoginPage;