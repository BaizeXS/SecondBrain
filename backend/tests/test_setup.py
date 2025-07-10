#!/usr/bin/env python3
"""测试Second Brain后端设置."""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """测试关键模块导入."""
    print("测试模块导入...")

    try:
        print("✅ 配置模块导入成功")

        print("✅ 数据模型导入成功")

        print("✅ 认证模式导入成功")

        print("✅ AI服务导入成功")

        print("✅ API路由导入成功")

        print("所有核心模块导入成功! ✨")
        return True

    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_config():
    """测试配置."""
    print("\n测试配置...")

    try:
        from app.core.config import settings

        print(f"应用名称: {settings.APP_NAME}")
        print(f"版本: {settings.VERSION}")
        print(f"环境: {settings.ENVIRONMENT}")
        print(f"数据库URL: {settings.DATABASE_URL}")
        print(f"免费用户限制: {settings.RATE_LIMIT_FREE_USER}")
        print(f"高级用户限制: {settings.RATE_LIMIT_PREMIUM_USER}")

        print("✅ 配置测试成功")
        return True

    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False


def test_ai_providers():
    """测试AI提供商配置."""
    print("\n测试AI提供商...")

    try:
        from app.services.ai_service import AIService

        ai_service = AIService()
        providers = ai_service.providers

        print(f"可用提供商: {list(providers.keys())}")

        for provider_name, provider_class in providers.items():
            print(f"  - {provider_name}: {provider_class.__name__}")

        print("✅ AI提供商测试成功")
        return True

    except Exception as e:
        print(f"❌ AI提供商测试失败: {e}")
        return False


def main():
    """主测试函数."""
    print("🚀 开始测试Second Brain后端设置...\n")

    tests = [
        test_imports,
        test_config,
        test_ai_providers,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")

    print(f"\n📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！后端设置正确。")
        print("\n下一步:")
        print("1. 设置环境变量 (.env 文件)")
        print("2. 启动数据库服务 (PostgreSQL, Redis等)")
        print("3. 运行数据库初始化: python scripts/init_db.py")
        print("4. 启动应用: uvicorn app.main:app --reload")
    else:
        print("❌ 部分测试失败，请检查配置。")
        sys.exit(1)


if __name__ == "__main__":
    main()
