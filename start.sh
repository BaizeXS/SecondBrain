#!/bin/bash
# 简单的启动脚本

echo "🚀 启动 SecondBrain 项目..."

# 停止并清理旧容器
docker-compose down

# 构建并启动所有服务
docker-compose up -d --build

# 等待数据库就绪
echo "⏳ 等待数据库启动..."
sleep 10

# 初始化数据库表
echo "📊 初始化数据库..."
docker-compose exec backend uv run python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import Base
from app.models import User, Space, Conversation, Message, Document, Agent, Note
import os

async def init_db():
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://secondbrain:secondbrain123@postgres:5432/secondbrain')
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        print('✅ 数据库表创建成功')
    
    await engine.dispose()

asyncio.run(init_db())
"

# 创建 MinIO bucket
echo "📦 创建存储桶..."
docker-compose exec backend uv run python -c "
from minio import Minio
client = Minio(
    'minio:9000',
    access_key='minioadmin',
    secret_key='minioadmin',
    secure=False
)
if not client.bucket_exists('secondbrain'):
    client.make_bucket('secondbrain')
    print('✅ 存储桶创建成功')
else:
    print('✅ 存储桶已存在')
"

echo "✅ 所有服务已启动！"
echo ""
echo "访问地址："
echo "  - 前端: http://localhost:3000"
echo "  - 后端API: http://localhost:8000"
echo "  - API文档: http://localhost:8000/api/v1/docs"
echo "  - MinIO控制台: http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo "查看日志: docker-compose logs -f"
