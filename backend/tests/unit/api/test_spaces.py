"""spaces.py 的完整单元测试"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.spaces import (
    create_space,
    delete_space,
    get_space,
    get_spaces,
    update_space,
)
from app.models.models import Document, Space, User
from app.schemas.spaces import (
    SpaceCreate,
    SpaceDetail,
    SpaceListResponse,
    SpaceResponse,
    SpaceUpdate,
)


class TestCreateSpace:
    """测试创建空间功能"""

    @pytest.mark.asyncio
    async def test_create_space_success(self):
        """测试成功创建空间"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.is_premium = False

        space_data = SpaceCreate(
            name="Test Space",
            description="Test Description",
            color=None,
            icon=None,
            is_public=False,
            allow_collaboration=False,
            tags=["test", "demo"],
            meta_data=None,
        )

        # Mock SpaceService
        with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
            mock_service.count_user_spaces = AsyncMock(return_value=2)

            mock_space = MagicMock(spec=Space)
            mock_space.id = 1
            mock_space.name = "Test Space"
            mock_space.description = "Test Description"
            mock_space.color = None
            mock_space.icon = None
            mock_space.is_public = False
            mock_space.allow_collaboration = False
            mock_space.tags = ["test", "demo"]
            mock_space.meta_data = None
            mock_space.user_id = 1
            mock_space.document_count = 0
            mock_space.note_count = 0
            mock_space.total_size = 0
            mock_space.created_at = datetime.now(UTC)
            mock_space.updated_at = datetime.now(UTC)

            mock_service.create_space = AsyncMock(return_value=mock_space)

            result = await create_space(
                space_data=space_data, db=mock_db, current_user=mock_user
            )

            assert isinstance(result, SpaceResponse)
            assert result.id == 1
            assert result.name == "Test Space"
            assert result.description == "Test Description"
            assert result.is_public is False
            assert result.tags == ["test", "demo"]

    @pytest.mark.asyncio
    async def test_create_space_limit_reached(self):
        """测试达到空间数量限制"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.is_premium = False  # 非会员限制5个

        space_data = SpaceCreate(
            name="Test Space",
            description="Test Description",
            color=None,
            icon=None,
            tags=None,
            meta_data=None,
        )

        with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
            mock_service.count_user_spaces = AsyncMock(return_value=5)  # 已达限制

            with pytest.raises(HTTPException) as exc_info:
                await create_space(
                    space_data=space_data, db=mock_db, current_user=mock_user
                )

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "已达到空间数量上限" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_space_premium_user(self):
        """测试高级用户创建空间"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.is_premium = True  # 会员限制10个

        space_data = SpaceCreate(
            name="Premium Space",
            description="Premium Description",
            color=None,
            icon=None,
            tags=None,
            meta_data=None,
        )

        with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
            mock_service.count_user_spaces = AsyncMock(return_value=8)  # 未达限制

            mock_space = MagicMock(spec=Space)
            mock_space.id = 2
            mock_space.name = "Premium Space"
            mock_space.description = "Premium Description"
            mock_space.color = None
            mock_space.icon = None
            mock_space.is_public = False
            mock_space.allow_collaboration = False
            mock_space.tags = None
            mock_space.meta_data = None
            mock_space.user_id = 1
            mock_space.document_count = 0
            mock_space.note_count = 0
            mock_space.total_size = 0
            mock_space.created_at = datetime.now(UTC)
            mock_space.updated_at = datetime.now(UTC)

            mock_service.create_space = AsyncMock(return_value=mock_space)

            result = await create_space(
                space_data=space_data, db=mock_db, current_user=mock_user
            )

            assert result.id == 2
            assert result.name == "Premium Space"

    @pytest.mark.asyncio
    async def test_create_space_value_error(self):
        """测试创建空间时的值错误"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.is_premium = False

        space_data = SpaceCreate(
            name="Test Space",
            description="Test Description",
            color=None,
            icon=None,
            tags=None,
            meta_data=None,
        )

        with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
            mock_service.count_user_spaces = AsyncMock(return_value=2)
            mock_service.create_space = AsyncMock(
                side_effect=ValueError("Invalid space name")
            )

            with pytest.raises(HTTPException) as exc_info:
                await create_space(
                    space_data=space_data, db=mock_db, current_user=mock_user
                )

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid space name" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_space_general_error(self):
        """测试创建空间时的一般错误"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.is_premium = False

        space_data = SpaceCreate(
            name="Test Space",
            description="Test Description",
            color=None,
            icon=None,
            tags=None,
            meta_data=None,
        )

        with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
            mock_service.count_user_spaces = AsyncMock(return_value=2)
            mock_service.create_space = AsyncMock(
                side_effect=Exception("Database error")
            )

            with pytest.raises(HTTPException) as exc_info:
                await create_space(
                    space_data=space_data, db=mock_db, current_user=mock_user
                )

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "创建空间失败" in str(exc_info.value.detail)


