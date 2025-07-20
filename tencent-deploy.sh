#!/bin/bash
# 腾讯云快速部署脚本（超简单版）

echo "🚀 SecondBrain 腾讯云部署"
echo "========================="

# 彩色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 安装 Docker（如果没有）
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}安装 Docker...${NC}"
    curl -fsSL https://get.docker.com | sh
fi

# 2. 检查 Docker Compose（新版本使用 docker compose）
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    echo -e "${GREEN}Docker Compose 已安装（使用 docker compose）${NC}"
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}Docker Compose 已安装（使用 docker-compose）${NC}"
    COMPOSE_CMD="docker-compose"
else
    echo -e "${YELLOW}安装 Docker Compose...${NC}"
    # 尝试使用 Docker 插件方式
    apt-get update
    apt-get install -y docker-compose-plugin
    COMPOSE_CMD="docker compose"
fi

# 3. 克隆项目
echo -e "\n${YELLOW}请输入 GitHub 信息：${NC}"
read -p "GitHub 用户名: " GITHUB_USER
read -p "仓库名 [SecondBrain]: " REPO_NAME
REPO_NAME=${REPO_NAME:-SecondBrain}

if [ -d "$REPO_NAME" ]; then
    cd $REPO_NAME
    git pull
else
    git clone "https://github.com/$GITHUB_USER/$REPO_NAME.git"
    cd $REPO_NAME
fi

# 4. 配置环境变量
if [ ! -f backend/.env ]; then
    echo -e "\n${YELLOW}配置 API Key（至少需要一个）：${NC}"
    echo "1. OpenRouter (推荐): https://openrouter.ai"
    echo "2. 其他可选: OpenAI, Anthropic"
    
    read -p "OPENROUTER_API_KEY: " OPENROUTER_KEY
    
    cat > backend/.env << EOF
# AI API Keys
OPENROUTER_API_KEY=$OPENROUTER_KEY

# 其他配置使用默认值
SECRET_KEY=$(openssl rand -hex 32)
EOF
fi

# 5. 启动服务
echo -e "\n${YELLOW}启动服务...${NC}"
$COMPOSE_CMD up -d

# 6. 等待启动
echo -e "\n${YELLOW}等待服务启动（30秒）...${NC}"
sleep 30

# 7. 初始化数据库
echo -e "\n${YELLOW}初始化数据库...${NC}"
$COMPOSE_CMD exec -T backend alembic upgrade head

# 8. 创建测试账号
$COMPOSE_CMD exec -T backend python << 'EOF'
import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.models import User
from app.core.security import get_password_hash

async def create_test_user():
    async with SessionLocal() as db:
        result = await db.execute(select(User).filter(User.email == 'demo@example.com'))
        if not result.scalar_one_or_none():
            user = User(
                username='demo',
                email='demo@example.com',
                hashed_password=get_password_hash('Demo123!'),
                full_name='演示用户',
                is_active=True
            )
            db.add(user)
            await db.commit()
            print('✅ 测试账号创建成功')

asyncio.run(create_test_user())
EOF

# 9. 获取服务器IP
SERVER_IP=$(curl -s ifconfig.me)

# 10. 完成提示
clear
echo -e "${GREEN}"
echo "🎉 =============================== 🎉"
echo "   SecondBrain 部署成功！"
echo "🎉 =============================== 🎉"
echo -e "${NC}"
echo ""
echo "📱 访问地址："
echo "   前端: http://$SERVER_IP:3000"
echo "   后端: http://$SERVER_IP:8000"
echo ""
echo "👤 测试账号："
echo "   邮箱: demo@example.com"
echo "   密码: Demo123!"
echo ""
echo "💡 常用命令："
echo "   查看日志: $COMPOSE_CMD logs -f"
echo "   重启服务: $COMPOSE_CMD restart"
echo ""
echo "🔄 更新代码："
echo "   git pull && $COMPOSE_CMD restart"
echo ""