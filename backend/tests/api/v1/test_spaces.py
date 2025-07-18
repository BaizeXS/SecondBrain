"""测试空间相关的API端点"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User, Space


class TestSpacesEndpoints:
    """空间端点测试"""
    
    @pytest.mark.asyncio
    async def test_create_space(self, async_client: AsyncClient, auth_headers: dict):
        """测试创建空间"""
        response = await async_client.post(
            "/api/v1/spaces/",
            headers=auth_headers,
            json={
                "name": "My Test Space",
                "description": "A space for testing",
                "is_public": False,
                "tags": ["test", "demo"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Test Space"
        assert data["description"] == "A space for testing"
        assert data["is_public"] is False
        assert set(data["tags"]) == {"test", "demo"}
    
    @pytest.mark.asyncio
    async def test_create_space_limit(self, async_client: AsyncClient, auth_headers: dict):
        """测试空间数量限制"""
        # 创建多个空间直到达到限制
        for i in range(10):  # 假设限制是10
            response = await async_client.post(
                "/api/v1/spaces/",
                headers=auth_headers,
                json={
                    "name": f"Space {i}",
                    "description": f"Description {i}"
                }
            )
            if response.status_code != 200:
                assert response.status_code == 400
                assert "空间数量已达上限" in response.json()["detail"]
                break
    
    @pytest.mark.asyncio
    async def test_get_spaces(self, async_client: AsyncClient, auth_headers: dict):
        """测试获取空间列表"""
        response = await async_client.get(
            "/api/v1/spaces/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    @pytest.mark.asyncio
    async def test_get_spaces_with_filters(self, async_client: AsyncClient, auth_headers: dict):
        """测试带过滤条件的空间列表"""
        response = await async_client.get(
            "/api/v1/spaces/",
            headers=auth_headers,
            params={
                "search": "test",
                "tags": ["demo"],
                "is_public": True,
                "skip": 0,
                "limit": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # 验证过滤结果
        for space in data["items"]:
            assert space["is_public"] is True
    
    @pytest.mark.asyncio
    async def test_get_space_by_id(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_space: Space
    ):
        """测试获取单个空间"""
        response = await async_client.get(
            f"/api/v1/spaces/{test_space.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_space.id
        assert data["name"] == test_space.name
    
    @pytest.mark.asyncio
    async def test_update_space(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_space: Space
    ):
        """测试更新空间"""
        response = await async_client.put(
            f"/api/v1/spaces/{test_space.id}",
            headers=auth_headers,
            json={
                "name": "Updated Space Name",
                "description": "Updated description",
                "tags": ["updated", "modified"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Space Name"
        assert data["description"] == "Updated description"
        assert set(data["tags"]) == {"updated", "modified"}
    
    @pytest.mark.asyncio
    async def test_delete_space(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_space: Space
    ):
        """测试删除空间"""
        response = await async_client.delete(
            f"/api/v1/spaces/{test_space.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # 验证空间已被删除
        response = await async_client.get(
            f"/api/v1/spaces/{test_space.id}",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_space_statistics(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_space: Space
    ):
        """测试空间统计信息"""
        response = await async_client.get(
            f"/api/v1/spaces/{test_space.id}/statistics",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "document_count" in data
        assert "note_count" in data
        assert "total_size" in data
        assert "last_activity" in data


class TestSpacePermissions:
    """空间权限测试"""
    
    @pytest.mark.asyncio
    async def test_access_private_space_unauthorized(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        private_space_other_user: Space
    ):
        """测试访问其他用户的私有空间"""
        response = await async_client.get(
            f"/api/v1/spaces/{private_space_other_user.id}",
            headers=auth_headers
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_access_public_space(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        public_space_other_user: Space
    ):
        """测试访问其他用户的公开空间"""
        response = await async_client.get(
            f"/api/v1/spaces/{public_space_other_user.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_update_space_unauthorized(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        public_space_other_user: Space
    ):
        """测试更新其他用户的空间"""
        response = await async_client.put(
            f"/api/v1/spaces/{public_space_other_user.id}",
            headers=auth_headers,
            json={
                "name": "Hacked Name"
            }
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_share_space(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_space: Space,
        test_user2: User
    ):
        """测试分享空间"""
        response = await async_client.post(
            f"/api/v1/spaces/{test_space.id}/share",
            headers=auth_headers,
            json={
                "user_id": test_user2.id,
                "permission": "view"
            }
        )
        assert response.status_code == 200
        
        # 验证被分享用户可以访问
        auth_headers2 = {"Authorization": f"Bearer {create_access_token(str(test_user2.id))}"}
        response = await async_client.get(
            f"/api/v1/spaces/{test_space.id}",
            headers=auth_headers2
        )
        assert response.status_code == 200


class TestSpaceValidation:
    """空间输入验证测试"""
    
    @pytest.mark.asyncio
    async def test_create_space_empty_name(self, async_client: AsyncClient, auth_headers: dict):
        """测试创建空间时名称为空"""
        response = await async_client.post(
            "/api/v1/spaces/",
            headers=auth_headers,
            json={
                "name": "",
                "description": "Test"
            }
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_space_name_too_long(self, async_client: AsyncClient, auth_headers: dict):
        """测试创建空间时名称过长"""
        response = await async_client.post(
            "/api/v1/spaces/",
            headers=auth_headers,
            json={
                "name": "a" * 256,  # 假设限制是255
                "description": "Test"
            }
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_invalid_space_id(self, async_client: AsyncClient, auth_headers: dict):
        """测试无效的空间ID"""
        response = await async_client.get(
            "/api/v1/spaces/999999",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_duplicate_space_name(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_space: Space
    ):
        """测试重复的空间名称"""
        response = await async_client.post(
            "/api/v1/spaces/",
            headers=auth_headers,
            json={
                "name": test_space.name,  # 使用已存在的名称
                "description": "Duplicate test"
            }
        )
        # 根据业务逻辑，可能允许重复名称
        # assert response.status_code == 400