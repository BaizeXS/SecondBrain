#!/usr/bin/env python3
"""
简单的端到端测试脚本 - 测试 Second Brain 的核心功能
"""
import requests
import json
import time

API_BASE_URL = "http://localhost:8000/api/v1"

class SecondBrainE2ETest:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        self.space_id = None
        self.conversation_id = None
        self.note_id = None
        self.test_user = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
    
    def make_request(self, method, endpoint, **kwargs):
        """发起 HTTP 请求"""
        url = f"{API_BASE_URL}{endpoint}"
        headers = kwargs.get("headers", {})
        
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        kwargs["headers"] = headers
        
        response = self.session.request(method, url, **kwargs)
        return response
    
    def test_1_health_check(self):
        """测试 1: 健康检查"""
        print("\n📋 测试 1: 健康检查")
        
        response = self.make_request("GET", "/health")
        assert response.status_code == 200, f"健康检查失败: {response.text}"
        print("✅ 后端服务运行正常")
    
    def test_2_user_registration(self):
        """测试 2: 用户注册"""
        print("\n📋 测试 2: 用户注册")
        
        response = self.make_request("POST", "/auth/register", json=self.test_user)
        if response.status_code not in [200, 201]:
            print(f"注册失败: {response.text}")
            assert False, f"注册失败: {response.text}"
        
        data = response.json()
        self.user_id = data["id"]
        print(f"✅ 用户注册成功: {self.test_user['username']} (ID: {self.user_id})")
    
    def test_3_user_login(self):
        """测试 3: 用户登录"""
        print("\n📋 测试 3: 用户登录")
        
        response = self.make_request(
            "POST", "/auth/login/json",
            json={
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
        )
        assert response.status_code == 200, f"登录失败: {response.text}"
        
        data = response.json()
        self.access_token = data["access_token"]
        print("✅ 用户登录成功，获得访问令牌")
    
    def test_4_get_user_info(self):
        """测试 4: 获取用户信息"""
        print("\n📋 测试 4: 获取用户信息")
        
        response = self.make_request("GET", "/users/me")
        assert response.status_code == 200, f"获取用户信息失败: {response.text}"
        
        data = response.json()
        assert data["username"] == self.test_user["username"], "用户名不匹配"
        print(f"✅ 成功获取用户信息: {data['username']}")
    
    def test_5_get_models(self):
        """测试 5: 获取可用模型"""
        print("\n📋 测试 5: 获取可用模型")
        
        response = self.make_request("GET", "/chat/models")
        assert response.status_code == 200, f"获取模型失败: {response.text}"
        
        data = response.json()
        print(f"✅ 获取到 {len(data['models'])} 个可用模型")
        for model in data["models"][:3]:
            print(f"   - {model['name']} ({model['id']})")
    
    def test_6_create_space(self):
        """测试 6: 创建知识空间"""
        print("\n📋 测试 6: 创建知识空间")
        
        space_data = {
            "name": "测试知识空间",
            "description": "端到端测试空间",
            "is_public": False,
            "tags": ["test"]
        }
        
        response = self.make_request("POST", "/spaces/", json=space_data)
        assert response.status_code in [200, 201], f"创建空间失败: {response.text}"
        
        data = response.json()
        self.space_id = data["id"]
        print(f"✅ 空间创建成功: {data['name']} (ID: {self.space_id})")
    
    def test_7_create_conversation(self):
        """测试 7: 创建对话"""
        print("\n📋 测试 7: 创建对话")
        
        conv_data = {
            "title": "测试对话",
            "mode": "chat",
            "space_id": self.space_id
        }
        
        response = self.make_request("POST", "/chat/conversations", json=conv_data)
        assert response.status_code in [200, 201], f"创建对话失败: {response.text}"
        
        data = response.json()
        self.conversation_id = data["id"]
        print(f"✅ 对话创建成功 (ID: {self.conversation_id})")
    
    def test_8_chat_completion(self):
        """测试 8: 聊天测试"""
        print("\n📋 测试 8: 聊天测试")
        
        chat_data = {
            "model": "openrouter/auto",
            "messages": [
                {"role": "user", "content": "你好，请简单介绍一下你自己。"}
            ],
            "conversation_id": self.conversation_id,
            "stream": False
        }
        
        response = self.make_request("POST", "/chat/completions", json=chat_data)
        assert response.status_code == 200, f"聊天失败: {response.text}"
        
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        print(f"✅ AI 回复: {reply[:100]}...")
    
    def test_9_create_note(self):
        """测试 9: 创建笔记"""
        print("\n📋 测试 9: 创建笔记")
        
        note_data = {
            "title": "测试笔记",
            "content": "这是测试内容",
            "space_id": self.space_id
        }
        
        response = self.make_request("POST", "/notes/", json=note_data)
        assert response.status_code in [200, 201], f"创建笔记失败: {response.text}"
        
        data = response.json()
        self.note_id = data["id"]
        print(f"✅ 笔记创建成功 (ID: {self.note_id})")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*50)
        print("🚀 开始 Second Brain 端到端测试")
        print("="*50)
        
        try:
            self.test_1_health_check()
            self.test_2_user_registration()
            self.test_3_user_login()
            self.test_4_get_user_info()
            self.test_5_get_models()
            self.test_6_create_space()
            self.test_7_create_conversation()
            self.test_8_chat_completion()
            self.test_9_create_note()
            
            print("\n" + "="*50)
            print("✅ 所有测试通过！")
            print("="*50)
            
        except AssertionError as e:
            print(f"\n❌ 测试失败: {str(e)}")
            return False
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            return False
        
        return True

if __name__ == "__main__":
    test = SecondBrainE2ETest()
    success = test.run_all_tests()
    exit(0 if success else 1)