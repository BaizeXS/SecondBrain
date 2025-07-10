"""后端API测试示例."""

import asyncio

import httpx

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

async def test_auth_flow():
    """测试认证流程."""
    async with httpx.AsyncClient() as client:
        # 1. 注册新用户
        print("1. 测试注册...")
        register_data = {
            "username": "testuser_demo",
            "email": "demo@test.com",
            "password": "testpassword123"
        }
        response = await client.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            print("✅ 注册成功")
        else:
            print(f"❌ 注册失败: {response.json()}")

        # 2. 登录
        print("\n2. 测试登录...")
        login_data = {
            "username": "testuser_demo",
            "password": "testpassword123"
        }
        response = await client.post(f"{BASE_URL}/auth/login/json", json=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ 登录成功")
            print(f"获得令牌: {token[:20]}...")
            return token
        else:
            print(f"❌ 登录失败: {response.json()}")
            return None

async def test_space_operations(token: str):
    """测试空间操作."""
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        # 1. 创建空间
        print("\n3. 测试创建空间...")
        space_data = {
            "name": "测试空间",
            "description": "这是一个测试空间"
        }
        response = await client.post(
            f"{BASE_URL}/spaces/",
            json=space_data,
            headers=headers
        )
        if response.status_code == 201:
            space_id = response.json()["id"]
            print("✅ 创建空间成功")
            print(f"空间ID: {space_id}")
            return space_id
        else:
            print(f"❌ 创建空间失败: {response.json()}")
            return None

        # 2. 获取空间列表
        print("\n4. 测试获取空间列表...")
        response = await client.get(f"{BASE_URL}/spaces/", headers=headers)
        if response.status_code == 200:
            spaces = response.json()
            print(f"✅ 获取成功，共有 {len(spaces)} 个空间")
        else:
            print(f"❌ 获取失败: {response.json()}")

async def main():
    """运行所有测试."""
    print("=== 开始测试 Second Brain 后端 ===\n")

    # 测试认证
    token = await test_auth_flow()

    if token:
        # 测试空间操作
        await test_space_operations(token)

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(main())
