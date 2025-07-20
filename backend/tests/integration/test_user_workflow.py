"""
完整用户工作流集成测试。

测试用户从注册到使用各项功能的完整流程。
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestCompleteUserWorkflow:
    """测试完整的用户工作流。"""

    async def test_knowledge_management_workflow(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_space_data: dict,
        sample_document_data: dict,
        sample_note_data: dict,
        mock_ai_service,
    ):
        """测试知识管理完整流程。"""
        # 1. 创建知识空间
        space_response = await client.post(
            "/api/v1/spaces/", json=sample_space_data, headers=auth_headers
        )
        assert space_response.status_code == 201
        space = space_response.json()
        space_id = space["id"]

        # 2. 上传文档到空间
        # 模拟文件上传
        files = {
            "file": (
                "test.txt",
                b"This is test content for the document.",
                "text/plain",
            )
        }
        data = {"space_id": str(space_id)}
        upload_response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=auth_headers,
        )
        assert upload_response.status_code == 201
        document = upload_response.json()
        document_id = document["id"]

        # 3. 创建笔记
        note_data = {**sample_note_data, "space_id": space_id}
        note_response = await client.post(
            "/api/v1/notes/", json=note_data, headers=auth_headers
        )
        assert note_response.status_code == 201
        note = note_response.json()
        note_id = note["id"]

        # 4. 更新笔记内容
        update_note_data = {"content": "Updated content with more information."}
        update_response = await client.put(
            f"/api/v1/notes/{note_id}", json=update_note_data, headers=auth_headers
        )
        assert update_response.status_code == 200
        updated_note = update_response.json()
        assert updated_note["content"] == update_note_data["content"]

        # 5. 添加文档标注
        annotation_data = {
            "document_id": document_id,
            "type": "highlight",
            "content": "Important section",
            "page_number": 1,
            "position_data": {"x": 100, "y": 200},
            "color": "#FFFF00",
        }
        annotation_response = await client.post(
            "/api/v1/annotations/", json=annotation_data, headers=auth_headers
        )
        assert annotation_response.status_code == 201
        annotation = annotation_response.json()

        # 6. 搜索文档
        search_response = await client.get(
            f"/api/v1/documents/?space_id={space_id}&search=test",
            headers=auth_headers,
        )
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert search_results["total"] > 0
        assert len(search_results["documents"]) > 0

        # 7. 获取空间统计信息
        # TODO: 空间统计端点尚未实现
        # stats_response = await client.get(
        #     f"/api/v1/spaces/{space_id}/stats", headers=auth_headers
        # )
        # assert stats_response.status_code == 200
        # stats = stats_response.json()
        # assert stats["document_count"] >= 1
        # assert stats["note_count"] >= 1

        # 8. 导出空间内容
        # 注意：空间导出只支持 PDF 格式
        export_data = {
            "space_id": space_id,
            "format": "pdf",
            "include_documents": True,
            "include_notes": True,
            "include_content": True,
        }
        export_response = await client.post(
            "/api/v1/export/space",
            json=export_data,
            headers=auth_headers,
        )
        assert export_response.status_code == 200

        # 9. 清理：删除空间（级联删除所有内容）
        delete_response = await client.delete(
            f"/api/v1/spaces/{space_id}?force=true", headers=auth_headers
        )
        assert delete_response.status_code == 204

    async def test_ai_chat_workflow(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_space_data: dict,
        mock_ai_service,
    ):
        """测试 AI 聊天工作流。"""
        # 1. 创建空间用于聊天
        space_response = await client.post(
            "/api/v1/spaces/", json=sample_space_data, headers=auth_headers
        )
        space_id = space_response.json()["id"]

        # 2. 创建对话
        conversation_data = {
            "title": "AI Chat Test",
            "mode": "chat",
            "model": "gpt-3.5-turbo",
            "space_id": space_id,
        }
        conv_response = await client.post(
            "/api/v1/chat/conversations", json=conversation_data, headers=auth_headers
        )
        assert conv_response.status_code == 201
        conversation = conv_response.json()
        conversation_id = conversation["id"]

        # 3. 发送聊天消息
        chat_data = {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, AI! Tell me about knowledge management.",
                }
            ],
            "model": "gpt-3.5-turbo",
            "stream": False,
        }
        chat_response = await client.post(
            "/api/v1/chat/completions", json=chat_data, headers=auth_headers
        )
        assert chat_response.status_code == 200
        chat_result = chat_response.json()
        assert "choices" in chat_result
        assert len(chat_result["choices"]) > 0

        # 4. 获取对话历史
        history_response = await client.get(
            f"/api/v1/chat/conversations/{conversation_id}", headers=auth_headers
        )
        assert history_response.status_code == 200
        conversation_with_messages = history_response.json()
        assert "messages" in conversation_with_messages
        assert len(conversation_with_messages["messages"]) >= 2  # 用户消息和 AI 回复

        # 5. 测试流式响应
        stream_data = {
            "conversation_id": conversation_id,
            "messages": [{"role": "user", "content": "Give me a brief summary."}],
            "model": "gpt-3.5-turbo",
            "stream": True,
        }
        stream_response = await client.post(
            "/api/v1/chat/completions", json=stream_data, headers=auth_headers
        )
        assert stream_response.status_code == 200
        # 流式响应会返回 text/event-stream

        # 6. 切换到搜索模式
        search_chat_data = {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "role": "user",
                    "content": "Search for information about Python programming.",
                }
            ],
            "model": "perplexity/sonar",
            "mode": "search",
        }
        search_response = await client.post(
            "/api/v1/chat/completions", json=search_chat_data, headers=auth_headers
        )
        assert search_response.status_code == 200

        # 7. 清理
        await client.delete(f"/api/v1/spaces/{space_id}", headers=auth_headers)

    @pytest.mark.skip(reason="邀请协作者端点尚未实现")
    async def test_collaboration_workflow(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_space_data: dict,
        db_session: AsyncSession,
    ):
        """测试协作工作流。"""
        # 1. 创建协作空间
        collab_space_data = {
            **sample_space_data,
            "name": "Collaboration Space",
            "is_public": True,
        }
        space_response = await client.post(
            "/api/v1/spaces/", json=collab_space_data, headers=auth_headers
        )
        space = space_response.json()
        space_id = space["id"]

        # 2. 创建第二个用户
        from app.crud.user import crud_user
        from app.schemas.users import UserCreate

        user2_data = UserCreate(
            username="collaborator",
            email="collab@example.com",
            full_name="Collaborator User",
            password="collabpass123",
        )
        user2 = await crud_user.create(db_session, obj_in=user2_data)
        await db_session.commit()

        # 3. 第二个用户登录
        # 使用表单数据格式
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": "collaborator", "password": "collabpass123"},
        )
        assert login_response.status_code == 200
        user2_token = login_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # 4. 邀请协作者
        invite_data = {"user_email": "collab@example.com", "role": "editor"}
        invite_response = await client.post(
            f"/api/v1/spaces/{space_id}/invite", json=invite_data, headers=auth_headers
        )
        assert invite_response.status_code == 200

        # 5. 协作者访问空间
        access_response = await client.get(
            f"/api/v1/spaces/{space_id}", headers=user2_headers
        )
        assert access_response.status_code == 200

        # 6. 协作者添加文档
        files = {"file": ("collab.txt", b"Collaborative content", "text/plain")}
        data = {"space_id": str(space_id)}
        collab_upload = await client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=user2_headers,
        )
        assert collab_upload.status_code == 200

        # 7. 原用户查看协作内容
        docs_response = await client.get(
            f"/api/v1/documents/?space_id={space_id}", headers=auth_headers
        )
        assert docs_response.status_code == 200
        docs = docs_response.json()
        assert docs["total"] >= 1

        # 8. 清理
        await client.delete(f"/api/v1/spaces/{space_id}", headers=auth_headers)

    async def test_agent_workflow(
        self, client: AsyncClient, auth_headers: dict, mock_ai_service
    ):
        """测试 AI 代理工作流。"""
        # 1. 获取可用代理列表
        agents_response = await client.get("/api/v1/agents/", headers=auth_headers)
        assert agents_response.status_code == 200
        agents = agents_response.json()
        assert len(agents["agents"]) > 0

        # 2. 执行深度研究代理
        research_data = {"query": "Knowledge Management Systems", "mode": "general"}
        research_response = await client.post(
            "/api/v1/agents/deep-research", json=research_data, headers=auth_headers
        )
        assert research_response.status_code == 200
        research_result = research_response.json()
        assert "space_id" in research_result
        assert "research_id" in research_result

        # 3. 验证研究结果
        space_id = research_result["space_id"]
        assert space_id is not None
        assert research_result["status"] == "completed"
        assert "result" in research_result  # DeepResearchResponse 返回 result 字段
