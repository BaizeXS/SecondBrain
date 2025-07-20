# 前端集成快速检查清单

## ✅ 后端服务已就绪

### 🎯 测试工具
1. **简单测试界面**：http://localhost:8080/simple_api_test.html
2. **API 文档**：http://localhost:8000/api/v1/docs
3. **健康检查**：http://localhost:8000/health

### 🔑 测试账号
- 用户名：`demo_user`
- 密码：`Demo123456!`

## 📋 前端集成检查项

### 1. 环境配置 ✓
```javascript
// .env.local 或 .env.development
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

### 2. 认证流程 ✓
- [ ] 登录接口：`POST /auth/login` (FormData)
- [ ] Token 存储（localStorage/sessionStorage）
- [ ] 请求头添加：`Authorization: Bearer <token>`
- [ ] Token 刷新：`POST /auth/refresh`
- [ ] 登出：`POST /auth/logout`

### 3. 核心功能 ✓
- [ ] AI 对话
  - 创建对话：`POST /chat/conversations`
  - 发送消息：`POST /chat/conversations/{id}/messages`
  - 流式响应（SSE）处理
- [ ] 知识管理
  - 空间列表：`GET /spaces`
  - 文档上传：`POST /documents/upload`
  - 笔记创建：`POST /notes`
- [ ] Deep Research
  - 执行研究：`POST /agents/1/execute`

### 4. 错误处理 ✓
```javascript
// 统一错误格式
{
  "detail": "错误信息",
  "status_code": 400,
  "timestamp": 12345.67,
  "path": "/api/v1/endpoint"
}
```

### 5. 注意事项 ⚠️
1. **CORS**：已配置 localhost:3000 和 5173
2. **文件上传**：使用 FormData，最大 100MB
3. **分页参数**：`skip` 和 `limit`
4. **流式响应**：使用 EventSource 或 fetch + ReadableStream

## 🚀 快速验证步骤

1. **打开简单测试界面**
   - 访问 http://localhost:8080/simple_api_test.html
   - 点击"登录"按钮
   - 点击"运行所有测试"

2. **检查测试结果**
   - 所有核心功能应该显示"✅ 通过"
   - 如有失败，查看日志详情

3. **前端连接测试**
   ```javascript
   // 示例代码
   const response = await fetch('http://localhost:8000/api/v1/auth/login', {
     method: 'POST',
     body: new FormData(...)
   });
   const { access_token } = await response.json();
   ```

## 🛠️ 故障排除

### 问题：CORS 错误
- 检查请求 URL 是否正确
- 确认前端端口在 CORS 白名单中

### 问题：401 未授权
- 检查 Token 是否正确传递
- Token 是否过期（30分钟）

### 问题：连接被拒绝
- 确认 Docker 服务运行：`docker-compose ps`
- 检查端口 8000 是否被占用

### 问题：WebSocket 连接失败
- 使用查询参数传递 token：`ws://localhost:8000/ws?token=<token>`
- 或改用轮询方式

## 📊 系统状态

- API 测试通过率：**98.1%**
- Deep Research：**正常工作**
- 演示数据：**已创建**

---

💡 **提示**：使用简单测试界面可以快速验证所有功能是否正常工作！