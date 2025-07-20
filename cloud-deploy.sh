#!/bin/bash
# SecondBrain 云服务器通用部署脚本（支持腾讯云、阿里云、DigitalOcean等）
# 使用方法: bash deploy.sh

set -e  # 遇到错误立即停止

echo "🚀 SecondBrain 自动部署脚本"
echo "================================"

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
  echo "请使用 root 用户运行此脚本"
  echo "使用: sudo bash deploy.sh"
  exit 1
fi

# 获取服务器 IP
SERVER_IP=$(curl -s ifconfig.me)
echo "📍 服务器 IP: $SERVER_IP"

# 1. 更新系统
echo -e "\n📦 更新系统包..."
apt update && apt upgrade -y
apt install -y curl git nano

# 2. 安装 Docker
echo -e "\n🐳 安装 Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo "Docker 已安装"
fi

# 3. 安装 Docker Compose
echo -e "\n🐳 安装 Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose 已安装"
fi

# 4. 获取 GitHub 仓库地址
echo -e "\n📝 请输入您的 GitHub 仓库信息:"
read -p "GitHub 用户名: " GITHUB_USER
read -p "仓库名 (默认: SecondBrain): " REPO_NAME
REPO_NAME=${REPO_NAME:-SecondBrain}

# 5. 克隆项目
echo -e "\n📥 克隆项目..."
if [ -d "$REPO_NAME" ]; then
    echo "项目目录已存在，更新代码..."
    cd $REPO_NAME
    git pull
else
    git clone "https://github.com/$GITHUB_USER/$REPO_NAME.git"
    cd $REPO_NAME
fi

# 6. 配置环境变量
echo -e "\n🔧 配置环境变量..."
if [ ! -f backend/.env ]; then
    echo "创建 .env 文件..."
    
    # 获取 API Key
    echo -e "\n请输入至少一个 AI API Key:"
    echo "1. OpenRouter (推荐): https://openrouter.ai"
    echo "2. OpenAI: https://platform.openai.com"
    echo "3. Anthropic: https://www.anthropic.com"
    
    read -p "OPENROUTER_API_KEY (可选): " OPENROUTER_KEY
    read -p "OPENAI_API_KEY (可选): " OPENAI_KEY
    read -p "ANTHROPIC_API_KEY (可选): " ANTHROPIC_KEY
    
    # 生成随机密钥
    SECRET_KEY=$(openssl rand -hex 32)
    
    # 创建 .env 文件
    cat > backend/.env << EOF
# AI API Keys
OPENROUTER_API_KEY=$OPENROUTER_KEY
OPENAI_API_KEY=$OPENAI_KEY
ANTHROPIC_API_KEY=$ANTHROPIC_KEY

# 安全密钥
SECRET_KEY=$SECRET_KEY

# 数据库配置（使用 docker-compose 默认值）
DATABASE_URL=postgresql+asyncpg://secondbrain:secondbrain123@postgres:5432/secondbrain
REDIS_URL=redis://redis:6379/0

# MinIO 配置
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=secondbrain

# Qdrant 配置
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# CORS 配置
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","http://$SERVER_IP:3000","http://$SERVER_IP:8000"]
EOF
    echo "✅ .env 文件创建成功"
else
    echo ".env 文件已存在，跳过配置"
fi

# 7. 启动服务
echo -e "\n🚀 启动 Docker 容器..."
docker-compose down 2>/dev/null || true
docker-compose up -d

# 8. 等待服务启动
echo -e "\n⏳ 等待服务启动（30秒）..."
sleep 30

# 9. 初始化数据库
echo -e "\n📊 初始化数据库..."
docker-compose exec -T backend alembic upgrade head

# 10. 创建演示用户
echo -e "\n👤 创建演示用户..."
docker-compose exec -T backend python << 'EOF'
import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.models import User
from app.core.security import get_password_hash

async def create_users():
    async with SessionLocal() as db:
        # 创建演示用户
        users = [
            {
                "username": "demo",
                "email": "demo@example.com",
                "password": "Demo123!",
                "full_name": "演示用户"
            },
            {
                "username": "test",
                "email": "test@example.com",
                "password": "Test123!",
                "full_name": "测试用户"
            }
        ]
        
        for user_data in users:
            # 检查用户是否存在
            result = await db.execute(
                select(User).filter(User.email == user_data["email"])
            )
            if not result.scalar_one_or_none():
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    is_active=True
                )
                db.add(user)
                await db.commit()
                print(f"✅ 创建用户: {user_data['email']}")
            else:
                print(f"用户已存在: {user_data['email']}")

asyncio.run(create_users())
EOF

# 11. 配置防火墙
echo -e "\n🔥 配置防火墙..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 3000/tcp  # 前端
ufw allow 8000/tcp  # 后端
ufw allow 9001/tcp  # MinIO Console
ufw --force enable

# 12. 创建更新脚本
echo -e "\n📝 创建更新脚本..."
cat > update.sh << 'EOF'
#!/bin/bash
# 快速更新脚本
cd $(dirname "$0")
git pull
docker-compose down
docker-compose up -d
echo "✅ 更新完成！"
EOF
chmod +x update.sh

# 13. 显示部署信息
clear
cat << EOF
🎉 ================================ 🎉
   SecondBrain 部署完成！
🎉 ================================ 🎉

🌐 访问地址:
   前端: http://$SERVER_IP:3000
   后端 API: http://$SERVER_IP:8000
   API 文档: http://$SERVER_IP:8000/docs
   MinIO 控制台: http://$SERVER_IP:9001

👤 测试账号:
   账号1: demo@example.com / Demo123!
   账号2: test@example.com / Test123!

📝 常用命令:
   查看日志: docker-compose logs -f
   重启服务: docker-compose restart
   停止服务: docker-compose down
   更新代码: ./update.sh

💡 下一步:
   1. 访问前端测试功能
   2. 上传测试文档
   3. 配置域名（可选）

🔧 故障排查:
   如遇问题，请查看日志:
   docker-compose logs backend
   docker-compose logs frontend

================================
EOF

# 14. 保存部署信息
cat > deployment-info.txt << EOF
SecondBrain 部署信息
===================
部署时间: $(date)
服务器 IP: $SERVER_IP
前端地址: http://$SERVER_IP:3000
后端地址: http://$SERVER_IP:8000
API 文档: http://$SERVER_IP:8000/docs
MinIO: http://$SERVER_IP:9001 (minioadmin/minioadmin)

测试账号:
- demo@example.com / Demo123!
- test@example.com / Test123!
EOF

echo -e "\n部署信息已保存到 deployment-info.txt"
echo "祝您演示成功! 🚀"