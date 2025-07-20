"""
AI聊天工作流集成测试。

测试AI聊天的完整功能，包括多模型支持、流式响应等。
"""

import json

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestChatWorkflow:
    """测试AI聊天工作流。"""

    async def test_basic_chat_conversation(
        self, client: AsyncClient, auth_headers: dict, mock_ai_service
    ):
        """测试基本聊天对话。"""
        # mock_ai_service 确保AI服务被正确模拟
        assert mock_ai_service is not None

        # 1. 创建对话
        conversation_data = {
            "title": "Test Chat",
            "mode": "chat",
            "model": "gpt-3.5-turbo",
        }
        conv_response = await client.post(
            "/api/v1/chat/conversations", json=conversation_data, headers=auth_headers
        )
        assert conv_response.status_code == 201
        conversation = conv_response.json()
        conversation_id = conversation["id"]

        # 2. 发送消息
        chat_data = {
            "conversation_id": conversation_id,
            "messages": [{"role": "user", "content": "Hello, can you help me?"}],
            "model": "gpt-3.5-turbo",
            "stream": False,
        }
        chat_response = await client.post(
            "/api/v1/chat/completions", json=chat_data, headers=auth_headers
        )
        assert chat_response.status_code == 200
        result = chat_response.json()
        assert "choices" in result
        assert len(result["choices"]) > 0
        assert "message" in result["choices"][0]

        # 3. 发送后续消息
        followup_data = {
            "conversation_id": conversation_id,
            "messages": [{"role": "user", "content": "Can you elaborate on that?"}],
            "model": "gpt-3.5-turbo",
            "stream": False,
        }
        followup_response = await client.post(
            "/api/v1/chat/completions", json=followup_data, headers=auth_headers
        )
        assert followup_response.status_code == 200

        # 4. 获取消息历史
        history_response = await client.get(
            f"/api/v1/chat/conversations/{conversation_id}", headers=auth_headers
        )
        assert history_response.status_code == 200
        conversation_with_messages = history_response.json()
        assert "messages" in conversation_with_messages
        assert (
            len(conversation_with_messages["messages"]) >= 4
        )  # 2个用户消息 + 2个AI响应

        # 5. 删除对话
        delete_response = await client.delete(
            f"/api/v1/chat/conversations/{conversation_id}", headers=auth_headers
        )
        assert delete_response.status_code == 204

    async def test_multi_model_chat(
        self, client: AsyncClient, auth_headers: dict, mock_ai_service
    ):
        """测试多模型聊天支持。"""
        assert mock_ai_service is not None

        # 支持的模型列表
        models = ["gpt-3.5-turbo", "gpt-4", "claude-2"]

        for model in models:
            # 1. 创建对话
            conv_data = {
                "title": f"Test {model}",
                "mode": "chat",
                "model": model,
            }
            conv_response = await client.post(
                "/api/v1/chat/conversations", json=conv_data, headers=auth_headers
            )
            assert conv_response.status_code == 201
            conversation_id = conv_response.json()["id"]

            # 2. 使用特定模型发送消息
            chat_data = {
                "conversation_id": conversation_id,
                "messages": [{"role": "user", "content": f"Test message for {model}"}],
                "model": model,
                "stream": False,
            }
            chat_response = await client.post(
                "/api/v1/chat/completions", json=chat_data, headers=auth_headers
            )
            assert chat_response.status_code == 200

            # 清理
            await client.delete(
                f"/api/v1/chat/conversations/{conversation_id}", headers=auth_headers
            )

    async def test_streaming_chat(
        self, client: AsyncClient, auth_headers: dict, mock_ai_service
    ):
        """测试流式聊天响应。"""
        assert mock_ai_service is not None

        # 1. 创建对话
        conv_response = await client.post(
            "/api/v1/chat/conversations",
            json={"title": "Streaming Test", "mode": "chat"},
            headers=auth_headers,
        )
        conversation_id = conv_response.json()["id"]

        # 2. 发送流式请求
        stream_data = {
            "conversation_id": conversation_id,
            "messages": [{"role": "user", "content": "Tell me a story"}],
            "model": "gpt-3.5-turbo",
            "stream": True,
        }

        chunks = []
        async with client.stream(
            "POST", "/api/v1/chat/completions", json=stream_data, headers=auth_headers
        ) as response:
            assert response.status_code == 200
            assert response.headers.get("content-type").startswith("text/event-stream")

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data != "[DONE]":
                        chunks.append(json.loads(data))

        assert len(chunks) > 0

        # 清理
        await client.delete(
            f"/api/v1/chat/conversations/{conversation_id}", headers=auth_headers
        )

    async def test_chat_with_context(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_space_data: dict,
        mock_ai_service,
    ):
        """测试带上下文的聊天（Space模式）。"""
        assert mock_ai_service is not None

        # 1. 创建空间
        space_response = await client.post(
            "/api/v1/spaces/", json=sample_space_data, headers=auth_headers
        )
        space_id = space_response.json()["id"]

        # 2. 上传文档作为上下文
        files = {
            "file": ("context.txt", b"Important context information here", "text/plain")
        }
        data = {"space_id": str(space_id)}
        upload_response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=auth_headers,
        )
        assert upload_response.status_code == 201

        # 3. 创建空间关联的对话
        conv_data = {
            "title": "Context Chat",
            "mode": "chat",
            "model": "gpt-3.5-turbo",
            "space_id": space_id,
        }
        conv_response = await client.post(
            "/api/v1/chat/conversations", json=conv_data, headers=auth_headers
        )
        conversation_id = conv_response.json()["id"]

        # 4. 发送需要上下文的问题
        chat_data = {
            "conversation_id": conversation_id,
            "messages": [{"role": "user", "content": "What's in the context?"}],
            "model": "gpt-3.5-turbo",
            "use_context": True,
            "stream": False,
        }
        chat_response = await client.post(
            "/api/v1/chat/completions", json=chat_data, headers=auth_headers
        )
        assert chat_response.status_code == 200

        # 清理
        await client.delete(f"/api/v1/spaces/{space_id}", headers=auth_headers)

    async def test_search_mode_chat(
        self, client: AsyncClient, auth_headers: dict, mock_ai_service
    ):
        """测试搜索模式聊天。"""
        assert mock_ai_service is not None

        # 1. 创建搜索模式对话
        conv_data = {
            "title": "Search Chat",
            "mode": "search",
            "model": "perplexity/sonar",
        }
        conv_response = await client.post(
            "/api/v1/chat/conversations", json=conv_data, headers=auth_headers
        )
        conversation_id = conv_response.json()["id"]

        # 2. 发送搜索请求
        search_data = {
            "conversation_id": conversation_id,
            "messages": [{"role": "user", "content": "Latest news about AI"}],
            "model": "perplexity/sonar",
            "stream": False,
        }
        search_response = await client.post(
            "/api/v1/chat/completions", json=search_data, headers=auth_headers
        )
        assert search_response.status_code == 200

        # 3. 检查搜索结果
        result = search_response.json()
        assert "choices" in result

        # 清理
        await client.delete(
            f"/api/v1/chat/conversations/{conversation_id}", headers=auth_headers
        )
