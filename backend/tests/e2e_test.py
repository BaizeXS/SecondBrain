#!/usr/bin/env python3
"""
端到端测试脚本 - 测试 Second Brain 的所有核心功能
"""
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, Optional

API_BASE_URL = "http://localhost:8000/api/v1"

class SecondBrainE2ETest:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.space_id: Optional[int] = None
        self.conversation_id: Optional[int] = None
        self.document_id: Optional[int] = None
        self.note_id: Optional[int] = None
        self.test_user = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
    
    async def setup(self):
        """初始化测试环境"""
        self.session = aiohttp.ClientSession()
        print("✅ 测试环境初始化完成")
    
    async def cleanup(self):
        """清理测试环境"""
        if self.session:
            await self.session.close()
        print("✅ 测试环境清理完成")
    
    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发起 HTTP 请求"""
        url = f"{API_BASE_URL}{endpoint}"
        headers = kwargs.get("headers", {})
        
        if self.access_token and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        kwargs["headers"] = headers
        
        async with self.session.request(method, url, **kwargs) as response:
            data = await response.json()
            if response.status >= 400:
                print(f"❌ 请求失败 {method} {endpoint}: {response.status} - {data}")
            return data, response.status
    
    async def test_1_user_registration(self):
        """测试 1: 用户注册"""
        print("\n📋 测试 1: 用户注册")
        
        data, status = await self.make_request(
            "POST", "/auth/register",
            json=self.test_user
        )
        
        assert status == 200, f"注册失败: {data}"
        assert "id" in data, "响应中没有用户 ID"
        self.user_id = data["id"]
        print(f"✅ 用户注册成功: {self.test_user['username']}")
    
    async def test_2_user_login(self):
        """测试 2: 用户登录"""
        print("\n📋 测试 2: 用户登录")
        
        data, status = await self.make_request(
            "POST", "/auth/login/json",
            json={
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
        )
        
        assert status == 200, f"登录失败: {data}"
        assert "access_token" in data, "响应中没有访问令牌"
        self.access_token = data["access_token"]
        print(f"✅ 用户登录成功，获得访问令牌")
    
    async def test_3_get_user_info(self):
        """测试 3: 获取用户信息"""
        print("\n📋 测试 3: 获取用户信息")
        
        data, status = await self.make_request("GET", "/users/me")
        
        assert status == 200, f"获取用户信息失败: {data}"
        assert data["username"] == self.test_user["username"], "用户名不匹配"
        print(f"✅ 成功获取用户信息: {data['username']}")
    
    async def test_4_get_available_models(self):
        """测试 4: 获取可用模型列表"""
        print("\n📋 测试 4: 获取可用模型列表")
        
        data, status = await self.make_request("GET", "/chat/models")
        
        assert status == 200, f"获取模型列表失败: {data}"
        assert "models" in data, "响应中没有模型列表"
        assert len(data["models"]) > 0, "模型列表为空"
        print(f"✅ 获取到 {len(data['models'])} 个可用模型")
        for model in data["models"][:3]:  # 只显示前3个
            print(f"   - {model['name']} ({model['id']})")
    
    async def test_5_get_agents(self):
        """测试 5: 获取 AI 代理列表"""
        print("\n📋 测试 5: 获取 AI 代理列表")
        
        data, status = await self.make_request("GET", "/agents/")
        
        assert status == 200, f"获取代理列表失败: {data}"
        assert "items" in data, "响应中没有代理列表"
        print(f"✅ 获取到 {len(data['items'])} 个 AI 代理")
        for agent in data["items"]:
            print(f"   - {agent['name']} ({agent['agent_type']})")
    
    async def test_6_create_space(self):
        """测试 6: 创建知识空间"""
        print("\n📋 测试 6: 创建知识空间")
        
        space_data = {
            "name": "测试知识空间",
            "description": "这是一个端到端测试创建的知识空间",
            "is_public": False,
            "tags": ["test", "e2e"]
        }
        
        data, status = await self.make_request("POST", "/spaces/", json=space_data)
        
        assert status == 200, f"创建空间失败: {data}"
        assert "id" in data, "响应中没有空间 ID"
        self.space_id = data["id"]
        print(f"✅ 知识空间创建成功: {data['name']} (ID: {self.space_id})")
    
    async def test_7_create_conversation(self):
        """测试 7: 创建对话"""
        print("\n📋 测试 7: 创建对话")
        
        conv_data = {
            "title": "测试对话",
            "mode": "chat",
            "space_id": self.space_id
        }
        
        data, status = await self.make_request("POST", "/chat/conversations", json=conv_data)
        
        assert status == 200, f"创建对话失败: {data}"
        assert "id" in data, "响应中没有对话 ID"
        self.conversation_id = data["id"]
        print(f"✅ 对话创建成功 (ID: {self.conversation_id})")
    
    async def test_8_chat_completion(self):
        """测试 8: 发送聊天消息"""
        print("\n📋 测试 8: 发送聊天消息")
        
        chat_data = {
            "model": "openrouter/auto",
            "messages": [
                {"role": "system", "content": "你是一个有帮助的助手。"},
                {"role": "user", "content": "你好，这是一个测试消息。请简单回复。"}
            ],
            "conversation_id": self.conversation_id,
            "stream": False
        }
        
        data, status = await self.make_request("POST", "/chat/completions", json=chat_data)
        
        assert status == 200, f"聊天失败: {data}"
        assert "choices" in data, "响应中没有回复"
        assert len(data["choices"]) > 0, "没有生成回复"
        
        response_text = data["choices"][0]["message"]["content"]
        print(f"✅ 收到 AI 回复: {response_text[:100]}...")
    
    async def test_9_create_note(self):
        """测试 9: 创建笔记"""
        print("\n📋 测试 9: 创建笔记")
        
        note_data = {
            "title": "测试笔记",
            "content": "这是一个端到端测试创建的笔记内容。",
            "space_id": self.space_id
        }
        
        data, status = await self.make_request("POST", "/notes/", json=note_data)
        
        assert status == 200, f"创建笔记失败: {data}"
        assert "id" in data, "响应中没有笔记 ID"
        self.note_id = data["id"]
        print(f"✅ 笔记创建成功: {data['title']} (ID: {self.note_id})")
    
    async def test_10_update_note(self):
        """测试 10: 更新笔记"""
        print("\n📋 测试 10: 更新笔记")
        
        update_data = {
            "title": "更新后的测试笔记",
            "content": "这是更新后的笔记内容。\n\n添加了一些新内容。"
        }
        
        data, status = await self.make_request(
            "PUT", f"/notes/{self.note_id}", 
            json=update_data
        )
        
        assert status == 200, f"更新笔记失败: {data}"
        assert data["title"] == update_data["title"], "笔记标题未更新"
        print(f"✅ 笔记更新成功")
    
    async def test_11_deep_research(self):
        """测试 11: 深度研究功能"""
        print("\n📋 测试 11: 深度研究功能")
        
        research_data = {
            "query": "人工智能的发展历史",
            "mode": "general",
            "stream": False
        }
        
        print("   ⏳ 正在进行深度研究（可能需要 10-30 秒）...")
        data, status = await self.make_request(
            "POST", "/agents/deep-research", 
            json=research_data,
            timeout=aiohttp.ClientTimeout(total=60)  # 60秒超时
        )
        
        assert status == 200, f"深度研究失败: {data}"
        assert "result" in data, "响应中没有研究结果"
        assert "space_id" in data, "响应中没有创建的空间 ID"
        
        print(f"✅ 深度研究完成")
        print(f"   - 创建的空间 ID: {data['space_id']}")
        print(f"   - 找到 {data.get('total_sources', 0)} 个相关资源")
        print(f"   - 结果预览: {data['result'][:200]}...")
    
    async def test_12_get_spaces(self):
        """测试 12: 获取空间列表"""
        print("\n📋 测试 12: 获取空间列表")
        
        data, status = await self.make_request("GET", "/spaces/")
        
        assert status == 200, f"获取空间列表失败: {data}"
        assert "spaces" in data, "响应中没有空间列表"
        assert "total" in data, "响应中没有总数"
        
        print(f"✅ 获取到 {data['total']} 个空间")
        for space in data["spaces"][:3]:  # 只显示前3个
            print(f"   - {space['name']} (ID: {space['id']})")
    
    async def test_13_logout(self):
        """测试 13: 用户登出"""
        print("\n📋 测试 13: 用户登出")
        
        data, status = await self.make_request("POST", "/auth/logout")
        
        assert status == 200, f"登出失败: {data}"
        print(f"✅ 用户登出成功")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("="*50)
        print("🚀 开始 Second Brain 端到端测试")
        print("="*50)
        
        try:
            await self.setup()
            
            # 按顺序执行所有测试
            await self.test_1_user_registration()
            await self.test_2_user_login()
            await self.test_3_get_user_info()
            await self.test_4_get_available_models()
            await self.test_5_get_agents()
            await self.test_6_create_space()
            await self.test_7_create_conversation()
            await self.test_8_chat_completion()
            await self.test_9_create_note()
            await self.test_10_update_note()
            await self.test_11_deep_research()
            await self.test_12_get_spaces()
            await self.test_13_logout()
            
            print("\n" + "="*50)
            print("✅ 所有测试通过！Second Brain 后端功能正常。")
            print("="*50)
            
        except AssertionError as e:
            print(f"\n❌ 测试失败: {str(e)}")
            raise
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            raise
        finally:
            await self.cleanup()

async def main():
    test = SecondBrainE2ETest()
    await test.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())