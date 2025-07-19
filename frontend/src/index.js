// src/index.js (最终修正版)
import React, { Suspense } from 'react';
import ReactDOM from 'react-dom/client';
import { I18nextProvider } from 'react-i18next'; // 1. 导入 I18nextProvider
import i18n from './i18n'; // 2. 导入我们创建的 i18n 实例，而不是只为了副作用

import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    {/* 3. 使用 I18nextProvider 包裹所有内容，并传入 i18n 实例 */}
    <I18nextProvider i18n={i18n}>
      <Suspense fallback="loading...">
        <App />
      </Suspense>
    </I18nextProvider>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
