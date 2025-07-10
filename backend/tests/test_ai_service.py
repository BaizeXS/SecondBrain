"""测试AI服务是否正常工作."""

import asyncio
import os

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def test_ai_service():
    """测试AI服务."""
    print("🔍 测试 AI 服务配置...")

    # 检查环境变量
    openai_key = os.getenv("OPENAI_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")

    print(f"OpenAI API Key: {'✅ 已设置' if openai_key else '❌ 未设置'}")
    print(f"DeepSeek API Key: {'✅ 已设置' if deepseek_key else '❌ 未设置'}")

    # 测试智能服务选择
    print("\n📦 测试服务导入...")
    try:
        from app.services import AIService, get_service_status
        status = get_service_status()
        print(f"当前使用的 AI 服务版本: {status['ai_service']}")

        if status['ai_service'] == 'full':
            print("✅ 使用完整版 AI 服务")

            # 测试简单的聊天功能
            print("\n🤖 测试 AI 聊天功能...")
            ai_service = AIService()

            # 创建一个模拟用户对象
            class MockUser:
                is_premium = False
                id = 1

            response = await ai_service.chat(
                messages=[{"role": "user", "content": "Hello, say hi back!"}],
                model="gpt-4o-mini",
                mode="chat",
                user=MockUser()
            )
            print(f"AI 响应: {response[:100] if isinstance(response, str) else str(response)[:100]}...")
            print("✅ AI 服务正常工作！")
        else:
            print("⚠️  使用简化版 AI 服务（模拟响应）")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_service())
