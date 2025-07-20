// 测试认证功能的简单脚本
// 在浏览器控制台运行这些函数来测试

// 测试登录
async function testLogin() {
  try {
    const response = await fetch('http://localhost:8000/api/v1/auth/login/json', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'test@example.com',
        password: 'testpassword'
      })
    });
    
    const data = await response.json();
    console.log('Login response:', data);
    
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      console.log('Login successful! Tokens saved.');
    }
  } catch (error) {
    console.error('Login failed:', error);
  }
}

// 测试获取当前用户
async function testGetCurrentUser() {
  const token = localStorage.getItem('access_token');
  if (!token) {
    console.error('No access token found. Please login first.');
    return;
  }
  
  try {
    const response = await fetch('http://localhost:8000/api/v1/users/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    const data = await response.json();
    console.log('Current user:', data);
  } catch (error) {
    console.error('Failed to get current user:', error);
  }
}

// 测试注册
async function testRegister() {
  try {
    const response = await fetch('http://localhost:8000/api/v1/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'newuser@example.com',
        email: 'newuser@example.com',
        password: 'newpassword123',
        full_name: 'New User'
      })
    });
    
    const data = await response.json();
    console.log('Register response:', data);
  } catch (error) {
    console.error('Registration failed:', error);
  }
}

console.log('认证测试函数已加载。使用以下命令测试：');
console.log('- testRegister() - 测试注册新用户');
console.log('- testLogin() - 测试登录');
console.log('- testGetCurrentUser() - 测试获取当前用户信息');