# Second Brain 快速启动

## 启动步骤

### 1. 配置API密钥
```bash
cd backend
cp .env.example .env
# 编辑 .env，添加 OPENROUTER_API_KEY=sk-or-xxx
```

### 2. 启动服务
```bash
# 在项目根目录
docker-compose up -d
```

### 3. 初始化数据库（仅首次）
```bash
# 等待10秒让数据库启动
sleep 10

# 运行数据库迁移
docker-compose exec backend uv run alembic upgrade head

# 创建演示数据（可选）
docker-compose exec backend uv run python tools/demo_data.py create
```

## 访问地址
- 前端：http://localhost
- API文档：http://localhost:8000/api/v1/docs
- 测试账号：demo_user / Demo123456!

## 测试系统

### 测试API是否正常
```bash
# 运行完整的API测试
docker-compose exec backend uv run python tools/test_api.py
```

### 清除演示数据
```bash
# 仅清除演示数据（保留其他数据）
docker-compose exec backend uv run python tools/demo_data.py clean
```

## 完全重置
```bash
# 停止并删除所有容器和数据
docker-compose down -v
```