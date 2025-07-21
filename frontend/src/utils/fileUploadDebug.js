// 文件上传和AI读取调试工具
// src/utils/fileUploadDebug.js

import apiService from '../services/apiService';

/**
 * 测试文件上传和AI读取流程
 * @param {File} file - 要测试的文件
 * @param {number} spaceId - 空间ID 
 * @returns {Promise<Object>} 测试结果
 */
export const testFileUploadAndAIReading = async (file, spaceId = null) => {
  console.log('🧪 开始文件上传和AI读取测试...');
  console.log('📄 文件信息:', {
    name: file.name,
    size: file.size,
    type: file.type
  });

  const testResult = {
    success: false,
    steps: [],
    documentId: null,
    documentContent: null,
    aiResponse: null,
    error: null
  };

  try {
    // 步骤1: 确定空间ID
    let targetSpaceId = spaceId;
    if (!targetSpaceId) {
      console.log('📁 创建临时空间...');
      const tempSpace = await apiService.space.createSpace({
        name: `文件测试空间 - ${new Date().toLocaleTimeString()}`,
        description: '文件上传测试专用空间',
        is_public: false,
        tags: ['test', 'file-upload']
      });
      targetSpaceId = tempSpace.id;
      testResult.steps.push({
        step: 'create_space',
        success: true,
        data: { spaceId: targetSpaceId }
      });
      console.log('✅ 临时空间创建成功:', targetSpaceId);
    } else {
      testResult.steps.push({
        step: 'use_existing_space',
        success: true,
        data: { spaceId: targetSpaceId }
      });
    }

    // 步骤2: 上传文件
    console.log('⬆️ 上传文件到空间:', targetSpaceId);
    const uploadedDoc = await apiService.document.uploadDocument(
      targetSpaceId,
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
        contentType: uploadedDoc.content_type,
        size: uploadedDoc.file_size
      }
    });
    console.log('✅ 文件上传成功:', uploadedDoc);

    // 步骤3: 获取文档内容
    console.log('📖 获取文档内容...');
    const documentContent = await apiService.document.getDocumentContent(uploadedDoc.id);
    testResult.documentContent = documentContent;
    testResult.steps.push({
      step: 'get_content',
      success: true,
      data: {
        contentLength: documentContent.content?.length || 0,
        hasContent: !!documentContent.content
      }
    });
    console.log('✅ 文档内容获取成功:', {
      contentLength: documentContent.content?.length || 0,
      preview: documentContent.content?.substring(0, 100) + '...'
    });

    // 步骤4: 创建对话测试AI读取
    console.log('💬 创建测试对话...');
    const conversation = await apiService.chat.createConversation({
      title: `文件读取测试 - ${file.name}`,
      mode: 'chat',
      space_id: targetSpaceId  // 确保对话和文件在同一个空间
    });

    testResult.steps.push({
      step: 'create_conversation',
      success: true,
      data: { conversationId: conversation.id }
    });
    console.log('✅ 对话创建成功:', conversation.id);

    // 步骤5: 测试AI是否能读取文件内容
    console.log('🤖 测试AI读取文件...');
    const requestData = {
      model: 'openrouter/auto',
      messages: [
        { 
          role: 'user', 
          content: `请总结这个文件的内容：${file.name}。如果你能看到文件内容，请详细描述其中包含的信息。如果看不到，请明确说明。` 
        }
      ],
      temperature: 0.7,
      stream: false,
      conversation_id: conversation.id,
      document_ids: [uploadedDoc.id]
    };
    
    console.log('AI请求参数:', requestData);
    const streamResponse = await apiService.chat.createStreamingChatCompletion(requestData);

    // 读取AI响应
    let aiResponse = '';
    if (streamResponse.body) {
      const reader = streamResponse.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') break;
            if (data === '' || data === 'null') continue;

            try {
              const chunk = JSON.parse(data);
              const content = chunk.choices?.[0]?.delta?.content;
              if (content) aiResponse += content;
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }
    } else {
      // 非流式响应
      const response = await streamResponse.json();
      aiResponse = response.choices?.[0]?.message?.content || '';
    }

    testResult.aiResponse = aiResponse;
    testResult.steps.push({
      step: 'ai_reading_test',
      success: true,
      data: {
        responseLength: aiResponse.length,
        containsFileInfo: aiResponse.toLowerCase().includes(file.name.toLowerCase()),
        responsePreview: aiResponse.substring(0, 200) + '...'
      }
    });

    // 分析AI响应
    const canReadFile = aiResponse.toLowerCase().includes('文件') || 
                       aiResponse.toLowerCase().includes('内容') ||
                       aiResponse.toLowerCase().includes(file.name.toLowerCase()) ||
                       aiResponse.length > 50; // 有实质性回复

    testResult.success = canReadFile;
    
    console.log('🎯 AI读取测试结果:', {
      canReadFile,
      responseLength: aiResponse.length,
      response: aiResponse
    });

    // 生成测试报告
    const report = generateTestReport(testResult, file);
    console.log('📊 测试报告:', report);

    return {
      ...testResult,
      report,
      recommendations: generateRecommendations(testResult)
    };

  } catch (error) {
    console.error('❌ 测试失败:', error);
    testResult.error = error.message;
    testResult.steps.push({
      step: 'error',
      success: false,
      data: { error: error.message }
    });

    return {
      ...testResult,
      report: `测试失败: ${error.message}`,
      recommendations: ['检查网络连接', '验证API配置', '确认文件格式支持']
    };
  }
};

