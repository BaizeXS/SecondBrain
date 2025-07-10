"""测试 v2 端点是否正常工作."""

import asyncio

import httpx
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"


async def test_v2_endpoints():
    """测试 v2 端点."""
    async with httpx.AsyncClient() as client:
        print("🔍 测试 v2 端点...\n")

        # 1. 登录获取令牌
        print("1. 登录...")
        login_data = {
            "username": "testuser_demo",
            "password": "testpassword123"
        }
        response = await client.post(f"{BASE_URL}/auth/login/json", json=login_data)

        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ 登录成功\n")
        else:
            print(f"❌ 登录失败: {response.json()}")
            return

        # 2. 测试用户端点
        print("2. 测试用户端点...")
        response = await client.get(f"{BASE_URL}/users/me", headers=headers)
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ 获取用户信息成功: {user_info['username']}")
        else:
            print(f"❌ 获取用户信息失败: {response.status_code}")

        # 获取用户统计
        response = await client.get(f"{BASE_URL}/users/me/stats", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 用户统计: 空间={stats['stats']['spaces']}, 文档={stats['stats']['documents']}")
        else:
            print(f"❌ 获取统计失败: {response.status_code}")

        # 3. 测试空间端点
        print("\n3. 测试空间端点...")
        response = await client.get(f"{BASE_URL}/spaces/", headers=headers)
        if response.status_code == 200:
            spaces = response.json()
            print(f"✅ 获取空间列表成功: 共 {spaces['total']} 个空间")

            if spaces['spaces']:
                space_id = spaces['spaces'][0]['id']
                # 获取空间详情
                response = await client.get(f"{BASE_URL}/spaces/{space_id}", headers=headers)
                if response.status_code == 200:
                    print("✅ 获取空间详情成功")
                else:
                    print(f"❌ 获取空间详情失败: {response.status_code}")
        else:
            print(f"❌ 获取空间列表失败: {response.status_code}")

        # 4. 测试文档端点
        print("\n4. 测试文档端点...")
        response = await client.get(f"{BASE_URL}/documents/", headers=headers)
        if response.status_code == 200:
            documents = response.json()
            print(f"✅ 获取文档列表成功: 共 {documents['total']} 个文档")
        else:
            print(f"❌ 获取文档列表失败: {response.status_code}")

        # 5. 测试对话端点
        print("\n5. 测试对话端点...")
        response = await client.get(f"{BASE_URL}/chat/conversations", headers=headers)
        if response.status_code == 200:
            conversations = response.json()
            print(f"✅ 获取对话列表成功: 共 {conversations['total']} 个对话")
        else:
            print(f"❌ 获取对话列表失败: {response.status_code}")

        # 创建新对话
        conversation_data = {
            "title": "测试对话",
            "mode": "chat"
        }
        response = await client.post(
            f"{BASE_URL}/chat/conversations",
            json=conversation_data,
            headers=headers
        )
        if response.status_code == 201:
            print("✅ 创建对话成功")
        else:
            print(f"❌ 创建对话失败: {response.status_code} - {response.text}")

        # 6. 测试代理端点
        print("\n6. 测试代理端点...")
        response = await client.get(f"{BASE_URL}/agents/", headers=headers)
        if response.status_code == 200:
            agents = response.json()
            print(f"✅ 获取代理列表成功: 共 {agents['total']} 个代理")

            if agents['agents']:
                agent_id = agents['agents'][0]['id']
                # 获取代理详情
                response = await client.get(f"{BASE_URL}/agents/{agent_id}", headers=headers)
                if response.status_code == 200:
                    print("✅ 获取代理详情成功")
                else:
                    print(f"❌ 获取代理详情失败: {response.status_code}")
        else:
            print(f"❌ 获取代理列表失败: {response.status_code}")

        print("\n✅ v2 端点测试完成！")


if __name__ == "__main__":
    asyncio.run(test_v2_endpoints())
