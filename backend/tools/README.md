# Backend 工具说明

本目录包含用于管理 Second Brain 后端的工具脚本。

## 可用工具

### 1. demo_data.py - 演示数据管理
创建或清除演示数据，包括用户、空间、笔记和对话。

```bash
# 创建演示数据
docker-compose exec backend uv run python tools/demo_data.py create

# 清除演示数据
docker-compose exec backend uv run python tools/demo_data.py clean
```

**演示账号信息：**
- 用户名：demo_user
- 密码：Demo123456!

### 2. test_api.py - API 测试工具
测试所有已实现的 API 端点，确保系统正常运行。

```bash
# 运行 API 测试
docker-compose exec backend uv run python tools/test_api.py
```

测试结果会保存到 `api_test_results.json` 文件。

## 注意事项

### bcrypt 警告
运行脚本时可能会看到以下警告：
```
(trapped) error reading bcrypt version
```

这是由于 bcrypt 库版本兼容性问题，不影响功能正常使用。如需解决，可以：

1. 更新 bcrypt 版本：
   ```bash
   docker-compose exec backend uv add bcrypt --upgrade
   ```

2. 或者忽略此警告，因为密码哈希功能仍然正常工作。

### 数据库连接
确保在运行这些工具之前：
1. Docker 容器正在运行
2. 数据库已经初始化（运行过迁移）
3. 必要的环境变量已配置

## 开发说明

所有工具脚本都应该：
- 使用 `uv run` 运行
- 包含清晰的用法说明
- 处理常见错误情况
- 提供有用的输出信息