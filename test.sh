#!/bin/bash
# 简单的测试脚本

echo "🧪 运行测试..."

# 确保服务正在运行
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ 服务未运行，请先执行 ./start.sh"
    exit 1
fi

# 运行单元测试
echo "📝 运行单元测试..."
cd backend
uv run pytest tests/unit/ -v

# 运行集成测试
echo "🔗 运行集成测试..."
uv run pytest tests/integration/ -v

# 显示测试覆盖率
echo "📊 生成测试覆盖率报告..."
uv run pytest --cov=app --cov-report=html --cov-report=term

echo "✅ 测试完成！"
echo "查看覆盖率报告: open backend/htmlcov/index.html"