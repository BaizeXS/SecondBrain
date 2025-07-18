"""Unit tests for user endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.users import (
    change_password,
    delete_account,
    get_current_user_info,
    get_user_stats,
    update_current_user,
)
from app.core.auth import AuthService
from app.core.config import settings
from app.models.models import User
from app.schemas.auth import ChangePasswordRequest
from app.schemas.users import UserResponse, UserStats, UserUpdate


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.hashed_password = "hashed_password"
    user.is_active = True
    user.is_premium = False
    user.full_name = "Test User"
    user.avatar_url = None
    user.preferences = {}
    user.is_verified = False
    user.daily_usage = 10
    user.last_reset_date = None
    user.last_login = None

    from datetime import UTC, datetime

    user.created_at = datetime.now(UTC)
    user.updated_at = datetime.now(UTC)
    return user


class TestGetCurrentUserInfo:
    """Test get current user info endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_info_success(self, mock_user):
        """Test successful retrieval of user info."""
        # Act
        result = await get_current_user_info(mock_user)

        # Assert
        assert isinstance(result, UserResponse)
        assert result.username == "testuser"
        assert result.email == "test@example.com"


class TestUpdateCurrentUser:
    """Test update current user endpoint."""

    @pytest.mark.asyncio
    async def test_update_user_success(self, mock_db, mock_user):
        """Test successful user update."""
        # Arrange
        user_update = UserUpdate(
            full_name="Updated Name",
            avatar_url="https://example.com/avatar.jpg",
            preferences=None
        )
        from datetime import UTC, datetime

        updated_user = MagicMock(spec=User)
        updated_user.id = 1
        updated_user.username = "testuser"
        updated_user.email = "test@example.com"
        updated_user.full_name = "Updated Name"
        updated_user.avatar_url = "https://example.com/avatar.jpg"
        updated_user.preferences = {}
        updated_user.is_active = True
        updated_user.is_premium = False
        updated_user.is_verified = False
        updated_user.daily_usage = 10
        updated_user.last_reset_date = None
        updated_user.last_login = None
        updated_user.created_at = datetime.now(UTC)
        updated_user.updated_at = datetime.now(UTC)

        with patch("app.crud.crud_user.update", return_value=updated_user):
            # Act
            result = await update_current_user(user_update, mock_db, mock_user)

            # Assert
            assert isinstance(result, UserResponse)

    @pytest.mark.asyncio
    async def test_update_user_error(self, mock_db, mock_user):
        """Test user update with database error."""
        # Arrange
        user_update = UserUpdate(
            full_name="Updated Name",
            avatar_url=None,
            preferences=None
        )

        with patch("app.crud.crud_user.update", side_effect=Exception("DB Error")):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await update_current_user(user_update, mock_db, mock_user)

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "更新用户信息失败" in str(exc_info.value.detail)


class TestChangePassword:
    """Test change password endpoint."""

    @pytest.mark.asyncio
    async def test_change_password_success(self, mock_db, mock_user):
        """Test successful password change."""
        # Arrange
        password_data = ChangePasswordRequest(
            old_password="oldpass", new_password="NewSecurePass123"
        )

        with (
            patch.object(AuthService, "verify_password", return_value=True),
            patch.object(AuthService, "get_password_hash", return_value="new_hashed"),
            patch("app.crud.crud_user.update", return_value=mock_user),
        ):
            # Act
            result = await change_password(password_data, mock_db, mock_user)

            # Assert
            assert result is None  # 204 No Content

    @pytest.mark.asyncio
    async def test_change_password_wrong_old(self, mock_db, mock_user):
        """Test password change with wrong old password."""
        # Arrange
        password_data = ChangePasswordRequest(
            old_password="wrongpass", new_password="NewSecurePass123"
        )

        with patch.object(AuthService, "verify_password", return_value=False):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await change_password(password_data, mock_db, mock_user)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "当前密码错误" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_change_password_weak_new(self, mock_db, mock_user):
        """Test password change with weak new password."""
        # Arrange
        password_data = ChangePasswordRequest(
            old_password="oldpass",
            new_password="weak123",  # Valid for schema but weak for validation
        )

        with patch.object(AuthService, "verify_password", return_value=True):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await change_password(password_data, mock_db, mock_user)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "密码长度至少8位" in str(exc_info.value.detail)


class TestGetUserStats:
    """Test get user stats endpoint."""

    @pytest.mark.asyncio
    async def test_get_stats_success(self, mock_db, mock_user):
        """Test successful stats retrieval."""
        # Arrange
        mock_result = MagicMock()
        mock_stats = MagicMock()
        mock_stats.space_count = 3
        mock_stats.document_count = 10
        mock_stats.conversation_count = 5
        mock_stats.note_count = 15
        mock_stats.total_storage = 1024 * 1024 * 100  # 100MB
        mock_result.first.return_value = mock_stats
        mock_db.execute.return_value = mock_result

        # Act
        result = await get_user_stats(mock_db, mock_user)

        # Assert
        assert isinstance(result, UserStats)
        assert result.total_spaces == 3
        assert result.total_documents == 10
        assert result.total_conversations == 5
        assert result.total_notes == 15
        assert result.storage_used == 1024 * 1024 * 100

    @pytest.mark.asyncio
    async def test_get_stats_no_data(self, mock_db, mock_user):
        """Test stats retrieval with no data."""
        # Arrange
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result

        # Act
        result = await get_user_stats(mock_db, mock_user)

        # Assert
        assert isinstance(result, UserStats)
        assert result.total_spaces == 0
        assert result.total_documents == 0
        assert result.total_conversations == 0
        assert result.total_notes == 0
        assert result.storage_used == 0

    @pytest.mark.asyncio
    async def test_get_stats_premium_user(self, mock_db, mock_user):
        """Test stats for premium user."""
        # Arrange
        mock_user.is_premium = True
        mock_result = MagicMock()
        mock_stats = MagicMock()
        mock_stats.space_count = 5
        mock_stats.document_count = 20
        mock_stats.conversation_count = 10
        mock_stats.note_count = 30
        mock_stats.total_storage = 0
        mock_result.first.return_value = mock_stats
        mock_db.execute.return_value = mock_result

        # Act
        result = await get_user_stats(mock_db, mock_user)

        # Assert
        assert result.usage_limit == settings.RATE_LIMIT_PREMIUM_USER


class TestDeleteAccount:
    """Test delete account endpoint."""

    @pytest.mark.asyncio
    async def test_delete_account_success(self, mock_db, mock_user):
        """Test successful account deletion."""
        # Arrange
        password = "correct_password"

        with (
            patch.object(AuthService, "verify_password", return_value=True),
            patch("app.crud.crud_user.remove", return_value=None),
        ):
            # Act
            result = await delete_account(password, mock_db, mock_user)

            # Assert
            assert result is None  # 204 No Content

    @pytest.mark.asyncio
    async def test_delete_account_wrong_password(self, mock_db, mock_user):
        """Test account deletion with wrong password."""
        # Arrange
        password = "wrong_password"

        with patch.object(AuthService, "verify_password", return_value=False):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await delete_account(password, mock_db, mock_user)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "密码错误" in str(exc_info.value.detail)
