#!/bin/bash
# SecondBrain 一键启动脚本

echo "🚀 SecondBrain 一键启动脚本"
echo "================================"

# 1. 检查 .env 文件
if [ ! -f backend/.env ]; then
    echo "📝 创建 .env 配置文件..."
    cp backend/.env.example backend/.env
    echo "⚠️  请编辑 backend/.env 文件，添加至少一个 AI API Key"
    echo "   支持: OPENAI_API_KEY, ANTHROPIC_API_KEY, OPENROUTER_API_KEY 等"
    read -p "配置完成后按回车继续..."
fi

# 2. 创建必要的目录
echo "📁 创建必要目录..."
mkdir -p backend/data/{postgres,redis,minio,qdrant}

# 3. 停止已有容器
echo "🛑 停止已有容器..."
docker-compose down

# 4. 构建镜像
echo "🔨 构建 Docker 镜像..."
docker-compose build

# 5. 启动所有服务
echo "🚀 启动所有服务..."
docker-compose up -d

# 6. 等待服务启动
echo "⏳ 等待服务启动（30秒）..."
sleep 30

# 7. 运行数据库迁移
echo "📊 初始化数据库..."
docker-compose exec backend alembic upgrade head

# 8. 创建测试账号
echo "👤 创建测试账号..."
docker-compose exec backend python -c "
import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.models import User
from app.core.security import get_password_hash

async def create_test_user():
    async with SessionLocal() as db:
        # 检查用户是否已存在
        result = await db.execute(select(User).filter(User.email == 'test@example.com'))
        if result.scalar_one_or_none():
            print('测试用户已存在')
            return
        
        # 创建新用户
        user = User(
            username='test',
            email='test@example.com',
            hashed_password=get_password_hash('Test123!'),
            full_name='测试用户',
            is_active=True
        )
        db.add(user)
        await db.commit()
        print('✅ 测试用户创建成功')

asyncio.run(create_test_user())
"

# 9. 显示访问信息
echo ""
echo "✅ 启动完成！"
echo "================================"
echo "🌐 前端地址: http://localhost:3000"
echo "🔧 后端 API: http://localhost:8000"
echo "📚 API 文档: http://localhost:8000/docs"
echo "💾 MinIO 控制台: http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo "📧 测试账号: test@example.com"
echo "🔑 测试密码: Test123!"
echo ""
echo "📋 查看日志: docker-compose logs -f"
echo "🛑 停止服务: docker-compose down"
echo "================================"