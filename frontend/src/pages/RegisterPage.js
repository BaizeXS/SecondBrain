// src/pages/RegisterPage.js
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import styles from './AuthPage.module.css'; // 复用 AuthPage 样式
import appLogo from '../assets/images/app-logo.png';
import { MdLanguage, MdEmail, MdLockOutline, MdPersonOutline } from 'react-icons/md'; // MdLockOutline for confirm password
import { useAuth } from '../contexts/AuthContext';

const RegisterPage = () => {
  const [username, setUsername] = useState(''); // 可选的用户名
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { register } = useAuth();

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

    // 调用真实的注册 API
    try {
      const userData = {
        username: username.trim() || email.trim(), // 如果没有用户名，使用email作为用户名
        email: email.trim(),
        password: password,
        full_name: username.trim() || email.split('@')[0] // 使用用户名或email前缀作为全名
      };
      
      const result = await register(userData);
      
      if (result.success) {
        // 注册成功，已自动登录，跳转到首页
        navigate('/');
      } else {
        setError(result.error || 'Registration failed. Please try again.');
      }
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
          <MdLanguage className={styles.languageIcon}/> English (US)
        </button>
      </header>

      <main className={styles.authPageContainer}>
        <div className={styles.authFormWrapper}>
          <h2 className={styles.formTitle}>Create Your Account</h2>
          <p className={styles.formSubtitle}>Join Second Brain, Start Your Intelligent Learning Journey.</p>

          <form onSubmit={handleSubmit} className={styles.authForm}>
            <div className={styles.inputGroup}>
              <label htmlFor="username">Username (Optional)</label>
              <div className={styles.inputWithIcon}>
                <MdPersonOutline className={styles.inputIcon} />
                <input
                  type="text"
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Please enter username"
                  aria-label="Username"
                />
              </div>
            </div>

            <div className={styles.inputGroup}>
              <label htmlFor="email">Email Address</label>
              <div className={styles.inputWithIcon}>
                <MdEmail className={styles.inputIcon} />
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Please enter email address"
                  aria-label="Email Address"
                />
              </div>
            </div>

            <div className={styles.inputGroup}>
              <label htmlFor="password">Password</label>
              <div className={styles.inputWithIcon}>
                <MdLockOutline className={styles.inputIcon} /> {/* 使用不同的图标 */}
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Please enter password (at least 6 characters)"
                  aria-label="Password"
                />
              </div>
            </div>

            <div className={styles.inputGroup}>
              <label htmlFor="confirmPassword">Confirm Password</label>
              <div className={styles.inputWithIcon}>
                <MdLockOutline className={styles.inputIcon} />
                <input
                  type="password"
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Please enter password again"
                  aria-label="Confirm Password"
                />
              </div>
            </div>

            {error && <p className={styles.errorMessage}>{error}</p>}

            <button type="submit" className={styles.submitButton} disabled={isLoading}>
              {isLoading ? 'Registering...' : 'Register Now'}
            </button>
          </form>

          <p className={styles.authLinkText}>
            Already have an account?{' '}
            <Link to="/login" className={styles.authLink}>
              Login Now
            </Link>
          </p>
        </div>
      </main>
      <footer className={styles.pageFooter}>
         {/* ... 页脚内容同上 ... */}
        <p>© 2024 Second Brain. All rights reserved</p>
        <nav className={styles.footerLinks}>
          <Link to="/help">Help Center</Link>
          <Link to="/privacy">Privacy Policy</Link>
          <Link to="/terms">Service Terms</Link>
        </nav>
      </footer>
    </div>
  );
};

export default RegisterPage;