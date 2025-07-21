import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 如果children是空的或者很短，可能是流式响应过程，不显示错误
      if (!this.props.children || (typeof this.props.children === 'string' && this.props.children.length < 10)) {
        return <div>{this.props.children}</div>;
      }

      return (
        <div style={{
          padding: '8px 10px',
          background: '#fff3cd',
          border: '1px solid #ffeaa7',
          borderRadius: '4px',
          color: '#856404',
          fontSize: '0.85rem'
        }}>
          <details>
            <summary style={{ cursor: 'pointer', fontWeight: '500' }}>
              内容渲染异常 (点击查看详情)
            </summary>
            <div style={{ marginTop: '5px', fontFamily: 'monospace', fontSize: '0.8rem' }}>
              {this.props.children}
            </div>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary; 