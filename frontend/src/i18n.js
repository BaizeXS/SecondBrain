// src/i18n.js
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';

i18n
  // 使用 i18next-http-backend 插件，它允许从远程服务器或本地 public 文件夹加载翻译文件
  .use(Backend)
  // 使用 i18next-browser-languagedetector 插件，自动检测用户语言
  .use(LanguageDetector)
  // 将 i18n 实例传递给 react-i18next
  .use(initReactI18next)
  // 初始化 i18next
  .init({
    // 设置备用语言（如果当前语言的翻译缺失，则使用此语言）
    fallbackLng: 'en',
    debug: true, // 在开发模式下开启 debug 输出，方便排查问题
    
    // 默认的命名空间
    ns: ['translation'],
    defaultNS: 'translation',

    interpolation: {
      escapeValue: false, // React 已经做了 XSS 防护，所以这里可以设为 false
    },
    
    backend: {
      // 翻译文件的加载路径
      // '{{lng}}' 会被替换为语言代码（如 'en'）
      // '{{ns}}' 会被替换为命名空间（如 'translation'）
      loadPath: '/locales/{{lng}}/{{ns}}.json',
    },
  });

export default i18n;