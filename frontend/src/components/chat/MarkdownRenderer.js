import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Highlight, themes } from 'prism-react-renderer';
import { FiCopy, FiCheck } from 'react-icons/fi';
import styles from './MarkdownRenderer.module.css';

const MarkdownRenderer = ({ children, className = '' }) => {
  const [copiedCode, setCopiedCode] = React.useState(null);
  const [hasError, setHasError] = React.useState(false);

  const handleCopyCode = (code) => {
    navigator.clipboard.writeText(code).then(() => {
      setCopiedCode(code);
      setTimeout(() => setCopiedCode(null), 2000);
    });
  };

  // 错误边界处理
  React.useEffect(() => {
    const handleError = (error) => {
      console.error('MarkdownRenderer error:', error);
      setHasError(true);
    };

    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);

  // 如果出错，回退到普通文本显示
  if (hasError) {
    return (
      <div className={`${styles.fallbackContent} ${className}`}>
        <p>{children || '内容渲染失败'}</p>
      </div>
    );
  }

  // 如果没有内容，返回空div（用于流式响应过程中）
  if (!children && children !== '') {
    return <div className={className}></div>;
  }

  // 如果是空字符串，也正常处理（流式响应开始时）
  if (children === '') {
    return <div className={className}></div>;
  }

  const CodeBlock = ({ children, className, ...props }) => {
    const match = /language-(\w+)/.exec(className || '');
    const language = match ? match[1] : '';
    const code = String(children).replace(/\n$/, '');

    if (!language) {
      // 内联代码
      return <code className={styles.inlineCode} {...props}>{children}</code>;
    }

    // 代码块
    return (
      <div className={styles.codeBlockContainer}>
        <div className={styles.codeBlockHeader}>
          <span className={styles.codeLanguage}>{language}</span>
          <button
            className={styles.copyButton}
            onClick={() => handleCopyCode(code)}
            title="复制代码"
          >
            {copiedCode === code ? <FiCheck /> : <FiCopy />}
          </button>
        </div>
        <Highlight theme={themes.github} code={code} language={language}>
          {({ className, style, tokens, getLineProps, getTokenProps }) => (
            <pre className={`${className} ${styles.codeBlock}`} style={style}>
              {tokens.map((line, i) => (
                <div key={i} {...getLineProps({ line, key: i })}>
                  <span className={styles.lineNumber}>{i + 1}</span>
                  {line.map((token, key) => (
                    <span key={key} {...getTokenProps({ token, key })} />
                  ))}
                </div>
              ))}
            </pre>
          )}
        </Highlight>
      </div>
    );
  };

  return (
    <div className={`${styles.markdownContent} ${className}`}>
      <ReactMarkdown
        components={{
          code: CodeBlock,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer; 