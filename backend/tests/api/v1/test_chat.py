"""测试聊天相关的API端点"""

import pytest
import json
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User, Space, Conversation


class TestChatEndpoints:
    """聊天端点测试"""
    
    @pytest.mark.asyncio
    async def test_chat_completion_success(self, async_client: AsyncClient, auth_headers: dict):
        """测试成功的聊天完成"""
        response = await async_client.post(
            "/api/v1/chat/completions",
            headers=auth_headers,
            json={
                "messages": [
                    {"role": "user", "content": "Hello, how are you?"}
                ],
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "stream": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "content" in data
        assert data["role"] == "assistant"
    
    @pytest.mark.asyncio
    async def test_chat_completion_with_conversation(
        self, 
        async_client: AsyncClient, 
        auth_headers: dict,
        test_conversation: Conversation
    ):
        """测试在对话中的聊天完成"""
        response = await async_client.post(
            "/api/v1/chat/completions",
            headers=auth_headers,
            json={
                "messages": [
                    {"role": "user", "content": "Continue our discussion"}
                ],
                "model": "gpt-3.5-turbo",
                "conversation_id": test_conversation.id
            }
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_chat_completion_streaming(self, async_client: AsyncClient, auth_headers: dict):
        """测试流式聊天完成"""
        response = await async_client.post(
            "/api/v1/chat/completions",
            headers=auth_headers,
            json={
                "messages": [
                    {"role": "user", "content": "Tell me a story"}
                ],
                "model": "gpt-3.5-turbo",
                "stream": True
            }
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"
        
        # 读取流式响应
        chunks = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]
                if data != "[DONE]":
                    chunks.append(json.loads(data))
        
        assert len(chunks) > 0
        assert all("content" in chunk for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_chat_completion_invalid_model(self, async_client: AsyncClient, auth_headers: dict):
        """测试无效模型"""
        response = await async_client.post(
            "/api/v1/chat/completions",
            headers=auth_headers,
            json={
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "model": "invalid-model"
            }
        )
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_chat_completion_without_messages(self, async_client: AsyncClient, auth_headers: dict):
        """测试没有消息的请求"""
        response = await async_client.post(
            "/api/v1/chat/completions",
            headers=auth_headers,
            json={
                "messages": [],
                "model": "gpt-3.5-turbo"
            }
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_chat_completion_unauthorized(self, async_client: AsyncClient):
        """测试未授权的聊天请求"""
        response = await async_client.post(
            "/api/v1/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "model": "gpt-3.5-turbo"
            }
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_conversations(self, async_client: AsyncClient, auth_headers: dict):
        """测试获取对话列表"""
        response = await async_client.get(
            "/api/v1/chat/conversations",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    @pytest.mark.asyncio
    async def test_get_conversation_messages(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_conversation: Conversation
    ):
        """测试获取对话消息"""
        response = await async_client.get(
            f"/api/v1/chat/conversations/{test_conversation.id}/messages",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    @pytest.mark.asyncio
    async def test_delete_conversation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_conversation: Conversation
    ):
        """测试删除对话"""
        response = await async_client.delete(
            f"/api/v1/chat/conversations/{test_conversation.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # 验证对话已被删除
        response = await async_client.get(
            f"/api/v1/chat/conversations/{test_conversation.id}",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_search_mode(self, async_client: AsyncClient, auth_headers: dict):
        """测试搜索模式"""
        response = await async_client.post(
            "/api/v1/chat/completions",
            headers=auth_headers,
            json={
                "messages": [
                    {"role": "user", "content": "What is the capital of France?"}
                ],
                "model": "gpt-3.5-turbo",
                "mode": "search"
            }
        )
        assert response.status_code == 200
        data = response.json()
        # 搜索模式应该包含引用
        assert "citations" in data or "sources" in data


class TestChatValidation:
    """聊天输入验证测试"""
    
    @pytest.mark.asyncio
    async def test_invalid_temperature(self, async_client: AsyncClient, auth_headers: dict):
        """测试无效的温度参数"""
        response = await async_client.post(
            "/api/v1/chat/completions",
            headers=auth_headers,
            json={
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "model": "gpt-3.5-turbo",
                "temperature": 3.0  # 超出范围
            }
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_invalid_message_role(self, async_client: AsyncClient, auth_headers: dict):
        """测试无效的消息角色"""
        response = await async_client.post(
            "/api/v1/chat/completions",
            headers=auth_headers,
            json={
                "messages": [
                    {"role": "invalid_role", "content": "Hello"}
                ],
                "model": "gpt-3.5-turbo"
            }
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_message_too_long(self, async_client: AsyncClient, auth_headers: dict):
        """测试过长的消息"""
        long_message = "a" * 100000  # 100k字符
        response = await async_client.post(
            "/api/v1/chat/completions",
            headers=auth_headers,
            json={
                "messages": [
                    {"role": "user", "content": long_message}
                ],
                "model": "gpt-3.5-turbo"
            }
        )
        # 应该有某种限制
        assert response.status_code in [400, 413, 422]
    
    @pytest.mark.asyncio
    async def test_too_many_messages(self, async_client: AsyncClient, auth_headers: dict):
        """测试过多的消息"""
        messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(200)
        ]
        response = await async_client.post(
            "/api/v1/chat/completions",
            headers=auth_headers,
            json={
                "messages": messages,
                "model": "gpt-3.5-turbo"
            }
        )
        # 应该有消息数量限制
        assert response.status_code in [400, 422]