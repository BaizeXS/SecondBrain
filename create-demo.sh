#!/bin/bash
# 创建演示数据的脚本

echo "🎯 SecondBrain 演示数据创建脚本"
echo "================================"

# 检查 Docker 服务是否运行
if ! docker compose ps | grep -q "backend.*Up"; then
    echo "❌ 后端服务未运行，请先启动服务："
    echo "   docker compose up -d"
    exit 1
fi

# 运行创建演示数据的 Python 脚本
echo ""
echo "📊 开始创建演示数据..."
docker compose exec backend python create-demo-data.py

echo ""
echo "✅ 完成！"
echo ""
echo "🌐 现在可以访问系统并使用以下账号登录："
echo "   - demo@example.com / Demo123!"
echo "   - teacher@demo.com / Teacher123!"
echo "   - student@demo.com / Student123!"
echo ""
echo "💡 系统中已包含："
echo "   - 3 个演示用户"
echo "   - 3 个知识空间（包含 AI 研究、毕设资料等）"
echo "   - 多篇笔记（系统架构、技术调研等）"
echo "   - 2 个演示对话（展示 AI 对话功能）"
echo "   - 4 个 AI Agents（通用、研究、写作、编程）"