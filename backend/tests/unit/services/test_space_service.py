"""Unit tests for Space Service."""

from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Space, SpaceCollaboration, User
from app.schemas.spaces import SpaceCreate, SpaceUpdate
from app.services.space_service import SpaceService


@pytest.fixture
def mock_db():
    """创建模拟数据库会话."""
    return Mock(spec=AsyncSession)


@pytest.fixture
def mock_user():
    """创建模拟用户."""
    user = Mock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_space():
    """创建模拟空间."""
    space = Mock(spec=Space)
    space.id = 1
    space.user_id = 1
    space.name = "Test Space"
    space.description = "Test Description"
    space.is_public = False
    space.document_count = 0
    space.note_count = 0
    space.total_size = 0
    return space


class TestCreateSpace:
    """测试创建空间功能."""

    @pytest.mark.asyncio
    async def test_create_space_success(self, mock_db, mock_user, mock_space):
        """测试成功创建空间."""
        # Mock CRUD
        from app import crud
        crud.crud_space.get_by_name = AsyncMock(return_value=None)
        crud.crud_space.create = AsyncMock(return_value=mock_space)

        # 创建请求数据
        space_data = SpaceCreate(
            name="New Space",
            description="New Description",
            icon="📚",
            color="#1E88E5",
            is_public=False,
            tags=[],
            meta_data={}
        )

        # 调用服务
        result = await SpaceService.create_space(mock_db, space_data, mock_user)

        # 验证
        assert result.id == 1
        assert result.name == "Test Space"
        crud.crud_space.get_by_name.assert_called_once_with(
            mock_db, name="New Space", user_id=1
        )
        crud.crud_space.create.assert_called_once_with(
            mock_db, obj_in=space_data, user_id=1
        )

    @pytest.mark.asyncio
    async def test_create_space_duplicate_name(self, mock_db, mock_user, mock_space):
        """测试创建重名空间时抛出异常."""
        # Mock CRUD - 返回已存在的空间
        from app import crud
        crud.crud_space.get_by_name = AsyncMock(return_value=mock_space)

        # 创建请求数据
        space_data = SpaceCreate(
            name="Test Space",  # 已存在的名称
            description="New Description",
            color="#1E88E5",
            icon="📚",
            tags=[],
            meta_data={}
        )

        # 调用服务并验证异常
        with pytest.raises(ValueError) as exc_info:
            await SpaceService.create_space(mock_db, space_data, mock_user)

        assert "空间名称 'Test Space' 已存在" in str(exc_info.value)
        crud.crud_space.get_by_name.assert_called_once()


class TestGetUserSpaces:
    """测试获取用户空间列表功能."""

    @pytest.mark.asyncio
    async def test_get_user_spaces(self, mock_db, mock_user):
        """测试获取用户空间列表."""
        # Mock CRUD
        from app import crud
        mock_spaces = [Mock(spec=Space) for _ in range(5)]
        crud.crud_space.get_user_spaces = AsyncMock(return_value=mock_spaces)

        # 调用服务
        result = await SpaceService.get_user_spaces(
            mock_db, mock_user, skip=0, limit=20
        )

        # 验证
        assert len(result) == 5
        crud.crud_space.get_user_spaces.assert_called_once_with(
            mock_db, user_id=1, skip=0, limit=20
        )


class TestGetSpaceById:
    """测试根据ID获取空间功能."""

    @pytest.mark.asyncio
    async def test_get_own_space(self, mock_db, mock_user, mock_space):
        """测试获取自己的空间."""
        # Mock CRUD
        from app import crud
        crud.crud_space.get = AsyncMock(return_value=mock_space)

        # 调用服务
        result = await SpaceService.get_space_by_id(mock_db, space_id=1, user=mock_user)

        # 验证
        assert result is not None
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_public_space(self, mock_db, mock_user):
        """测试获取公开空间."""
        # Mock公开空间
        public_space = Mock(spec=Space)
        public_space.id = 2
        public_space.user_id = 2  # 其他用户
        public_space.is_public = True

        # Mock CRUD
        from app import crud
        crud.crud_space.get = AsyncMock(return_value=public_space)

        # 调用服务
        result = await SpaceService.get_space_by_id(mock_db, space_id=2, user=mock_user)

        # 验证
        assert result is not None
        assert result.id == 2
        assert result.is_public is True

    @pytest.mark.asyncio
    async def test_get_space_with_collaboration(self, mock_db, mock_user):
        """测试获取有协作权限的空间."""
        # Mock空间
        collab_space = Mock(spec=Space)
        collab_space.id = 3
        collab_space.user_id = 2  # 其他用户
        collab_space.is_public = False

        # Mock协作权限
        access = Mock(spec=SpaceCollaboration)

        # Mock CRUD
        from app import crud
        crud.crud_space.get = AsyncMock(return_value=collab_space)
        crud.crud_space.get_user_access = AsyncMock(return_value=access)

        # 调用服务
        result = await SpaceService.get_space_by_id(mock_db, space_id=3, user=mock_user)

        # 验证
        assert result is not None
        assert result.id == 3
        crud.crud_space.get_user_access.assert_called_once_with(
            mock_db, space_id=3, user_id=1
        )

    @pytest.mark.asyncio
    async def test_get_space_no_access(self, mock_db, mock_user):
        """测试无权限访问空间."""
        # Mock私有空间
        private_space = Mock(spec=Space)
        private_space.id = 4
        private_space.user_id = 2  # 其他用户
        private_space.is_public = False

        # Mock CRUD
        from app import crud
        crud.crud_space.get = AsyncMock(return_value=private_space)
        crud.crud_space.get_user_access = AsyncMock(return_value=None)

        # 调用服务
        result = await SpaceService.get_space_by_id(mock_db, space_id=4, user=mock_user)

        # 验证
        assert result is None


