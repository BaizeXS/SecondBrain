"""
空间管理工作流集成测试。

测试知识空间的完整生命周期管理。
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSpacesWorkflow:
    """测试空间管理工作流。"""

    async def test_space_lifecycle(
        self, client: AsyncClient, auth_headers: dict, sample_space_data: dict
    ):
        """测试空间的完整生命周期。"""
        # 1. 创建空间
        create_response = await client.post(
            "/api/v1/spaces/", json=sample_space_data, headers=auth_headers
        )
        assert create_response.status_code == 201
        space = create_response.json()
        space_id = space["id"]
        assert space["name"] == sample_space_data["name"]

        # 2. 获取空间列表
        list_response = await client.get("/api/v1/spaces/", headers=auth_headers)
        assert list_response.status_code == 200
        spaces = list_response.json()
        assert spaces["total"] >= 1
        assert any(s["id"] == space_id for s in spaces["spaces"])

        # 3. 获取单个空间详情
        detail_response = await client.get(
            f"/api/v1/spaces/{space_id}", headers=auth_headers
        )
        assert detail_response.status_code == 200
        space_detail = detail_response.json()
        assert space_detail["id"] == space_id

        # 4. 更新空间
        update_data = {
            "name": "Updated Space Name",
            "description": "Updated description",
            "color": "#00FF00",
        }
        update_response = await client.put(
            f"/api/v1/spaces/{space_id}", json=update_data, headers=auth_headers
        )
        assert update_response.status_code == 200
        updated_space = update_response.json()
        assert updated_space["name"] == update_data["name"]
        assert updated_space["description"] == update_data["description"]

        # 5. 获取空间统计
        # TODO: 空间统计端点尚未实现
        # stats_response = await client.get(
        #     f"/api/v1/spaces/{space_id}/stats", headers=auth_headers
        # )
        # assert stats_response.status_code == 200
        # stats = stats_response.json()
        # assert "document_count" in stats
        # assert "note_count" in stats
        # assert "total_size" in stats

        # 6. 删除空间
        delete_response = await client.delete(
            f"/api/v1/spaces/{space_id}", headers=auth_headers
        )
        assert delete_response.status_code == 204

        # 7. 验证空间已删除
        verify_response = await client.get(
            f"/api/v1/spaces/{space_id}", headers=auth_headers
        )
        assert verify_response.status_code == 404

    async def test_space_permissions(
        self, client: AsyncClient, auth_headers: dict, sample_space_data: dict
    ):
        """测试空间权限管理。"""
        # 1. 创建私有空间
        private_space_data = {**sample_space_data, "is_public": False}
        create_response = await client.post(
            "/api/v1/spaces/", json=private_space_data, headers=auth_headers
        )
        space_id = create_response.json()["id"]

        # 2. 未授权访问（无token）
        unauth_response = await client.get(f"/api/v1/spaces/{space_id}")
        assert unauth_response.status_code == 401

        # 3. 创建公开空间
        public_space_data = {
            **sample_space_data,
            "name": "Public Space",
            "is_public": True,
        }
        public_response = await client.post(
            "/api/v1/spaces/", json=public_space_data, headers=auth_headers
        )
        public_space_id = public_response.json()["id"]

        # TODO: 测试其他用户访问公开空间的场景

        # 清理
        await client.delete(f"/api/v1/spaces/{space_id}", headers=auth_headers)
        await client.delete(f"/api/v1/spaces/{public_space_id}", headers=auth_headers)

    @pytest.mark.skip(reason="空间笔记移动功能暂时存在问题")
    async def test_space_content_management(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_space_data: dict,
        sample_note_data: dict,
    ):
        """测试空间内容管理。"""
        # 1. 创建空间
        space_response = await client.post(
            "/api/v1/spaces/", json=sample_space_data, headers=auth_headers
        )
        space_id = space_response.json()["id"]

        # 2. 创建多个笔记
        note_ids = []
        for i in range(3):
            note_data = {
                **sample_note_data,
                "title": f"Note {i + 1}",
                "space_id": space_id,
            }
            note_response = await client.post(
                "/api/v1/notes/", json=note_data, headers=auth_headers
            )
            assert note_response.status_code == 201
            note_ids.append(note_response.json()["id"])

        # 3. 获取空间内的笔记
        notes_response = await client.get(
            f"/api/v1/notes/?space_id={space_id}", headers=auth_headers
        )
        assert notes_response.status_code == 200
        notes = notes_response.json()
        assert notes["total"] == 3

        # 4. 移动笔记到另一个空间
        new_space_data = {**sample_space_data, "name": "New Space"}
        new_space_response = await client.post(
            "/api/v1/spaces/", json=new_space_data, headers=auth_headers
        )
        new_space_id = new_space_response.json()["id"]

        move_response = await client.put(
            f"/api/v1/notes/{note_ids[0]}",
            json={"space_id": new_space_id},
            headers=auth_headers,
        )
        assert move_response.status_code == 200

        # 5. 验证笔记已移动
        old_space_notes = await client.get(
            f"/api/v1/notes/?space_id={space_id}", headers=auth_headers
        )
        assert old_space_notes.json()["total"] == 2

        new_space_notes = await client.get(
            f"/api/v1/notes/?space_id={new_space_id}", headers=auth_headers
        )
        assert new_space_notes.json()["total"] == 1

        # 清理
        await client.delete(f"/api/v1/spaces/{space_id}", headers=auth_headers)
        await client.delete(f"/api/v1/spaces/{new_space_id}", headers=auth_headers)

    async def test_space_search_and_filter(
        self, client: AsyncClient, auth_headers: dict, sample_space_data: dict
    ):
        """测试空间搜索和过滤功能。"""
        # 1. 创建多个空间
        space_names = ["Research Space", "Personal Notes", "Work Projects"]
        space_ids = []

        for name in space_names:
            space_data = {**sample_space_data, "name": name}
            response = await client.post(
                "/api/v1/spaces/", json=space_data, headers=auth_headers
            )
            space_ids.append(response.json()["id"])

        # 2. 搜索空间
        search_response = await client.get(
            "/api/v1/spaces/?search=Research", headers=auth_headers
        )
        assert search_response.status_code == 200
        results = search_response.json()
        assert results["total"] >= 1
        assert any("Research" in s["name"] for s in results["spaces"])

        # 3. 按标签过滤
        # 更新一个空间添加标签
        tag_update = {"tags": ["work", "important"]}
        await client.put(
            f"/api/v1/spaces/{space_ids[2]}", json=tag_update, headers=auth_headers
        )

        tagged_response = await client.get(
            "/api/v1/spaces/?tags=work", headers=auth_headers
        )
        assert tagged_response.status_code == 200
        tagged_results = tagged_response.json()
        assert any("work" in s.get("tags", []) for s in tagged_results["spaces"])

        # 清理
        for space_id in space_ids:
            await client.delete(f"/api/v1/spaces/{space_id}", headers=auth_headers)
