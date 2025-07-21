// 流式输出测试工具
// src/utils/streamingTestUtils.js

import { chatAPI } from '../services/apiService';

/**
 * 测试流式连接的完整功能
 * @param {Object} options 测试选项
 * @returns {Promise<Object>} 测试结果
 */
export const testStreamingConnection = async (options = {}) => {
  const {
    model = 'openrouter/auto',
    message = 'Hello, this is a streaming test. Please respond with a brief greeting.',
    timeout = 30000,
    verbose = false
  } = options;

  console.log('🧪 开始流式输出测试...');
  
  const startTime = Date.now();
  let totalChunks = 0;
  let totalContent = '';
  let firstChunkTime = null;
  let lastChunkTime = null;

  try {
    const response = await chatAPI.createStreamingChatCompletion({
      model,
      messages: [
        { role: 'user', content: message }
      ],
      temperature: 0.7,
      max_tokens: 100,
    });

    if (verbose) {
      console.log('✅ 响应接收成功');
      console.log('📋 Response headers:', [...response.headers.entries()]);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('测试超时')), timeout);
    });

    const readingPromise = (async () => {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        if (!firstChunkTime) {
          firstChunkTime = Date.now();
        }
        lastChunkTime = Date.now();
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            
            if (data === '[DONE]') {
              if (verbose) console.log('✅ 接收到结束标记');
              return;
            }
            
            if (data === '' || data === 'null') continue;
            
            try {
              const chunk = JSON.parse(data);
              const content = chunk.choices?.[0]?.delta?.content;
              if (content) {
                totalContent += content;
                totalChunks++;
                if (verbose) console.log(`📝 块 ${totalChunks}: "${content}"`);
              }
            } catch (parseError) {
              console.warn('⚠️ 解析块失败:', data);
            }
          }
        }
      }
    })();

    await Promise.race([readingPromise, timeoutPromise]);

    const endTime = Date.now();
    const totalTime = endTime - startTime;
    const timeToFirstChunk = firstChunkTime ? firstChunkTime - startTime : 0;

    const result = {
      success: true,
      content: totalContent,
      metrics: {
        totalTime,
        timeToFirstChunk,
        totalChunks,
        avgChunkTime: totalChunks > 0 ? totalTime / totalChunks : 0,
        contentLength: totalContent.length,
        chunksPerSecond: totalChunks / (totalTime / 1000)
      }
    };

    console.log('✅ 流式输出测试成功!');
    console.log('📊 测试结果:', result.metrics);
    console.log('💬 生成内容:', totalContent);

    return result;

  } catch (error) {
    console.error('❌ 流式输出测试失败:', error);
    return {
      success: false,
      error: error.message,
      metrics: {
        totalTime: Date.now() - startTime,
        totalChunks,
        contentLength: totalContent.length
      }
    };
  }
};

/**
 * 运行多个流式测试
 * @param {number} count 测试次数
 * @param {Object} options 测试选项
 * @returns {Promise<Object>} 聚合测试结果
 */
export const runMultipleStreamTests = async (count = 3, options = {}) => {
  console.log(`🔄 运行 ${count} 次流式测试...`);
  
  const results = [];
  
  for (let i = 0; i < count; i++) {
    console.log(`\n--- 测试 ${i + 1}/${count} ---`);
    const result = await testStreamingConnection({
      ...options,
      verbose: false
    });
    results.push(result);
    
    // 测试间隔
    if (i < count - 1) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  const successCount = results.filter(r => r.success).length;
  const failureCount = count - successCount;
  
  const successfulResults = results.filter(r => r.success);
  const avgMetrics = successfulResults.length > 0 ? {
    avgTotalTime: successfulResults.reduce((sum, r) => sum + r.metrics.totalTime, 0) / successfulResults.length,
    avgTimeToFirstChunk: successfulResults.reduce((sum, r) => sum + r.metrics.timeToFirstChunk, 0) / successfulResults.length,
    avgTotalChunks: successfulResults.reduce((sum, r) => sum + r.metrics.totalChunks, 0) / successfulResults.length,
    avgContentLength: successfulResults.reduce((sum, r) => sum + r.metrics.contentLength, 0) / successfulResults.length,
  } : {};

  const summary = {
    totalTests: count,
    successCount,
    failureCount,
    successRate: (successCount / count) * 100,
    avgMetrics,
    allResults: results
  };

  console.log('\n🎯 聚合测试结果:');
  console.log(`✅ 成功: ${successCount}/${count} (${summary.successRate.toFixed(1)}%)`);
  console.log(`❌ 失败: ${failureCount}/${count}`);
  
  if (successfulResults.length > 0) {
    console.log('📈 平均指标:', avgMetrics);
  }

  return summary;
};

/**
 * 检查流式输出配置
 * @returns {Object} 配置检查结果
 */
export const checkStreamingConfiguration = () => {
  const checks = {
    apiBaseUrl: !!process.env.REACT_APP_API_URL,
    authToken: !!localStorage.getItem('access_token'),
    fetchSupport: typeof fetch !== 'undefined',
    readableStreamSupport: typeof ReadableStream !== 'undefined',
    textDecoderSupport: typeof TextDecoder !== 'undefined'
  };

  const allChecks = Object.values(checks).every(Boolean);

  console.log('🔍 流式输出配置检查:');
  Object.entries(checks).forEach(([key, value]) => {
    console.log(`${value ? '✅' : '❌'} ${key}: ${value}`);
  });

  return {
    allChecksPass: allChecks,
    checks
  };
};

/**
 * 创建流式输出性能监控器
 * @param {Function} onUpdate 更新回调
 * @returns {Object} 监控器对象
 */
export const createStreamingMonitor = (onUpdate) => {
  let startTime = null;
  let chunkCount = 0;
  let totalContent = '';
  let firstChunkTime = null;

  return {
    start() {
      startTime = Date.now();
      chunkCount = 0;
      totalContent = '';
      firstChunkTime = null;
    },

    onChunk(content) {
      if (!firstChunkTime) {
        firstChunkTime = Date.now();
      }
      
      chunkCount++;
      totalContent += content;
      
      const now = Date.now();
      const metrics = {
        elapsed: now - startTime,
        timeToFirstChunk: firstChunkTime - startTime,
        chunkCount,
        contentLength: totalContent.length,
        chunksPerSecond: chunkCount / ((now - startTime) / 1000)
      };

      if (onUpdate) {
        onUpdate(metrics);
      }

      return metrics;
    },

    finish() {
      const endTime = Date.now();
      return {
        totalTime: endTime - startTime,
        timeToFirstChunk: firstChunkTime ? firstChunkTime - startTime : 0,
        totalChunks: chunkCount,
        contentLength: totalContent.length,
        avgChunkTime: chunkCount > 0 ? (endTime - startTime) / chunkCount : 0
      };
    }
  };
}; 