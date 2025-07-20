// src/pages/LoginPage.js
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import styles from './LoginPage.module.css'; // 假设这是你之前创建并正在使用的 AuthPage 通用样式
import appLogo from '../assets/images/app-logo.png';
import loginPageImage from '../assets/images/login-image.jpg';
import { useAuth } from '../contexts/AuthContext';
import { FaEnvelope, FaLock, FaGoogle, FaApple, FaWeibo, FaEye, FaEyeSlash } from 'react-icons/fa'; // 引入眼睛图标
import { MdLanguage } from 'react-icons/md';
import { useTranslation } from 'react-i18next';

const LoginPage = () => {
  const { t, i18n } = useTranslation();
  console.log('Inspecting i18n object:', i18n);
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
      // 使用 email 作为 username
      const result = await login(email, password);
      if (result.success) {
        navigate('/');
      } else {
        setError(result.error || 'Invalid email or password.');
      }
    } catch (err) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLanguageChange = () => {
    const newLang = i18n.language === 'zh' ? 'en' : 'zh';
    i18n.changeLanguage(newLang);
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
          <MdLanguage className={styles.languageIcon}/> {t('loginPage.languageButton')}
        </button>
      </header>

      <main className={styles.loginPageContainer}>
        <div className={styles.leftPanel}>
          <img src={loginPageImage} alt="Learning Community" className={styles.panelImage} />
          {/* <<< 5. 替换左侧面板的硬编码文本 */}
          <h1 className={styles.leftPanelTitle}>{t('loginPage.leftPanel.title')}</h1>
          <p className={styles.leftPanelText}>{t('loginPage.leftPanel.text')}</p>
        </div>

        <div className={styles.rightPanel}>
          {/* <<< 6. 替换右侧面板的所有硬编码文本 */}
          <h2 className={styles.welcomeTitle}>{t('loginPage.welcomeTitle')}</h2>
          <p className={styles.welcomeSubtitle}>{t('loginPage.welcomeSubtitle')}</p>

          <form onSubmit={handleLogin} className={styles.loginForm}>
            <div className={styles.inputGroup}>
              <label htmlFor="email">{t('loginPage.emailLabel')}</label>
              <div className={styles.inputWithIcon}>
                <FaEnvelope className={styles.inputIcon} />
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t('loginPage.emailPlaceholder')}
                  aria-label="Email Address"
                />
              </div>
            </div>

            <div className={styles.inputGroup}>
              <label htmlFor="password">{t('loginPage.passwordLabel')}</label>
              <div className={`${styles.inputWithIcon} ${styles.passwordInputContainer}`}>
                <FaLock className={styles.inputIcon} />
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t('loginPage.passwordPlaceholder')}
                  aria-label="Password"
                />
                <button
                  type="button"
                  onClick={togglePasswordVisibility}
                  className={styles.passwordVisibilityToggle}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <FaEyeSlash /> : <FaEye />}
                </button>
              </div>
            </div>

            <div className={styles.formOptions}>
              <label htmlFor="rememberMe" className={styles.rememberMeLabel}>
                <input
                  type="checkbox"
                  id="rememberMe"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                {t('loginPage.rememberMe')}
              </label>
              <Link to="/forgot-password" className={styles.forgotPasswordLink}>
                {t('loginPage.forgotPassword')}
              </Link>
            </div>

            {error && <p className={styles.errorMessage}>{error}</p>}

            <button type="submit" className={styles.loginButton} disabled={isLoading}>
              {isLoading ? t('loginPage.loggingInButton') : t('loginPage.loginButton')}
            </button>
          </form>

          <div className={styles.separator}>
            <span>{t('loginPage.socialLoginSeparator')}</span>
          </div>
          
          <div className={styles.socialLogin}>
            <button className={styles.socialButton} aria-label="Login with Google"><FaGoogle /></button>
            <button className={styles.socialButton} aria-label="Login with Apple"><FaApple /></button>
            <button className={styles.socialButton} aria-label="Login with Weibo"><FaWeibo /></button>
          </div>

          <p className={styles.signUpText}>
            {t('loginPage.signUpText')}{' '}
            <Link to="/register" className={styles.signUpLink}>
              {t('loginPage.signUpLink')}
            </Link>
          </p>
        </div>
      </main>

      <footer className={styles.pageFooter}>
        {/* ... (页脚内容保持不变) ... */}
        <p>© 2024 Second Brain. All rights reserved</p>
        <nav className={styles.footerLinks}>
          <Link to="/help">Help Center</Link>
          <Link to="/privacy">Privacy Policy</Link>
          <Link to="/terms">Terms of Service</Link>
        </nav>
      </footer>
    </div>
  );
};

export default LoginPage;