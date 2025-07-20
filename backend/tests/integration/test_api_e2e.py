"""
API 端到端测试。

测试完整的 API 调用链，验证各个组件的集成。
"""

import asyncio
import json

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAPIEndToEnd:
    """测试 API 端到端功能。"""

    async def test_full_api_health_check(self, client: AsyncClient):
        """测试所有 API 端点的健康状态。"""
        # 公开端点
        public_endpoints = [
            ("/api/v1/auth/login", "POST"),
            ("/api/v1/auth/register", "POST"),
        ]

        # 检查公开端点
        for endpoint, method in public_endpoints:
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "POST":
                response = await client.post(endpoint, json={})

            # 应该返回 4xx 错误（缺少参数），而不是 5xx 错误
            assert response.status_code < 500, f"{endpoint} returned server error"

    async def test_rate_limiting(self, client: AsyncClient):
        """测试速率限制功能。"""
        # 快速发送多个请求
        login_data = {"username": "testuser", "password": "wrongpass"}

        responses = []
        for _ in range(10):
            response = await client.post("/api/v1/auth/login", data=login_data)
            responses.append(response.status_code)

        # 如果速率限制没有启用，至少验证请求都是有效的（401未授权）
        # 注意：在测试环境中速率限制可能被禁用
        if not any(status == 429 for status in responses):
            # 确保所有请求都返回了401（错误的密码）
            assert all(status == 401 for status in responses), (
                f"Unexpected status codes: {set(responses)}"
            )

    async def test_concurrent_operations(
        self, client: AsyncClient, auth_headers: dict, sample_space_data: dict
    ):
        """测试并发操作的正确性。"""
        # 创建多个空间的并发请求
        tasks = []
        for i in range(5):
            space_data = {**sample_space_data, "name": f"Concurrent Space {i}"}
            task = client.post("/api/v1/spaces/", json=space_data, headers=auth_headers)
            tasks.append(task)

        # 执行并发请求
        responses = await asyncio.gather(*tasks)

        # 验证所有请求都成功
        created_ids = []
        for response in responses:
            assert response.status_code == 201  # 201 Created for new resources
            created_ids.append(response.json()["id"])

        # 验证创建的空间都是唯一的
        assert len(set(created_ids)) == 5

        # 清理
        cleanup_tasks = [
            client.delete(f"/api/v1/spaces/{space_id}", headers=auth_headers)
            for space_id in created_ids
        ]
        await asyncio.gather(*cleanup_tasks)

    async def test_error_handling_cascade(
        self, client: AsyncClient, auth_headers: dict
    ):
        """测试错误处理和级联效果。"""
        # 1. 尝试访问不存在的资源
        response = await client.get(
            "/api/v1/spaces/999999",
            headers=auth_headers,  # 使用不存在的整数ID
        )
        assert response.status_code == 404
        error_detail = response.json()
        assert "detail" in error_detail

        # 2. 尝试无效的操作
        invalid_data = {
            "name": "",  # 空名称应该被拒绝
            "description": "Test",
        }
        response = await client.post(
            "/api/v1/spaces/", json=invalid_data, headers=auth_headers
        )
        assert response.status_code == 422

        # 3. 尝试未授权的操作
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    async def test_data_consistency(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_space_data: dict,
        sample_note_data: dict,
    ):
        """测试数据一致性。"""
        # 1. 创建空间
        space_response = await client.post(
            "/api/v1/spaces/", json=sample_space_data, headers=auth_headers
        )
        assert space_response.status_code == 201
        space_id = space_response.json()["id"]

        # 2. 创建多个笔记
        note_ids = []
        for i in range(3):
            note_data = {**sample_note_data, "title": f"Note {i}", "space_id": space_id}
            note_response = await client.post(
                "/api/v1/notes/", json=note_data, headers=auth_headers
            )
            note_ids.append(note_response.json()["id"])

        # 3. 验证通过列出笔记来检查数据一致性
        notes_response = await client.get(
            f"/api/v1/notes/?space_id={space_id}", headers=auth_headers
        )
        assert notes_response.status_code == 200
        notes_data = notes_response.json()
        assert notes_data["total"] == 3

        # 4. 删除一个笔记
        await client.delete(f"/api/v1/notes/{note_ids[0]}", headers=auth_headers)

        # 5. 重新验证笔记数量
        notes_response = await client.get(
            f"/api/v1/notes/?space_id={space_id}", headers=auth_headers
        )
        notes_data = notes_response.json()
        assert notes_data["total"] == 2

        # 6. 清理
        await client.delete(f"/api/v1/spaces/{space_id}", headers=auth_headers)

    async def test_search_integration(
        self, client: AsyncClient, auth_headers: dict, mock_ai_service
    ):
        """测试搜索功能集成。"""
        # mock_ai_service 确保AI服务被正确模拟
        assert mock_ai_service is not None
        # 1. 创建测试数据
        space_response = await client.post(
            "/api/v1/spaces/",
            json={
                "name": "Search Test Space",
                "description": "Space for testing search functionality",
            },
            headers=auth_headers,
        )
        assert space_response.status_code == 201
        space_id = space_response.json()["id"]

        # 2. 创建可搜索的内容
        test_contents = [
            ("Python Programming", "Learn Python programming basics"),
            ("JavaScript Guide", "Master JavaScript development"),
            ("Python Advanced", "Advanced Python techniques"),
        ]

        for title, content in test_contents:
            note_data = {
                "title": title,
                "content": content,
                "space_id": space_id,
                "tags": ["programming", "tutorial"],
            }
            note_response = await client.post(
                "/api/v1/notes/", json=note_data, headers=auth_headers
            )
            assert note_response.status_code == 201

        # 3. 搜索特定关键词
        search_response = await client.post(
            "/api/v1/notes/search",
            json={"query": "Python", "space_ids": [space_id]},
            headers=auth_headers,
        )
        assert search_response.status_code == 200
        results = search_response.json()
        assert results["total"] == 2  # 应该找到两个 Python 相关的笔记

        # 4. 测试标签搜索
        tag_response = await client.get(
            f"/api/v1/notes/?space_id={space_id}&tags=programming", headers=auth_headers
        )
        assert tag_response.status_code == 200
        tag_results = tag_response.json()
        assert tag_results["total"] == 3

        # 5. 清理
        await client.delete(f"/api/v1/spaces/{space_id}", headers=auth_headers)

    async def test_streaming_response(
        self, client: AsyncClient, auth_headers: dict, mock_ai_service
    ):
        """测试流式响应。"""
        # mock_ai_service 确保AI服务被正确模拟
        assert mock_ai_service is not None
        # 创建对话
        conv_data = {
            "title": "Streaming Test",
            "mode": "chat",
        }
        conv_response = await client.post(
            "/api/v1/chat/conversations", json=conv_data, headers=auth_headers
        )
        conversation_id = conv_response.json()["id"]

        # 发送流式请求
        stream_data = {
            "conversation_id": conversation_id,
            "messages": [{"role": "user", "content": "Tell me a story"}],
            "model": "gpt-3.5-turbo",
            "stream": True,
        }

        async with client.stream(
            "POST", "/api/v1/chat/completions", json=stream_data, headers=auth_headers
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")

            # 读取流式数据
            chunks = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data != "[DONE]":
                        chunks.append(json.loads(data))

            assert len(chunks) > 0

    async def test_file_handling(self, client: AsyncClient, auth_headers: dict):
        """测试文件处理功能。"""
        # 创建空间
        space_response = await client.post(
            "/api/v1/spaces/", json={"name": "File Test Space"}, headers=auth_headers
        )
        assert space_response.status_code == 201
        space_id = space_response.json()["id"]

        # 测试不同类型的文件
        test_files = [
            ("text.txt", b"Plain text content", "text/plain"),
            ("doc.pdf", b"%PDF-1.4 fake pdf content", "application/pdf"),
            ("readme.md", b"# Markdown Content\n\nThis is a test", "text/markdown"),
        ]

        uploaded_ids = []
        for filename, content, content_type in test_files:
            files = {"file": (filename, content, content_type)}
            data = {"space_id": str(space_id)}
            upload_response = await client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data,
                headers=auth_headers,
            )
            assert upload_response.status_code == 201
            uploaded_ids.append(upload_response.json()["id"])

        # 验证文件列表
        docs_response = await client.get(
            f"/api/v1/documents/?space_id={space_id}", headers=auth_headers
        )
        docs = docs_response.json()
        assert docs["total"] == 3

        # 清理
        await client.delete(f"/api/v1/spaces/{space_id}", headers=auth_headers)