/**
 * 生成测试报告
 */
function generateTestReport(testResult, file) {
  const { success, steps, documentContent, aiResponse } = testResult;
  
  let report = `📋 文件读取测试报告\n\n`;
  report += `📄 文件: ${file.name} (${(file.size / 1024).toFixed(1)} KB)\n`;
  report += `🎯 整体结果: ${success ? '✅ 成功' : '❌ 失败'}\n\n`;
  
  report += `📝 执行步骤:\n`;
  steps.forEach((step, index) => {
    const status = step.success ? '✅' : '❌';
    report += `${index + 1}. ${status} ${step.step}\n`;
  });
  
  if (documentContent) {
    report += `\n📖 文档内容: ${documentContent.content ? '有内容' : '无内容'}\n`;
    if (documentContent.content) {
      report += `   长度: ${documentContent.content.length} 字符\n`;
    }
  }
  
  if (aiResponse) {
    report += `\n🤖 AI响应: ${aiResponse.length} 字符\n`;
    report += `   预览: ${aiResponse.substring(0, 100)}...\n`;
  }
  
  return report;
}

/**
 * 生成改进建议
 */
function generateRecommendations(testResult) {
  const recommendations = [];
  
  if (!testResult.success) {
    recommendations.push('检查文件是否成功上传到正确的空间');
    recommendations.push('验证文档内容是否被正确提取');
    recommendations.push('确认document_ids参数是否正确传递给AI');
  }
  
  if (testResult.documentContent && !testResult.documentContent.content) {
    recommendations.push('文档内容为空，检查文件格式是否支持');
    recommendations.push('尝试使用其他文件格式（如txt, md）');
  }
  
  if (testResult.aiResponse && testResult.aiResponse.length < 50) {
    recommendations.push('AI响应过短，可能未读取到文件内容');
    recommendations.push('检查后端文档上下文处理逻辑');
  }
  
  if (testResult.success) {
    recommendations.push('✅ 文件读取功能正常工作');
    recommendations.push('可以继续使用此功能');
  }
  
  return recommendations;
}

/**
 * 快速测试当前聊天中的文件
 */
export const quickTestCurrentFiles = async () => {
  console.log('🚀 快速测试当前聊天文件...');
  
  // 创建一个简单的测试文件
  const testContent = `测试文档内容
这是一个用于测试AI读取功能的文档。

主要内容：
1. 这是第一项内容
2. 这是第二项内容  
3. 这包含一些中文文字用于测试

如果AI能够读取到这些内容，说明文件读取功能工作正常。

创建时间: ${new Date().toLocaleString()}`;

  const testFile = new File([testContent], 'ai-reading-test.txt', { type: 'text/plain' });
  
  return await testFileUploadAndAIReading(testFile);
}; 