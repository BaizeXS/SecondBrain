"""测试服务器连接."""

import asyncio

import httpx


async def test_connection():
    """测试服务器是否可访问."""
    try:
        async with httpx.AsyncClient() as client:
            # 测试根路径
            response = await client.get("http://localhost:8000/")
            print(f"根路径状态: {response.status_code}")

            # 测试API文档
            response = await client.get("http://localhost:8000/docs")
            print(f"API文档状态: {response.status_code}")

            # 测试健康检查
            response = await client.get("http://localhost:8000/api/v1/health")
            print(f"健康检查状态: {response.status_code}")

    except Exception as e:
        print(f"连接错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
