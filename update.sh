#!/bin/bash
# 服务器更新脚本

echo "🔄 更新 SecondBrain..."

# 拉取最新代码
echo "📥 拉取最新代码..."
git pull

# 检查是否需要重新构建
if git diff HEAD~ --name-only | grep -E "(requirements\.txt|package\.json|Dockerfile)"; then
    echo "🔨 检测到依赖变化，重新构建..."
    docker compose build
fi

# 重启服务
echo "🔄 重启服务..."
docker compose restart

# 检查是否有数据库迁移
if git diff HEAD~ --name-only | grep -E "alembic/versions"; then
    echo "📊 运行数据库迁移..."
    docker compose exec backend alembic upgrade head
fi

echo "✅ 更新完成！"

# 显示服务状态
docker compose ps