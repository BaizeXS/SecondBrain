// 前端调试脚本 - 在浏览器控制台运行

// 检查 localStorage 中的认证信息
console.log('=== 认证信息 ===');
console.log('Access Token:', localStorage.getItem('access_token') ? '存在' : '不存在');
console.log('Refresh Token:', localStorage.getItem('refresh_token') ? '存在' : '不存在');
console.log('User:', localStorage.getItem('user'));

// 测试 API 连接
async function testAPIConnection() {
  console.log('\n=== 测试 API 连接 ===');
  
  try {
    // 测试健康检查
    const healthResponse = await fetch('http://localhost:8000/api/v1/health');
    console.log('健康检查:', healthResponse.ok ? '✅ 正常' : '❌ 失败');
    
    // 测试获取 agents
    const token = localStorage.getItem('access_token');
    if (token) {
      const agentsResponse = await fetch('http://localhost:8000/api/v1/agents/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const agentsData = await agentsResponse.json();
      console.log('Agents API:', agentsResponse.ok ? '✅ 正常' : '❌ 失败');
      console.log('Agents 数量:', agentsData.items ? agentsData.items.length : 0);
      if (agentsData.items) {
        console.log('Agents 列表:');
        agentsData.items.forEach(agent => {
          console.log(`  - ${agent.name} (${agent.agent_type}) ID: ${agent.id}`);
        });
      }
    } else {
      console.log('❌ 没有 token，无法测试认证 API');
    }
  } catch (error) {
    console.error('API 测试失败:', error);
  }
}

// 检查 React Context
console.log('\n=== React Context 检查 ===');
console.log('提示: 在 React DevTools 中查看 AgentContext 的值');

// 运行测试
testAPIConnection();