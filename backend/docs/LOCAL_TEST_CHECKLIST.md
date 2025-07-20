# 本地部署测试清单

在正式部署之前，请按以下步骤进行本地测试：

## 1. 环境准备检查

### 必需软件
- [ ] Docker Desktop 已安装并运行
- [ ] Docker Compose 可用 (docker-compose 或 docker compose)
- [ ] Git 已安装
- [ ] 有可用的文本编辑器

### API Keys 配置
- [ ] 至少配置一个 AI 服务的 API Key：
  - [ ] OPENROUTER_API_KEY (推荐，支持多模型)
  - [ ] OPENAI_API_KEY
  - [ ] ANTHROPIC_API_KEY
  - [ ] GOOGLE_API_KEY
  - [ ] DEEPSEEK_API_KEY

## 2. 基础测试步骤

### 步骤 1: 设置权限并运行测试脚本
```bash
cd backend
chmod +x deploy_test_local.sh
./deploy_test_local.sh
```

### 步骤 2: 检查服务状态
所有服务应该显示为"运行中"：
- [ ] PostgreSQL ✓ 运行中
- [ ] Redis ✓ 运行中
- [ ] MinIO ✓ 运行中
- [ ] Qdrant ✓ 运行中
- [ ] 后端服务 ✓ 运行中

### 步骤 3: 验证 API 端点
- [ ] 健康检查返回 200
- [ ] API 文档可访问
- [ ] 登录测试成功
- [ ] 获取访问令牌成功

## 3. 功能测试

### 基础功能测试
1. **访问 API 文档**
   - 打开 http://localhost:8000/api/v1/docs
   - [ ] 页面正常显示
   - [ ] 可以看到所有 API 端点

2. **测试用户认证**
   - 使用测试账号登录
   - [ ] 登录成功
   - [ ] 获得有效的访问令牌

3. **测试 AI 对话**
   ```bash
   # 使用 tools/test_chat.py 进行测试
   cd tools
   python test_chat.py
   ```
   - [ ] AI 对话功能正常

4. **测试文件上传**
   - 访问 http://localhost:8080/simple_api_test.html
   - [ ] 可以上传文件
   - [ ] 文件处理成功

### 高级功能测试
1. **Space 功能**
   - [ ] 创建 Space
   - [ ] 列出 Spaces
   - [ ] 删除 Space

2. **笔记功能**
   - [ ] 创建笔记
   - [ ] 更新笔记
   - [ ] 删除笔记

3. **Deep Research**（如果配置了 OpenRouter）
   - [ ] 执行深度研究
   - [ ] 结果保存成功

## 4. 性能和稳定性测试

### 资源使用检查
```bash
docker stats
```
- [ ] CPU 使用率正常（< 80%）
- [ ] 内存使用合理（< 2GB）
- [ ] 无内存泄漏迹象

### 日志检查
```bash
docker-compose logs -f backend
```
- [ ] 无错误日志
- [ ] 无异常警告
- [ ] API 响应时间正常

## 5. 前端集成测试

如果有前端项目：

1. **修改前端配置**
   ```javascript
   // 修改 API 地址为本地后端
   const API_BASE_URL = 'http://localhost:8000/api/v1'
   ```

2. **测试前端连接**
   - [ ] 前端可以连接后端
   - [ ] CORS 配置正确
   - [ ] API 调用成功

## 6. 部署前最终检查

### 配置检查
- [ ] .env 文件中的 SECRET_KEY 已更新
- [ ] 数据库密码已更改（如需要）
- [ ] API Keys 正确配置

### 安全检查
- [ ] 没有敏感信息提交到代码库
- [ ] .gitignore 包含所有必要文件
- [ ] 生产环境配置与开发分离

### 数据准备
- [ ] 数据库迁移成功
- [ ] 必要的初始数据已创建
- [ ] 演示账号可用

## 7. 故障排除

### 常见问题

1. **Docker 服务无法启动**
   ```bash
   # 检查 Docker 是否运行
   docker info
   
   # 清理并重启
   docker-compose down -v
   docker-compose up -d
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库容器
   docker-compose logs postgres
   
   # 手动连接测试
   docker-compose exec postgres psql -U secondbrain -d secondbrain
   ```

3. **后端服务启动失败**
   ```bash
   # 查看详细日志
   docker-compose logs --tail=100 backend
   
   # 检查依赖安装
   docker-compose exec backend uv pip list
   ```

4. **API 调用失败**
   - 检查 CORS 配置
   - 验证 API Key 设置
   - 查看网络请求详情

## 8. 完整部署

本地测试通过后：

1. **运行完整部署脚本**
   ```bash
   ./deploy.sh
   ```

2. **使用 docker-compose.full.yml**
   ```bash
   # 包含前后端的完整部署
   docker-compose -f docker-compose.full.yml up -d
   ```

3. **验证部署结果**
   - [ ] 所有服务正常运行
   - [ ] 可以通过浏览器访问
   - [ ] 功能测试全部通过

## 9. 测试记录

记录测试结果：

| 测试项目 | 状态 | 备注 |
|---------|------|------|
| Docker 环境 | ✓ | |
| 服务启动 | ✓ | |
| API 健康检查 | ✓ | |
| 用户认证 | ✓ | |
| AI 对话 | ✓ | |
| 文件上传 | ✓ | |
| 前端集成 | - | |
| 性能测试 | - | |

测试日期：__________
测试人员：__________

## 10. 部署建议

基于测试结果：

1. **最小部署**（推荐用于毕业设计）
   - 使用 docker-compose.yml
   - 单机部署
   - SQLite 或 PostgreSQL

2. **标准部署**
   - 使用 docker-compose.full.yml
   - 包含所有服务
   - 适合演示和测试

3. **生产部署**
   - 使用云服务
   - 配置负载均衡
   - 启用 HTTPS