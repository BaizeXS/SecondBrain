// 文件上传调试工具
// 帮助诊断文件上传问题

import apiService from '../services/apiService';

/**
 * 调试文件上传问题
 * @param {File} file - 要调试的文件
 * @returns {Promise<Object>} 调试结果
 */
export const debugFileUpload = async (file) => {
  console.log('🔍 开始文件上传调试...');
  
  const debugInfo = {
    file: {
      name: file.name,
      size: file.size,
      type: file.type || 'unknown',
      lastModified: new Date(file.lastModified).toISOString(),
    },
    checks: {
      basicValidation: null,
      spaceAvailability: null,
      fileContent: null
    },
    recommendations: []
  };

  // 1. 基本文件验证
  console.log('📄 检查文件基本信息...');
  debugInfo.checks.basicValidation = {
    hasName: !!file.name,
    hasSize: file.size > 0,
    sizeInMB: (file.size / 1024 / 1024).toFixed(2),
    withinSizeLimit: file.size <= 100 * 1024 * 1024,
    hasValidType: !!file.type
  };

  if (!debugInfo.checks.basicValidation.hasName) {
    debugInfo.recommendations.push('文件名为空');
  }
  
  if (!debugInfo.checks.basicValidation.hasSize) {
    debugInfo.recommendations.push('文件大小为0');
  }
  
  if (!debugInfo.checks.basicValidation.withinSizeLimit) {
    debugInfo.recommendations.push(`文件太大: ${debugInfo.checks.basicValidation.sizeInMB}MB (限制: 100MB)`);
  }

  // 2. 检查是否有可用的空间
  console.log('🏠 检查空间可用性...');
  try {
    const spaces = await apiService.space.getSpaces();
    debugInfo.checks.spaceAvailability = {
      hasSpaces: spaces && spaces.length > 0,
      spaceCount: spaces ? spaces.length : 0,
      canCreateSpace: true // 假设用户有创建空间的权限
    };
    
    if (!debugInfo.checks.spaceAvailability.hasSpaces) {
      debugInfo.recommendations.push('当前用户没有可用的空间');
    }
  } catch (error) {
    console.error('空间检查失败:', error);
    debugInfo.checks.spaceAvailability = {
      hasSpaces: false,
      error: error.message
    };
    debugInfo.recommendations.push('无法获取空间列表: ' + error.message);
  }

  // 3. 文件内容检查
  console.log('📖 检查文件内容...');
  try {
    const reader = new FileReader();
    const readPromise = new Promise((resolve, reject) => {
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject(reader.error);
    });
    
    reader.readAsArrayBuffer(file);
    const arrayBuffer = await readPromise;
    
    debugInfo.checks.fileContent = {
      canRead: true,
      bufferSize: arrayBuffer.byteLength,
      isNotEmpty: arrayBuffer.byteLength > 0
    };
    
    if (!debugInfo.checks.fileContent.isNotEmpty) {
      debugInfo.recommendations.push('文件内容为空');
    }
  } catch (error) {
    console.error('文件内容读取失败:', error);
    debugInfo.checks.fileContent = {
      canRead: false,
      error: error.message
    };
    debugInfo.recommendations.push('无法读取文件内容: ' + error.message);
  }

  // 生成调试报告
  console.log('📋 调试报告:', debugInfo);
  return debugInfo;
};

/**
 * 格式化调试报告为用户友好的文本
 * @param {Object} debugInfo - 调试信息
 * @returns {string} 格式化的报告
 */
export const formatDebugReport = (debugInfo) => {
  let report = '📋 文件上传调试报告\n\n';
  
  report += '📄 文件信息:\n';
  report += `  名称: ${debugInfo.file.name}\n`;
  report += `  大小: ${debugInfo.file.size} bytes (${debugInfo.checks.basicValidation?.sizeInMB || 0} MB)\n`;
  report += `  类型: ${debugInfo.file.type}\n`;
  report += `  修改时间: ${debugInfo.file.lastModified}\n\n`;
  
  report += '✅ 基本验证:\n';
  const basic = debugInfo.checks.basicValidation;
  if (basic) {
    report += `  有文件名: ${basic.hasName ? '✅' : '❌'}\n`;
    report += `  有内容: ${basic.hasSize ? '✅' : '❌'}\n`;
    report += `  大小合规: ${basic.withinSizeLimit ? '✅' : '❌'}\n`;
    report += `  有类型: ${basic.hasValidType ? '✅' : '❌'}\n`;
  }
  
  report += '\n🏠 空间检查:\n';
  const space = debugInfo.checks.spaceAvailability;
  if (space) {
    if (space.error) {
      report += `  状态: ❌ 错误 - ${space.error}\n`;
    } else {
      report += `  可用空间: ${space.hasSpaces ? '✅' : '❌'} (${space.spaceCount || 0}个)\n`;
    }
  }
  
  report += '\n📖 文件内容:\n';
  const content = debugInfo.checks.fileContent;
  if (content) {
    if (content.error) {
      report += `  读取状态: ❌ 错误 - ${content.error}\n`;
    } else {
      report += `  可读取: ${content.canRead ? '✅' : '❌'}\n`;
      report += `  有内容: ${content.isNotEmpty ? '✅' : '❌'}\n`;
    }
  }
  
  if (debugInfo.recommendations.length > 0) {
    report += '\n⚠️ 建议:\n';
    debugInfo.recommendations.forEach(rec => {
      report += `  - ${rec}\n`;
    });
  } else {
    report += '\n🎯 结论: 文件看起来可以正常上传！\n';
  }
  
  return report;
};

/**
 * 快速调试并显示报告
 * @param {File} file - 要调试的文件
 */
export const quickDebugAndShow = async (file) => {
  try {
    const debugInfo = await debugFileUpload(file);
    const report = formatDebugReport(debugInfo);
    
    // 在控制台显示
    console.log(report);
    
    // 也可以弹窗显示
    alert(report);
    
    return debugInfo;
  } catch (error) {
    const errorMessage = `调试过程出错: ${error.message}`;
    console.error(errorMessage, error);
    alert(errorMessage);
    throw error;
  }
}; 