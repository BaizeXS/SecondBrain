// 文件上传诊断工具
// src/utils/uploadDiagnostic.js

import apiService from '../services/apiService';

/**
 * 诊断文件上传问题
 * @param {File} file - 要诊断的文件
 * @param {number} spaceId - 空间ID
 * @returns {Promise<Object>} 诊断结果
 */
export const diagnoseFileUpload = async (file, spaceId) => {
  console.log('🔍 开始文件上传诊断...');
  
  const diagnosis = {
    file: {
      name: file.name,
      size: file.size,
      type: file.type || 'unknown',
      lastModified: new Date(file.lastModified).toISOString(),
    },
    spaceId,
    checks: {},
    errors: [],
    recommendations: []
  };

  // 1. 检查文件基本信息
  console.log('📄 文件信息:', diagnosis.file);
  
  // 2. 检查文件MIME类型
  diagnosis.checks.mimeType = {
    detected: file.type,
    expected: detectExpectedMimeType(file.name),
    isSupported: isMimeTypeSupported(file.type)
  };
  
  if (!diagnosis.checks.mimeType.isSupported) {
    diagnosis.errors.push(`不支持的文件类型: ${file.type}`);
    diagnosis.recommendations.push(`尝试使用支持的格式: .txt, .md, .pdf, .docx, .png, .jpg`);
  }

  // 3. 检查文件大小
  const maxSizeMB = 100; // 从后端配置获取
  diagnosis.checks.fileSize = {
    sizeMB: (file.size / 1024 / 1024).toFixed(2),
    maxSizeMB,
    isWithinLimit: file.size <= maxSizeMB * 1024 * 1024
  };
  
  if (!diagnosis.checks.fileSize.isWithinLimit) {
    diagnosis.errors.push(`文件大小超限: ${diagnosis.checks.fileSize.sizeMB}MB > ${maxSizeMB}MB`);
  }

  if (file.size === 0) {
    diagnosis.errors.push('文件为空');
  }

  // 4. 检查空间是否存在
  try {
    console.log('🏠 检查空间:', spaceId);
    const space = await apiService.space.getSpace(spaceId);
    diagnosis.checks.space = {
      exists: true,
      name: space.name,
      id: space.id,
      userCanEdit: true // 假设可以编辑，实际应该从空间权限检查
    };
    console.log('✅ 空间检查通过:', space.name);
  } catch (spaceError) {
    diagnosis.checks.space = {
      exists: false,
      error: spaceError.message
    };
    diagnosis.errors.push(`空间不存在或无权访问: ${spaceError.message}`);
    console.error('❌ 空间检查失败:', spaceError);
  }

  // 5. 检查认证状态
  try {
    const token = localStorage.getItem('access_token');
    diagnosis.checks.auth = {
      hasToken: !!token,
      tokenLength: token?.length || 0
    };
    
    if (!token) {
      diagnosis.errors.push('缺少认证token');
    }
  } catch (authError) {
    diagnosis.checks.auth = {
      hasToken: false,
      error: authError.message
    };
    diagnosis.errors.push('认证检查失败');
  }

  // 6. 尝试读取文件内容（预览）
  try {
    if (file.type.startsWith('text/') || file.name.endsWith('.md') || file.name.endsWith('.txt')) {
      const content = await readFileAsText(file);
      diagnosis.checks.content = {
        readable: true,
        contentLength: content.length,
        preview: content.substring(0, 100) + (content.length > 100 ? '...' : ''),
        encoding: 'UTF-8'
      };
    } else {
      diagnosis.checks.content = {
        readable: false,
        reason: '非文本文件'
      };
    }
  } catch (contentError) {
    diagnosis.checks.content = {
      readable: false,
      error: contentError.message
    };
  }

  // 7. 生成诊断报告
  const report = generateDiagnosisReport(diagnosis);
  console.log('📊 诊断报告:', report);

  return {
    ...diagnosis,
    report,
    canUpload: diagnosis.errors.length === 0
  };
};

/**
 * 根据文件名推测期望的MIME类型
 */
function detectExpectedMimeType(filename) {
  const ext = filename.toLowerCase().split('.').pop();
  const mimeTypes = {
    'md': 'text/markdown',
    'txt': 'text/plain',
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'csv': 'text/csv'
  };
  return mimeTypes[ext] || 'unknown';
}

/**
 * 检查MIME类型是否被后端支持
 */
