#!/usr/bin/env python3
"""测试 Deep Research 功能"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.deep_research_service import deep_research_service


async def test_deep_research():
    """测试 Deep Research 服务"""
    print("🔍 测试 Deep Research 功能")
    print("-" * 50)
    
    # 测试查询
    query = "什么是机器学习中的注意力机制？"
    
    try:
        # 创建研究（不需要用户和数据库）
        print(f"📝 研究主题: {query}")
        print("⏳ 正在进行深度研究...")
        
        result = await deep_research_service.create_research(
            query=query,
            mode="general",
            user=None,
            db=None,
            space_id=None
        )
        
        if "error" in result:
            print(f"❌ 错误: {result['error']}")
            print(f"   详情: {result.get('message', '')}")
        else:
            print("✅ 研究完成!")
            print(f"   状态: {result.get('status', 'unknown')}")
            
            # 提取内容
            if "result" in result and "choices" in result["result"]:
                content = result["result"]["choices"][0]["message"]["content"]
                print(f"\n📄 研究报告预览:")
                print("-" * 50)
                print(content[:500] + "..." if len(content) > 500 else content)
                print("-" * 50)
            
    except Exception as e:
        print(f"❌ 发生异常: {type(e).__name__}")
        print(f"   详情: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_ai_service():
    """直接测试 AI Service"""
    print("\n\n🤖 直接测试 AI Service")
    print("-" * 50)
    
    from app.services.ai_service import ai_service
    
    # 检查 OpenRouter 配置
    print("📋 AI Service 配置状态:")
    print(f"   OpenRouter Client: {'✅ 已配置' if ai_service.openrouter_client else '❌ 未配置'}")
    print(f"   Ollama Provider: {'✅ 已配置' if ai_service.ollama_provider else '❌ 未配置'}")
    
    # 测试 Deep Research 模型
    try:
        print("\n🔬 测试 Deep Research 模型...")
        response = await ai_service.chat(
            messages=[
                {"role": "user", "content": "什么是深度学习？简短回答。"}
            ],
            model="perplexity/sonar-deep-research",
            temperature=0.7
        )
        
        print("✅ 模型调用成功!")
        print(f"   响应: {response[:200]}...")
        
    except Exception as e:
        print(f"❌ 模型调用失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 SecondBrain Deep Research 测试工具")
    print("=" * 50)
    
    # 检查环境变量
    print("🔑 环境变量检查:")
    env_vars = {
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
        "PERPLEXITY_API_KEY": os.getenv("PERPLEXITY_API_KEY"),
    }
    
    for key, value in env_vars.items():
        if value:
            print(f"   {key}: ✅ 已设置 ({value[:10]}...)")
        else:
            print(f"   {key}: ❌ 未设置")
    
    # 运行测试
    asyncio.run(test_ai_service())
    asyncio.run(test_deep_research())