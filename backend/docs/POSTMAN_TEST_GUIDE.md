# Second Brain API Postman测试指南

## 前置准备

### 1. 安装和启动系统
```bash
# 确保Docker服务已启动
docker-compose up -d

# 检查服务状态
docker-compose ps

# 查看后端日志
docker-compose logs -f backend
```

### 2. 创建演示数据
```bash
# 创建演示用户和数据
docker-compose exec backend uv run python tools/demo_data.py create
```
演示账号信息：
- 用户名：`demo_user`
- 密码：`Demo123456!`

### 3. 安装Postman
- 下载地址：https://www.postman.com/downloads/
- 或使用Web版本：https://web.postman.co/

## 导入测试集合

### 方法1：导入JSON文件
1. 打开Postman
2. 点击左上角 "Import" 按钮
3. 选择 `SecondBrain_Postman_Collection.json` 文件
4. 点击 "Import"

### 方法2：手动创建
1. 创建新的Collection
2. 设置Collection变量：
   - `base_url`: `http://localhost:8000/api/v1`
   - `access_token`: （登录后自动填充）
   - `refresh_token`: （登录后自动填充）
   - `space_id`: （创建空间后自动填充）
   - `note_id`: （创建笔记后自动填充）
   - `conversation_id`: （创建对话后自动填充）

## 测试流程

### 步骤1：基础连接测试
1. 运行 "健康检查" 请求
2. 应返回 200 状态码和系统状态信息

### 步骤2：认证流程测试
1. **用户登录**
   - 运行 "用户登录" 请求
   - 使用演示账号：demo_user / Demo123456!
   - 成功后会自动保存token到环境变量

2. **验证认证**
   - 运行 "获取当前用户信息"
   - 应返回用户详细信息

### 步骤3：核心功能测试

#### 3.1 空间管理
```
执行顺序：
1. 创建空间 → 自动保存space_id
2. 获取空间列表
3. 获取空间详情
4. 更新空间
```

#### 3.2 笔记管理
```
执行顺序：
1. 创建笔记 → 自动保存note_id
2. 获取笔记列表
3. 搜索笔记
4. 更新笔记
5. 获取笔记版本历史
```

#### 3.3 AI对话
```
执行顺序：
1. 创建对话 → 自动保存conversation_id
2. 发送消息（多次测试不同问题）
3. 获取对话列表
```

#### 3.4 深度研究
```
直接执行：
- 执行深度研究（注意：需要配置API Key）
```

#### 3.5 导出功能
```
执行顺序：
1. 导出空间（PDF格式）
2. 导出笔记（PDF格式）
3. 导出对话（Markdown格式）
```

## 常见测试场景

### 场景1：完整用户流程
1. 健康检查
2. 用户登录
3. 创建空间
4. 创建多个笔记
5. 搜索笔记
6. 创建AI对话
7. 导出内容

### 场景2：认证过期处理
1. 登录获取token
2. 等待token过期（默认1小时）
3. 使用刷新token获取新token
4. 继续使用新token访问API

### 场景3：错误处理测试
1. 使用错误的token访问API（应返回401）
2. 访问不存在的资源（应返回404）
3. 提交格式错误的数据（应返回422）

## 高级测试技巧

### 1. 使用环境变量
创建不同的环境配置：
- Development: `http://localhost:8000/api/v1`
- Production: `https://your-domain.com/api/v1`

### 2. 自动化测试脚本
在Tests标签页添加JavaScript代码：
```javascript
// 检查状态码
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// 检查响应时间
pm.test("Response time is less than 1000ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(1000);
});

// 验证响应格式
pm.test("Response has required fields", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
    pm.expect(jsonData).to.have.property('title');
});
```

### 3. 批量测试
使用Postman的Collection Runner：
1. 点击Collection旁边的"Run"按钮
2. 选择要运行的请求
3. 设置迭代次数和延迟
4. 点击"Run Collection"

### 4. 性能测试
监控每个请求的：
- 响应时间
- 响应大小
- 状态码分布

## 调试技巧

### 1. 查看详细日志
```bash
# 实时查看后端日志
docker-compose logs -f backend

# 查看数据库日志
docker-compose logs -f postgres
```

### 2. 使用Postman Console
- 按 `Ctrl+Alt+C` (Windows/Linux) 或 `Cmd+Alt+C` (Mac)
- 查看完整的请求和响应详情

### 3. 常见问题排查

#### 问题：401 Unauthorized
- 检查token是否过期
- 确认Authorization header格式正确
- 重新登录获取新token

#### 问题：连接被拒绝
- 确认Docker容器正在运行
- 检查端口8000是否被占用
- 确认防火墙设置

#### 问题：500 Internal Server Error
- 查看后端日志了解具体错误
- 检查请求数据格式是否正确
- 确认所有依赖服务正常运行

## 完整测试清单

- [ ] 健康检查端点可访问
- [ ] 用户注册功能正常
- [ ] 用户登录并获取token
- [ ] Token认证机制正常
- [ ] 创建/读取/更新/删除空间
- [ ] 创建/读取/更新/删除笔记
- [ ] 笔记搜索功能正常
- [ ] AI对话功能正常
- [ ] 消息发送和接收正常
- [ ] 文档上传功能（如实现）
- [ ] 深度研究功能（需要API Key）
- [ ] 导出PDF功能正常
- [ ] 导出Markdown功能正常
- [ ] 错误处理机制正常
- [ ] 分页功能正常
- [ ] 权限控制正常

## 导出测试报告

1. 运行完整测试后，点击"View Results"
2. 点击"Export Results"
3. 选择导出格式（JSON/HTML）
4. 保存测试报告

## 与前端集成

前端开发者可以：
1. 使用相同的Postman集合了解API
2. 查看请求/响应格式
3. 复制请求代码（Postman可生成各种语言的代码）
4. 基于测试结果调整前端实现

## 下一步

1. 完成所有API测试
2. 记录发现的问题
3. 与前端开发者分享测试结果
4. 根据反馈优化API设计