function isMimeTypeSupported(mimeType) {
  const supportedTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain',
    'text/markdown',
    'text/csv',
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp'
  ];
  
  // 特殊处理：很多浏览器对.md文件返回空的MIME类型或text/plain
  if (!mimeType || mimeType === '') {
    return true; // 允许空MIME类型，后端会进一步验证
  }
  
  return supportedTypes.includes(mimeType);
}

/**
 * 读取文件为文本
 */
function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error('文件读取失败'));
    reader.readAsText(file, 'UTF-8');
  });
}

/**
 * 生成诊断报告
 */
function generateDiagnosisReport(diagnosis) {
  let report = '📋 文件上传诊断报告\n\n';
  
  // 文件信息
  report += `📄 文件信息:\n`;
  report += `  名称: ${diagnosis.file.name}\n`;
  report += `  大小: ${(diagnosis.file.size / 1024).toFixed(1)} KB\n`;
  report += `  类型: ${diagnosis.file.type || '未知'}\n\n`;
  
  // MIME类型检查
  report += `🎭 MIME类型检查:\n`;
  report += `  检测到: ${diagnosis.checks.mimeType?.detected || '无'}\n`;
  report += `  期望: ${diagnosis.checks.mimeType?.expected || '无'}\n`;
  report += `  支持: ${diagnosis.checks.mimeType?.isSupported ? '✅' : '❌'}\n\n`;
  
  // 文件大小检查
  report += `📏 文件大小检查:\n`;
  report += `  当前: ${diagnosis.checks.fileSize?.sizeMB || '0'} MB\n`;
  report += `  限制: ${diagnosis.checks.fileSize?.maxSizeMB || '100'} MB\n`;
  report += `  状态: ${diagnosis.checks.fileSize?.isWithinLimit ? '✅' : '❌'}\n\n`;
  
  // 空间检查
  report += `🏠 空间检查:\n`;
  if (diagnosis.checks.space?.exists) {
    report += `  空间: ${diagnosis.checks.space.name} (ID: ${diagnosis.checks.space.id})\n`;
    report += `  状态: ✅ 可访问\n\n`;
  } else {
    report += `  状态: ❌ ${diagnosis.checks.space?.error || '无法访问'}\n\n`;
  }
  
  // 认证检查
  report += `🔐 认证检查:\n`;
  report += `  Token: ${diagnosis.checks.auth?.hasToken ? '✅ 存在' : '❌ 缺失'}\n\n`;
  
  // 内容检查
  if (diagnosis.checks.content?.readable) {
    report += `📖 内容检查:\n`;
    report += `  可读性: ✅\n`;
    report += `  长度: ${diagnosis.checks.content.contentLength} 字符\n`;
    report += `  预览: ${diagnosis.checks.content.preview}\n\n`;
  }
  
  // 错误和建议
  if (diagnosis.errors.length > 0) {
    report += `❌ 发现问题:\n`;
    diagnosis.errors.forEach((error, index) => {
      report += `  ${index + 1}. ${error}\n`;
    });
    report += '\n';
  }
  
  if (diagnosis.recommendations.length > 0) {
    report += `💡 建议:\n`;
    diagnosis.recommendations.forEach((rec, index) => {
      report += `  ${index + 1}. ${rec}\n`;
    });
    report += '\n';
  }
  
  // 结论
  report += `🎯 结论: ${diagnosis.errors.length === 0 ? '✅ 文件应该可以正常上传' : '❌ 发现阻止上传的问题'}\n`;
  
  return report;
}

/**
 * 快速诊断当前选择的文件
 */
export const quickDiagnoseFile = async () => {
  return new Promise((resolve) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.md,.txt,.pdf,.docx,.png,.jpg,.jpeg';
    
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) {
        resolve({ error: '未选择文件' });
        return;
      }
      
      // 创建一个测试空间
      try {
        const tempSpace = await apiService.space.createSpace({
          name: `诊断测试空间 - ${new Date().toLocaleTimeString()}`,
          description: '文件上传诊断测试',
          is_public: false,
          tags: ['diagnostic', 'test']
        });
        
        const diagnosis = await diagnoseFileUpload(file, tempSpace.id);
        resolve(diagnosis);
      } catch (error) {
        resolve({ error: `创建测试空间失败: ${error.message}` });
      }
    };
    
    input.click();
  });
}; 