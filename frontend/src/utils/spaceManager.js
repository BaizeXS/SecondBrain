// 空间管理工具
// 帮助用户查看和管理空间使用情况

import apiService from '../services/apiService';

/**
 * 检查用户空间使用情况
 * @returns {Promise<Object>} 空间使用情况报告
 */
export const checkSpaceUsage = async () => {
  try {
    console.log('🔍 检查空间使用情况...');
    
    const spaces = await apiService.space.getSpaces({ limit: 100 });
    const userInfo = await apiService.user.getUserInfo();
    
    // 计算限制
    const maxSpaces = userInfo.is_premium ? 10 : 5;
    const currentSpaces = spaces.spaces?.length || 0;
    const remainingSpaces = maxSpaces - currentSpaces;
    
    const report = {
      currentSpaces,
      maxSpaces,
      remainingSpaces,
      isAtLimit: currentSpaces >= maxSpaces,
      isPremium: userInfo.is_premium,
      spaces: spaces.spaces || [],
      suggestions: []
    };
    
    // 生成建议
    if (report.isAtLimit) {
      report.suggestions.push('您已达到空间数量上限');
      report.suggestions.push('考虑删除不需要的空间以释放配额');
      report.suggestions.push('或升级到高级账户以获得更多空间');
    } else if (remainingSpaces <= 1) {
      report.suggestions.push('空间配额即将用完，建议整理现有空间');
    }
    
    // 找出可能可以删除的空间
    const emptySpaces = report.spaces.filter(space => 
      (space.document_count || 0) === 0 && 
      (space.note_count || 0) === 0
    );
    
    if (emptySpaces.length > 0) {
      report.suggestions.push(`发现 ${emptySpaces.length} 个空的空间可以考虑删除`);
      report.emptySpaces = emptySpaces;
    }
    
    console.log('📋 空间使用报告:', report);
    return report;
    
  } catch (error) {
    console.error('❌ 检查空间使用情况失败:', error);
    throw error;
  }
};

/**
 * 格式化空间使用报告
 * @param {Object} report - 空间使用报告
 * @returns {string} 格式化的报告文本
 */
export const formatSpaceUsageReport = (report) => {
  let text = '📊 空间使用情况报告\n\n';
  
  text += `📈 当前使用: ${report.currentSpaces}/${report.maxSpaces} 个空间\n`;
  text += `💎 账户类型: ${report.isPremium ? '高级账户' : '普通账户'}\n`;
  text += `🆓 剩余配额: ${report.remainingSpaces} 个空间\n\n`;
  
  if (report.spaces.length > 0) {
    text += '📁 现有空间列表:\n';
    report.spaces.forEach((space, index) => {
      text += `  ${index + 1}. "${space.name}" - ${space.document_count || 0}个文档, ${space.note_count || 0}个笔记\n`;
    });
    text += '\n';
  }
  
  if (report.suggestions.length > 0) {
    text += '💡 建议:\n';
    report.suggestions.forEach(suggestion => {
      text += `  • ${suggestion}\n`;
    });
    text += '\n';
  }
  
  if (report.emptySpaces && report.emptySpaces.length > 0) {
    text += '🗑️ 可删除的空空间:\n';
    report.emptySpaces.forEach(space => {
      text += `  • "${space.name}" (创建于 ${new Date(space.created_at).toLocaleDateString()})\n`;
    });
  }
  
  return text;
};

/**
 * 快速检查并显示空间使用情况
 */
export const quickCheckAndShow = async () => {
  try {
    const report = await checkSpaceUsage();
    const formattedReport = formatSpaceUsageReport(report);
    
    console.log(formattedReport);
    alert(formattedReport);
    
    return report;
  } catch (error) {
    const errorMessage = `检查空间使用情况失败: ${error.message}`;
    console.error(errorMessage, error);
    alert(errorMessage);
    throw error;
  }
};

/**
 * 寻找适合文件上传的空间
 * @returns {Promise<Object|null>} 找到的空间或null
 */
export const findSuitableSpaceForFiles = async () => {
  try {
    const spaces = await apiService.space.getSpaces({ limit: 100 });
    
    if (!spaces.spaces || spaces.spaces.length === 0) {
      return null;
    }
    
    // 优先寻找专门的文件/聊天空间
    let targetSpace = spaces.spaces.find(space => 
      space.name.toLowerCase().includes('chat') || 
      space.name.toLowerCase().includes('file') || 
      space.name.toLowerCase().includes('upload') ||
      space.tags?.includes('chat') || 
      space.tags?.includes('files')
    );
    
    // 如果没找到，使用第一个可用空间
    if (!targetSpace) {
      targetSpace = spaces.spaces[0];
    }
    
    console.log('🎯 找到适合的文件空间:', targetSpace.name, '(ID:', targetSpace.id, ')');
    return targetSpace;
    
  } catch (error) {
    console.error('❌ 寻找适合空间失败:', error);
    return null;
  }
}; 