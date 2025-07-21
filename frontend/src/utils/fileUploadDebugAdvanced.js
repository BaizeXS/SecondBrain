// 高级文件上传调试工具
// 专门调试文件上传到AI读取的完整流程

import apiService from '../services/apiService';

/**
 * 测试完整的文件上传到AI读取流程
 * @param {File} file - 要测试的文件
 * @returns {Promise<Object>} 完整的测试结果
 */
export const testFileToAIFlow = async (file) => {
  console.log('🧪 开始测试文件上传到AI读取的完整流程...');
  
  const testResult = {
    success: false,
    steps: [],
    file: {
      name: file.name,
      size: file.size,
      type: file.type
    },
    spaceId: null,
    documentId: null,
    documentContent: null,
    aiResponse: null,
    error: null
  };

  try {
    // 步骤1: 寻找或创建空间
    console.log('📁 步骤1: 寻找合适的空间...');
    const spaces = await apiService.space.getSpaces({ limit: 100 });
    
    let targetSpace = null;
    if (spaces.spaces && spaces.spaces.length > 0) {
      targetSpace = spaces.spaces.find(space => 
        space.name.toLowerCase().includes('chat') || 
        space.name.toLowerCase().includes('file') ||
        space.tags?.includes('chat') || 
        space.tags?.includes('files')
      ) || spaces.spaces[0];
    }
    
    if (!targetSpace) {
      throw new Error('没有可用的空间');
    }
    
    testResult.spaceId = targetSpace.id;
    testResult.steps.push({
      step: 'find_space',
      success: true,
      data: { 
        spaceId: targetSpace.id, 
        spaceName: targetSpace.name 
      }
    });
    console.log('✅ 找到空间:', targetSpace.name, '(ID:', targetSpace.id, ')');

    // 步骤2: 上传文件
    console.log('⬆️ 步骤2: 上传文件...');
    const uploadedDoc = await apiService.document.uploadDocument(
      targetSpace.id,
      file,
      file.name,
      ['test', 'ai-reading-test']
    );
    
    testResult.documentId = uploadedDoc.id;
    testResult.steps.push({
      step: 'upload_file',
      success: true,
      data: {
        documentId: uploadedDoc.id,
        filename: uploadedDoc.filename,
        contentType: uploadedDoc.content_type
      }
    });
    console.log('✅ 文件上传成功, Document ID:', uploadedDoc.id);

    // 步骤3: 验证文档内容
    console.log('📖 步骤3: 验证文档内容...');
    const documentDetails = await apiService.document.getDocument(uploadedDoc.id);
    
    testResult.documentContent = documentDetails.content;
    testResult.steps.push({
      step: 'verify_content',
      success: !!documentDetails.content,
      data: {
        hasContent: !!documentDetails.content,
        contentLength: documentDetails.content ? documentDetails.content.length : 0,
        contentPreview: documentDetails.content ? documentDetails.content.substring(0, 200) + '...' : null
      }
    });
    
    if (!documentDetails.content) {
      console.warn('⚠️ 文档没有内容或内容为空');
    } else {
      console.log('✅ 文档有内容，长度:', documentDetails.content.length, '字符');
    }

    // 步骤4: 创建对话
    console.log('💬 步骤4: 创建对话...');
    const conversation = await apiService.chat.createConversation({
      title: `文件测试对话 - ${file.name}`,
      mode: 'chat',
      space_id: targetSpace.id
    });
    
    testResult.steps.push({
      step: 'create_conversation',
      success: true,
      data: {
        conversationId: conversation.id,
        spaceId: conversation.space_id
      }
    });
    console.log('✅ 对话创建成功, ID:', conversation.id, '关联空间:', conversation.space_id);

    // 步骤5: 发送消息给AI，包含文档ID
    console.log('🤖 步骤5: 发送消息给AI...');
    const testMessage = `请分析这个文件的内容：${file.name}`;
    
    const streamRequestData = {
      model: 'openrouter/auto',
      messages: [
        { role: 'system', content: '你是一个文档分析助手。请仔细分析用户提供的文档内容。' },
        { role: 'user', content: testMessage }
      ],
      temperature: 0.7,
      stream: false, // 使用非流式以便获取完整响应
      conversation_id: conversation.id,
      document_ids: [uploadedDoc.id]  // 关键：传递文档ID
    };
    
    console.log('📤 发送给AI的请求数据:', streamRequestData);
    
    // 使用聊天完成API
    const aiResponse = await apiService.chat.createChatCompletion(streamRequestData);
    
    testResult.aiResponse = aiResponse;
    testResult.steps.push({
      step: 'ai_chat',
      success: true,
      data: {
        responseLength: aiResponse.length,
        responsePreview: aiResponse.substring(0, 200) + '...',
        mentionsFile: aiResponse.toLowerCase().includes(file.name.toLowerCase()),
        hasFileAnalysis: aiResponse.toLowerCase().includes('文件') || 
                        aiResponse.toLowerCase().includes('文档') ||
                        aiResponse.toLowerCase().includes('内容')
      }
    });
    
    console.log('✅ AI响应:', aiResponse.substring(0, 200) + '...');

    // 步骤6: 分析结果
    const hasFileAnalysis = testResult.steps[4].data.hasFileAnalysis;
    testResult.success = hasFileAnalysis;
    
    testResult.steps.push({
      step: 'analyze_result',
      success: hasFileAnalysis,
      data: {
        conclusion: hasFileAnalysis ? 'AI成功分析了文件内容' : 'AI没有分析文件内容',
        recommendation: hasFileAnalysis ? '流程正常' : '需要检查文档内容传递机制'
      }
    });

    console.log('🎯 测试结果:', hasFileAnalysis ? '成功' : '失败');
    return testResult;

  } catch (error) {
    console.error('❌ 测试过程中出错:', error);
    testResult.error = error.message;
    testResult.steps.push({
      step: 'error',
      success: false,
      data: { error: error.message }
    });
    return testResult;
  }
};

