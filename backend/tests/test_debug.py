"""调试示例 - 展示错误处理."""

import asyncio

import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def test_error_handling():
    """测试错误处理."""
    async with httpx.AsyncClient() as client:
        # 1. 测试未授权访问
        print("1. 测试未授权访问...")
        try:
            response = await client.get(f"{BASE_URL}/spaces/")
            print(f"状态码: {response.status_code}")
            print(f"错误信息: {response.json()}")
        except Exception as e:
            print(f"发生异常: {e}")

        # 2. 测试错误的登录信息
        print("\n2. 测试错误的登录...")
        try:
            login_data = {
                "username": "wrong_user",
                "password": "wrong_password"
            }
            response = await client.post(
                f"{BASE_URL}/auth/login/json",
                json=login_data
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
        except Exception as e:
            print(f"发生异常: {e}")

        # 3. 测试无效的数据格式
        print("\n3. 测试无效的数据格式...")
        # 先正常登录获取token
        login_data = {
            "username": "testuser_demo",
            "password": "testpassword123"
        }
        response = await client.post(
            f"{BASE_URL}/auth/login/json",
            json=login_data
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 发送无效数据
            invalid_space = {
                "name": "",  # 空名称应该失败
                "description": "测试"
            }
            response = await client.post(
                f"{BASE_URL}/spaces/",
                json=invalid_space,
                headers=headers
            )
            print(f"状态码: {response.status_code}")
            print(f"验证错误: {response.json()}")

if __name__ == "__main__":
    asyncio.run(test_error_handling())