class TestUpdateSpace:
    """测试更新空间功能."""

    @pytest.mark.asyncio
    async def test_update_space(self, mock_db, mock_space):
        """测试更新空间信息."""
        # Mock CRUD
        from app import crud
        updated_space = Mock(spec=Space)
        updated_space.name = "Updated Space"
        updated_space.description = "Updated Description"
        crud.crud_space.update = AsyncMock(return_value=updated_space)

        # 创建更新数据
        update_data = SpaceUpdate(
            name="Updated Space",
            description="Updated Description",
            color="#1E88E5",
            icon="📚",
            is_public=None,
            allow_collaboration=None,
            tags=None,
            meta_data=None
        )

        # 调用服务
        result = await SpaceService.update_space(mock_db, mock_space, update_data)

        # 验证
        assert result.name == "Updated Space"
        assert result.description == "Updated Description"
        crud.crud_space.update.assert_called_once_with(
            mock_db, db_obj=mock_space, obj_in=update_data
        )


class TestDeleteSpace:
    """测试删除空间功能."""

    @pytest.mark.asyncio
    async def test_delete_space(self, mock_db, mock_space):
        """测试删除空间."""
        # Mock CRUD
        from app import crud
        crud.crud_space.remove = AsyncMock()

        # 调用服务
        result = await SpaceService.delete_space(mock_db, mock_space)

        # 验证
        assert result is True
        crud.crud_space.remove.assert_called_once_with(mock_db, id=1)


class TestCountUserSpaces:
    """测试统计用户空间数量功能."""

    @pytest.mark.asyncio
    async def test_count_user_spaces(self, mock_db, mock_user):
        """测试统计用户空间数量."""
        # Mock CRUD
        from app import crud
        crud.crud_space.get_count = AsyncMock(return_value=10)

        # 调用服务
        result = await SpaceService.count_user_spaces(mock_db, mock_user)

        # 验证
        assert result == 10
        crud.crud_space.get_count.assert_called_once()

        # 验证查询参数
        call_args = crud.crud_space.get_count.call_args
        assert 'query' in call_args.kwargs


class TestUpdateSpaceStats:
    """测试更新空间统计信息功能."""

    @pytest.mark.asyncio
    async def test_update_space_stats(self, mock_db):
        """测试更新空间统计."""
        # Mock更新后的空间
        updated_space = Mock(spec=Space)
        updated_space.document_count = 5
        updated_space.note_count = 3
        updated_space.total_size = 1024

        # Mock CRUD
        from app import crud
        crud.crud_space.update_stats = AsyncMock(return_value=updated_space)

        # 调用服务
        result = await SpaceService.update_space_stats(
            mock_db,
            space_id=1,
            document_delta=2,
            note_delta=1,
            size_delta=512
        )

        # 验证
        assert result is not None
        assert result.document_count == 5
        assert result.note_count == 3
        assert result.total_size == 1024
        crud.crud_space.update_stats.assert_called_once_with(
            mock_db,
            space_id=1,
            document_delta=2,
            note_delta=1,
            size_delta=512
        )

    @pytest.mark.asyncio
    async def test_update_space_stats_not_found(self, mock_db):
        """测试更新不存在的空间统计."""
        # Mock CRUD
        from app import crud
        crud.crud_space.update_stats = AsyncMock(return_value=None)

        # 调用服务
        result = await SpaceService.update_space_stats(
            mock_db,
            space_id=999,
            document_delta=1
        )

        # 验证
        assert result is None