/**
 * 格式化测试结果
 * @param {Object} result - 测试结果
 * @returns {string} 格式化的报告
 */
export const formatTestReport = (result) => {
  let report = '🧪 文件上传到AI读取流程测试报告\n\n';
  
  report += '📄 文件信息:\n';
  report += `  名称: ${result.file.name}\n`;
  report += `  大小: ${result.file.size} bytes\n`;
  report += `  类型: ${result.file.type}\n\n`;
  
  report += '📋 测试步骤:\n';
  result.steps.forEach((step, index) => {
    const status = step.success ? '✅' : '❌';
    report += `  ${index + 1}. ${step.step}: ${status}\n`;
    
    if (step.data) {
      Object.entries(step.data).forEach(([key, value]) => {
        report += `     ${key}: ${value}\n`;
      });
    }
    report += '\n';
  });
  
  report += '🎯 最终结果:\n';
  report += `  状态: ${result.success ? '✅ 成功' : '❌ 失败'}\n`;
  if (result.error) {
    report += `  错误: ${result.error}\n`;
  }
  
  if (result.documentContent) {
    report += `  文档内容长度: ${result.documentContent.length} 字符\n`;
  }
  
  if (result.aiResponse) {
    report += `  AI响应长度: ${result.aiResponse.length} 字符\n`;
    report += `  AI响应预览: ${result.aiResponse.substring(0, 100)}...\n`;
  }
  
  return report;
};

/**
 * 快速测试并显示结果
 * @param {File} file - 要测试的文件
 */
export const quickTestFileToAI = async (file) => {
  try {
    const result = await testFileToAIFlow(file);
    const report = formatTestReport(result);
    
    console.log(report);
    alert(report);
    
    return result;
  } catch (error) {
    const errorMessage = `测试失败: ${error.message}`;
    console.error(errorMessage, error);
    alert(errorMessage);
    throw error;
  }
}; 