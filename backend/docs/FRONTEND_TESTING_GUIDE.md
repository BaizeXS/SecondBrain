# 前后端联调测试指南

本指南帮助前端开发者在本地测试 SecondBrain 的所有功能。

## 🚀 快速开始

### 1. 确保后端服务运行

```bash
# 在 backend 目录下
docker-compose ps

# 如果服务未运行，启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

### 2. 验证后端状态

```bash
# 健康检查
curl http://localhost:8000/health

# API 文档
open http://localhost:8000/api/v1/docs
```

## 🧪 测试方法

### 方法 1：使用 Web 测试界面（推荐）

```bash
# 启动增强版 Web 测试界面
uv run python tools/web_test_server.py --enhanced

# 访问 http://localhost:8080
```

**特点：**
- 可视化测试所有 API
- 演示账号自动填充
- 实时查看请求/响应
- 支持文件上传测试
- 性能监控图表

### 方法 2：使用集成测试脚本

```bash
# 运行完整功能测试
uv run python tools/integration_test.py
```

**测试内容：**
- 用户注册/登录
- AI 对话（Chat 和 Search 模式）
- 空间管理
- 文档上传和搜索
- 笔记创建和管理
- Deep Research 功能

### 方法 3：使用 API 文档

访问 http://localhost:8000/api/v1/docs

- Swagger UI 界面
- 可以直接测试每个端点
- 查看请求/响应格式

## 📱 前端连接配置

### 环境变量设置

```javascript
// .env.local 或 .env.development
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

### CORS 配置

后端已配置 CORS，允许以下来源：
- http://localhost:3000
- http://localhost:5173

如需其他端口，修改 `backend/.env`：
```
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:你的端口
```

## 🔑 测试账号

### 演示账号（推荐）
- 用户名：`demo_user`
- 密码：`Demo123456!`
- 特点：已有示例数据

### 创建新账号
使用 Web 测试界面或 API 文档注册新用户

## ✅ 功能测试清单

### 1. 认证功能
- [ ] 用户注册
- [ ] 用户登录（表单/JSON）
- [ ] Token 刷新
- [ ] 修改密码
- [ ] 登出

### 2. AI 对话
- [ ] 创建对话
- [ ] 发送消息（同步）
- [ ] 流式对话（SSE）
- [ ] Chat 模式
- [ ] Search 模式（需配置 Perplexity）
- [ ] 对话历史
- [ ] 消息分支

### 3. 知识管理
- [ ] 创建空间
- [ ] 上传文档（PDF、Word、图片等）
- [ ] 文档搜索
- [ ] 创建笔记
- [ ] 笔记搜索
- [ ] AI 生成笔记

### 4. 高级功能
- [ ] Deep Research（深度研究）
- [ ] 文档导出（PDF/DOCX）
- [ ] 批量操作
- [ ] 标注功能

## 🛠️ 常见问题

### 1. 连接被拒绝
```bash
# 检查后端服务
docker-compose ps
docker-compose restart backend
```

### 2. CORS 错误
- 检查前端请求的 URL
- 确认 `.env` 中的 ALLOWED_ORIGINS
- 重启后端服务

### 3. 认证失败
- 检查 Token 是否正确传递
- Headers: `Authorization: Bearer <token>`
- Token 有效期：30 分钟

### 4. WebSocket 连接失败
- 确保使用正确的 WS URL
- 检查防火墙设置

## 📊 性能测试

```bash
# 运行性能测试
uv run python tools/performance_test_suite.py
```

测试项目：
- API 响应时间
- 并发请求处理
- 文件上传速度
- AI 模型响应时间

## 🔍 调试技巧

### 1. 查看后端日志
```bash
docker-compose logs -f backend
```

### 2. 数据库状态
```bash
uv run python tools/database_cleaner.py --stats
```

### 3. 清理测试数据
```bash
# 保留演示数据
uv run python tools/database_cleaner.py

# 重置演示数据
uv run python tools/database_cleaner.py --reset-demo
```

### 4. 网络请求调试
使用浏览器开发者工具：
- Network 标签查看请求
- Console 查看错误信息
- 检查请求头和响应

## 📝 API 响应格式

### 成功响应
```json
{
  "id": 1,
  "data": "...",
  "message": "Success"
}
```

### 错误响应
```json
{
  "detail": "错误信息",
  "status_code": 400,
  "timestamp": 12345.67,
  "path": "/api/v1/endpoint"
}
```

### 分页响应
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_prev": false
}
```

## 🚀 部署前检查

1. **API 测试通过率**
   ```bash
   uv run python tools/api_test_suite.py
   ```
   目标：>95% 通过率

2. **集成测试通过**
   ```bash
   uv run python tools/integration_test.py
   ```

3. **性能指标达标**
   - API 响应时间 <500ms
   - 并发支持 >100 请求/秒

4. **演示数据准备**
   ```bash
   uv run python tools/demo_data_creator.py
   ```

## 💡 提示

1. **AI 功能测试**
   - 需要配置 OPENROUTER_API_KEY
   - 免费额度可能有限制
   - 可使用 Ollama 本地模型测试

2. **文件上传测试**
   - 支持格式：PDF, DOCX, TXT, MD, 图片
   - 最大文件：100MB
   - 测试文件在 `tools/test_files/`

3. **实时功能测试**
   - 流式对话使用 SSE
   - 确保前端正确处理流式响应
   - 注意连接超时设置

## 📞 需要帮助？

- 查看 API 文档：http://localhost:8000/api/v1/docs
- 查看后端日志：`docker-compose logs -f backend`
- 运行诊断：`uv run python tools/api_test_suite.py`

---

祝测试顺利！🎉