class TestGetSpaces:
    """测试获取空间列表功能"""

    @pytest.mark.asyncio
    async def test_get_spaces_default(self):
        """测试默认获取空间列表"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_spaces = []
        for i in range(3):
            mock_space = MagicMock(spec=Space)
            mock_space.id = i + 1
            mock_space.name = f"Space {i + 1}"
            mock_space.description = f"Description {i + 1}"
            mock_space.color = None
            mock_space.icon = None
            mock_space.is_public = False
            mock_space.allow_collaboration = False
            mock_space.tags = [f"tag{i + 1}"]
            mock_space.meta_data = None
            mock_space.user_id = 1
            mock_space.document_count = 0
            mock_space.note_count = 0
            mock_space.total_size = 0
            mock_space.created_at = datetime.now(UTC)
            mock_space.updated_at = None
            mock_spaces.append(mock_space)

        with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
            mock_service.get_user_spaces = AsyncMock(return_value=mock_spaces)

            result = await get_spaces(
                skip=0,
                limit=20,
                search=None,
                tags=None,
                is_public=None,
                include_public=False,
                db=mock_db,
                current_user=mock_user,
            )

            assert isinstance(result, SpaceListResponse)
            assert result.total == 3
            assert len(result.spaces) == 3
            assert result.page == 1
            assert result.has_next is False

    @pytest.mark.asyncio
    async def test_get_spaces_with_search(self):
        """测试带搜索条件的空间列表"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_spaces = []
        for i in range(3):
            mock_space = MagicMock(spec=Space)
            mock_space.id = i + 1
            mock_space.name = f"Space {i + 1}" if i != 1 else "Test Space"
            mock_space.description = f"Description {i + 1}"
            mock_space.color = None
            mock_space.icon = None
            mock_space.is_public = False
            mock_space.allow_collaboration = False
            mock_space.tags = None
            mock_space.meta_data = None
            mock_space.user_id = 1
            mock_space.document_count = 0
            mock_space.note_count = 0
            mock_space.total_size = 0
            mock_space.created_at = datetime.now(UTC)
            mock_space.updated_at = None
            mock_spaces.append(mock_space)

        with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
            mock_service.get_user_spaces = AsyncMock(return_value=mock_spaces)

            result = await get_spaces(
                skip=0,
                limit=20,
                search="Test",
                tags=None,
                is_public=None,
                include_public=False,
                db=mock_db,
                current_user=mock_user,
            )

            assert result.total == 1
            assert len(result.spaces) == 1
            assert result.spaces[0].name == "Test Space"

    @pytest.mark.asyncio
    async def test_get_spaces_with_tags_filter(self):
        """测试带标签过滤的空间列表"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_spaces = []
        for i in range(3):
            mock_space = MagicMock(spec=Space)
            mock_space.id = i + 1
            mock_space.name = f"Space {i + 1}"
            mock_space.description = f"Description {i + 1}"
            mock_space.color = None
            mock_space.icon = None
            mock_space.is_public = False
            mock_space.allow_collaboration = False
            mock_space.tags = ["common", f"tag{i + 1}"] if i < 2 else ["other"]
            mock_space.meta_data = None
            mock_space.user_id = 1
            mock_space.document_count = 0
            mock_space.note_count = 0
            mock_space.total_size = 0
            mock_space.created_at = datetime.now(UTC)
            mock_space.updated_at = None
            mock_spaces.append(mock_space)

        with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
            mock_service.get_user_spaces = AsyncMock(return_value=mock_spaces)

            result = await get_spaces(
                skip=0,
                limit=20,
                search=None,
                tags=["common"],
                is_public=None,
                include_public=False,
                db=mock_db,
                current_user=mock_user,
            )

            assert result.total == 2
            assert len(result.spaces) == 2

    @pytest.mark.asyncio
    async def test_get_spaces_include_public(self):
        """测试包含公开空间的列表"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_spaces = []
        for i in range(5):
            mock_space = MagicMock(spec=Space)
            mock_space.id = i + 1
            mock_space.name = f"Space {i + 1}"
            mock_space.description = f"Description {i + 1}"
            mock_space.color = None
            mock_space.icon = None
            mock_space.is_public = i % 2 == 0  # 偶数为公开
            mock_space.allow_collaboration = False
            mock_space.tags = None
            mock_space.meta_data = None
            mock_space.user_id = 1 if i < 3 else 2  # 前3个是当前用户的
            mock_space.document_count = 0
            mock_space.note_count = 0
            mock_space.total_size = 0
            mock_space.created_at = datetime.now(UTC)
            mock_space.updated_at = None
            mock_spaces.append(mock_space)

        with patch("app.api.v1.endpoints.spaces.crud") as mock_crud:
            mock_crud.crud_space.get_user_spaces = AsyncMock(return_value=mock_spaces)

            result = await get_spaces(
                skip=0,
                limit=20,
                search=None,
                tags=None,
                is_public=True,  # 只要公开的
                include_public=True,
                db=mock_db,
                current_user=mock_user,
            )

            assert len([s for s in result.spaces if s.is_public]) == len(result.spaces)

    @pytest.mark.asyncio
    async def test_get_spaces_pagination(self):
        """测试空间列表分页"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_spaces = []
        for i in range(25):  # 创建25个空间
            mock_space = MagicMock(spec=Space)
            mock_space.id = i + 1
            mock_space.name = f"Space {i + 1}"
            mock_space.description = f"Description {i + 1}"
            mock_space.color = None
            mock_space.icon = None
            mock_space.is_public = False
            mock_space.allow_collaboration = False
            mock_space.tags = None
            mock_space.meta_data = None
            mock_space.user_id = 1
            mock_space.document_count = 0
            mock_space.note_count = 0
            mock_space.total_size = 0
            mock_space.created_at = datetime.now(UTC)
            mock_space.updated_at = None
            mock_spaces.append(mock_space)

        with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
            mock_service.get_user_spaces = AsyncMock(return_value=mock_spaces)

            result = await get_spaces(
                skip=20,
                limit=10,
                search=None,
                tags=None,
                is_public=None,
                include_public=False,
                db=mock_db,
                current_user=mock_user,
            )

            assert result.total == 25
            assert result.page == 3  # skip=20, limit=10, 所以是第3页
            assert result.has_next is False  # 25个总共，跳过20个，只剩5个


class TestGetSpace:
    """测试获取单个空间功能"""

    @pytest.mark.asyncio
    async def test_get_space_success(self):
        """测试成功获取空间详情"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.name = "Test Space"
        mock_space.description = "Test Description"
        mock_space.color = None
        mock_space.icon = None
        mock_space.is_public = False
        mock_space.allow_collaboration = False
        mock_space.tags = ["test"]
        mock_space.meta_data = None
        mock_space.user_id = 1
        mock_space.document_count = 5
        mock_space.note_count = 10
        mock_space.total_size = 1024000
        mock_space.created_at = datetime.now(UTC)
        mock_space.updated_at = datetime.now(UTC)
        mock_space.documents = []
        mock_space.notes = []

        with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
            mock_service.get_space_by_id = AsyncMock(return_value=mock_space)

            result = await get_space(space_id=1, db=mock_db, current_user=mock_user)

            assert isinstance(result, SpaceDetail)
            assert result.id == 1
            assert result.name == "Test Space"
            assert result.document_count == 5
            assert result.note_count == 10

    @pytest.mark.asyncio
    async def test_get_space_not_found(self):
        """测试获取不存在的空间"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
            mock_service.get_space_by_id = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_space(space_id=999, db=mock_db, current_user=mock_user)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "空间不存在或无权访问" in str(exc_info.value.detail)


class TestUpdateSpace:
    """测试更新空间功能"""

    @pytest.mark.asyncio
    async def test_update_space_success(self):
        """测试成功更新空间（所有者）"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1  # 当前用户是所有者
        mock_space.name = "Old Name"

        space_update = SpaceUpdate(
            name="New Name",
            description="New Description",
            color=None,
            icon=None,
            is_public=None,
            allow_collaboration=None,
            tags=["new", "updated"],
            meta_data=None,
        )

        mock_updated_space = MagicMock(spec=Space)
        mock_updated_space.id = 1
        mock_updated_space.name = "New Name"
        mock_updated_space.description = "New Description"
        mock_updated_space.color = None
        mock_updated_space.icon = None
        mock_updated_space.is_public = False
        mock_updated_space.allow_collaboration = False
        mock_updated_space.tags = ["new", "updated"]
        mock_updated_space.meta_data = None
        mock_updated_space.user_id = 1
        mock_updated_space.document_count = 0
        mock_updated_space.note_count = 0
        mock_updated_space.total_size = 0
        mock_updated_space.created_at = datetime.now(UTC)
        mock_updated_space.updated_at = datetime.now(UTC)

        with patch("app.api.v1.endpoints.spaces.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)

            with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
                mock_service.update_space = AsyncMock(return_value=mock_updated_space)

                result = await update_space(
                    space_id=1,
                    space_data=space_update,
                    db=mock_db,
                    current_user=mock_user,
                )

                assert isinstance(result, SpaceResponse)
                assert result.name == "New Name"
                assert result.description == "New Description"
                assert result.tags == ["new", "updated"]

    @pytest.mark.asyncio
    async def test_update_space_with_edit_permission(self):
        """测试有编辑权限的用户更新空间"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 2  # 不是所有者

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1  # 其他用户是所有者

        mock_access = MagicMock()
        mock_access.can_edit = True  # 有编辑权限

        space_update = SpaceUpdate(
            name="Updated by Editor",
            description=None,
            color=None,
            icon=None,
            is_public=None,
            allow_collaboration=None,
            tags=None,
            meta_data=None,
        )

        mock_updated_space = MagicMock(spec=Space)
        mock_updated_space.id = 1
        mock_updated_space.name = "Updated by Editor"
        mock_updated_space.description = "Test Description"
        mock_updated_space.color = None
        mock_updated_space.icon = None
        mock_updated_space.is_public = False
        mock_updated_space.allow_collaboration = False
        mock_updated_space.tags = None
        mock_updated_space.meta_data = None
        mock_updated_space.user_id = 1
        mock_updated_space.document_count = 0
        mock_updated_space.note_count = 0
        mock_updated_space.total_size = 0
        mock_updated_space.created_at = datetime.now(UTC)
        mock_updated_space.updated_at = datetime.now(UTC)

        with patch("app.api.v1.endpoints.spaces.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_space.get_user_access = AsyncMock(return_value=mock_access)

            with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
                mock_service.update_space = AsyncMock(return_value=mock_updated_space)

                result = await update_space(
                    space_id=1,
                    space_data=space_update,
                    db=mock_db,
                    current_user=mock_user,
                )

                assert result.name == "Updated by Editor"

    @pytest.mark.asyncio
    async def test_update_space_not_found(self):
        """测试更新不存在的空间"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        space_update = SpaceUpdate(
            name="New Name",
            description=None,
            color=None,
            icon=None,
            is_public=None,
            allow_collaboration=None,
            tags=None,
            meta_data=None,
        )

        with patch("app.api.v1.endpoints.spaces.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await update_space(
                    space_id=999,
                    space_data=space_update,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "空间不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_space_no_permission(self):
        """测试无权限更新空间"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 2

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1  # 其他用户是所有者

        mock_access = MagicMock()
        mock_access.can_edit = False  # 没有编辑权限

        space_update = SpaceUpdate(
            name="Unauthorized Update",
            description=None,
            color=None,
            icon=None,
            is_public=None,
            allow_collaboration=None,
            tags=None,
            meta_data=None,
        )

        with patch("app.api.v1.endpoints.spaces.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_space.get_user_access = AsyncMock(return_value=mock_access)

            with pytest.raises(HTTPException) as exc_info:
                await update_space(
                    space_id=1,
                    space_data=space_update,
                    db=mock_db,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "无权编辑此空间" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_space_error(self):
        """测试更新空间时发生错误"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        space_update = SpaceUpdate(
            name="Error Update",
            description=None,
            color=None,
            icon=None,
            is_public=None,
            allow_collaboration=None,
            tags=None,
            meta_data=None,
        )

        with patch("app.api.v1.endpoints.spaces.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)

            with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
                mock_service.update_space = AsyncMock(
                    side_effect=Exception("Database error")
                )

                with pytest.raises(HTTPException) as exc_info:
                    await update_space(
                        space_id=1,
                        space_data=space_update,
                        db=mock_db,
                        current_user=mock_user,
                    )

                assert (
                    exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                assert "更新空间失败" in str(exc_info.value.detail)


class TestDeleteSpace:
    """测试删除空间功能"""

    @pytest.mark.asyncio
    async def test_delete_space_success(self):
        """测试成功删除空间（无关联数据）"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1  # 当前用户是所有者

        with patch("app.api.v1.endpoints.spaces.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_document.get_by_space = AsyncMock(return_value=[])  # 无文档

            with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
                mock_service.delete_space = AsyncMock(return_value=None)

                # 应该成功，没有返回值
                await delete_space(
                    space_id=1, force=False, db=mock_db, current_user=mock_user
                )

                mock_service.delete_space.assert_called_once_with(mock_db, mock_space)

    @pytest.mark.asyncio
    async def test_delete_space_with_documents_no_force(self):
        """测试删除有文档的空间（非强制）"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        mock_document = MagicMock(spec=Document)
        mock_document.id = 1

        with patch("app.api.v1.endpoints.spaces.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_document.get_by_space = AsyncMock(
                return_value=[mock_document]
            )  # 有文档

            with pytest.raises(HTTPException) as exc_info:
                await delete_space(
                    space_id=1, force=False, db=mock_db, current_user=mock_user
                )

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "空间中还有文档" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_space_with_documents_force(self):
        """测试强制删除有文档的空间"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        with patch("app.api.v1.endpoints.spaces.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            # force=True时不检查文档

            with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
                mock_service.delete_space = AsyncMock(return_value=None)

                await delete_space(
                    space_id=1, force=True, db=mock_db, current_user=mock_user
                )

                mock_service.delete_space.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_space_not_found(self):
        """测试删除不存在的空间"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        with patch("app.api.v1.endpoints.spaces.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await delete_space(
                    space_id=999, force=False, db=mock_db, current_user=mock_user
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "空间不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_space_no_permission(self):
        """测试无权限删除空间"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 2

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1  # 其他用户是所有者

        with patch("app.api.v1.endpoints.spaces.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)

            with pytest.raises(HTTPException) as exc_info:
                await delete_space(
                    space_id=1, force=False, db=mock_db, current_user=mock_user
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "无权删除此空间" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_space_error(self):
        """测试删除空间时发生错误"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_space = MagicMock(spec=Space)
        mock_space.id = 1
        mock_space.user_id = 1

        with patch("app.api.v1.endpoints.spaces.crud") as mock_crud:
            mock_crud.crud_space.get = AsyncMock(return_value=mock_space)
            mock_crud.crud_document.get_by_space = AsyncMock(return_value=[])

            with patch("app.api.v1.endpoints.spaces.SpaceService") as mock_service:
                mock_service.delete_space = AsyncMock(
                    side_effect=Exception("Database error")
                )

                with pytest.raises(HTTPException) as exc_info:
                    await delete_space(
                        space_id=1, force=False, db=mock_db, current_user=mock_user
                    )

                assert (
                    exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                assert "删除空间失败" in str(exc_info.value.detail)
