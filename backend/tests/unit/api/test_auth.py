"""Unit tests for auth endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import (
    change_password,
    confirm_reset_password,
    login,
    login_json,
    logout,
    refresh_token,
    register,
    reset_password,
    validate_password_strength,
)
from app.core.auth import AuthService
from app.models.models import User
from app.schemas.auth import (
    ChangePasswordRequest,
    RefreshTokenRequest,
    ResetPasswordConfirm,
    ResetPasswordRequest,
    UserLogin,
    UserRegister,
)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user():
    """Mock user object."""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.is_active = True
    user.hashed_password = "hashed_password"
    user.full_name = "Test User"
    user.avatar_url = None
    user.preferences = {}
    user.is_verified = False
    user.is_premium = False
    user.daily_usage = 10
    user.last_reset_date = None
    user.last_login = None
    user.created_at = datetime.now(UTC)
    user.updated_at = datetime.now(UTC)
    return user


@pytest.fixture
def mock_request():
    """Mock request object."""
    request = MagicMock(spec=Request)
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    return request


@pytest.fixture
def mock_form_data():
    """Mock OAuth2 form data."""
    form = MagicMock(spec=OAuth2PasswordRequestForm)
    form.username = "testuser"
    form.password = "Password123"
    return form


class TestPasswordValidation:
    """Test password validation function."""

    def test_valid_password(self):
        """Test valid password passes validation."""
        validate_password_strength("Password123")

    def test_password_too_short(self):
        """Test password too short."""
        with pytest.raises(ValueError) as exc_info:
            validate_password_strength("Pass1")
        assert "密码长度至少8位" in str(exc_info.value)

    def test_password_no_uppercase(self):
        """Test password without uppercase."""
        with pytest.raises(ValueError) as exc_info:
            validate_password_strength("password123")
        assert "密码必须包含至少一个大写字母" in str(exc_info.value)

    def test_password_no_lowercase(self):
        """Test password without lowercase."""
        with pytest.raises(ValueError) as exc_info:
            validate_password_strength("PASSWORD123")
        assert "密码必须包含至少一个小写字母" in str(exc_info.value)

    def test_password_no_digit(self):
        """Test password without digit."""
        with pytest.raises(ValueError) as exc_info:
            validate_password_strength("PasswordABC")
        assert "密码必须包含至少一个数字" in str(exc_info.value)


class TestRegisterEndpoint:
    """Test cases for register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, mock_db, mock_user):
        """Test successful user registration."""
        # Arrange
        user_data = UserRegister(
            username="newuser",
            email="new@example.com",
            password="SecurePass123",
            full_name="New User",
        )

        with patch.object(AuthService, "create_user", return_value=mock_user):
            # Act
            result = await register(user_data, mock_db)

            # Assert
            # Result is the mock_user, not UserResponse
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_register_weak_password(self, mock_db):
        """Test registration with weak password."""
        # Arrange
        user_data = UserRegister(
            username="newuser",
            email="new@example.com",
            password="weak123",  # Valid for schema (6 chars) but weak for validation
            full_name="New User",
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await register(user_data, mock_db)

        assert exc_info.value.status_code == 400
        assert "密码长度至少8位" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_register_duplicate_user(self, mock_db):
        """Test registration with duplicate username."""
        # Arrange
        user_data = UserRegister(
            username="existinguser",
            email="existing@example.com",
            password="Password123",
            full_name="Existing User",
        )

        with patch.object(
            AuthService,
            "create_user",
            side_effect=HTTPException(status_code=400, detail="用户名已存在"),
        ):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await register(user_data, mock_db)

            assert exc_info.value.status_code == 400
            assert "用户名已存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_register_database_error(self, mock_db):
        """Test registration with database error."""
        # Arrange
        user_data = UserRegister(
            username="newuser",
            email="new@example.com",
            password="Password123",
            full_name="New User",
        )

        with patch.object(
            AuthService,
            "create_user",
            side_effect=Exception("Database connection error"),
        ):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await register(user_data, mock_db)

            assert exc_info.value.status_code == 500
            assert "注册失败" in str(exc_info.value.detail)


class TestLoginEndpoint:
    """Test cases for login endpoints."""

    @pytest.mark.asyncio
    async def test_login_success(
        self, mock_request, mock_db, mock_user, mock_form_data
    ):
        """Test successful login."""
        # Arrange
        with (
            patch.object(AuthService, "authenticate_user", return_value=mock_user),
            patch.object(
                AuthService, "create_access_token", return_value="access_token"
            ),
            patch.object(
                AuthService, "create_refresh_token", return_value="refresh_token"
            ),
            patch("app.core.config.settings.ACCESS_TOKEN_EXPIRE_MINUTES", 30),
        ):
            # Act
            result = await login(mock_request, mock_form_data, mock_db)

            # Assert
            assert result["access_token"] == "access_token"
            assert result["refresh_token"] == "refresh_token"
            assert result["token_type"] == "bearer"
            assert result["expires_in"] == 1800  # 30 * 60

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(
        self, mock_request, mock_db, mock_form_data
    ):
        """Test login with invalid credentials."""
        # Arrange
        with patch.object(AuthService, "authenticate_user", return_value=None):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await login(mock_request, mock_form_data, mock_db)

            assert exc_info.value.status_code == 401
            assert "用户名或密码错误" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self, mock_request, mock_db, mock_user, mock_form_data
    ):
        """Test login with inactive user."""
        # Arrange
        mock_user.is_active = False

        with patch.object(AuthService, "authenticate_user", return_value=mock_user):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await login(mock_request, mock_form_data, mock_db)

            assert exc_info.value.status_code == 400
            assert "用户账户已禁用" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_json_success(self, mock_request, mock_db, mock_user):
        """Test successful JSON login."""
        # Arrange
        user_data = UserLogin(username="testuser", password="Password123")

        with (
            patch.object(AuthService, "authenticate_user", return_value=mock_user),
            patch.object(
                AuthService, "create_access_token", return_value="access_token"
            ),
            patch.object(
                AuthService, "create_refresh_token", return_value="refresh_token"
            ),
            patch("app.core.config.settings.ACCESS_TOKEN_EXPIRE_MINUTES", 30),
        ):
            # Act
            result = await login_json(mock_request, user_data, mock_db)

            # Assert
            assert result["access_token"] == "access_token"
            assert result["refresh_token"] == "refresh_token"


class TestRefreshTokenEndpoint:
    """Test cases for refresh token endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, mock_db, mock_user):
        """Test successful token refresh."""
        # Arrange
        refresh_data = RefreshTokenRequest(refresh_token="valid_refresh_token")

        with (
            patch.object(AuthService, "verify_token", return_value={"sub": "1"}),
            patch.object(AuthService, "get_user_by_id", return_value=mock_user),
            patch.object(
                AuthService, "create_access_token", return_value="new_access_token"
            ),
            patch.object(
                AuthService, "create_refresh_token", return_value="new_refresh_token"
            ),
        ):
            # Act
            result = await refresh_token(refresh_data, mock_db)

            # Assert
            assert result["access_token"] == "new_access_token"
            assert result["refresh_token"] == "new_refresh_token"

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, mock_db):
        """Test refresh with invalid token."""
        # Arrange
        refresh_data = RefreshTokenRequest(refresh_token="invalid_token")

        with patch.object(
            AuthService, "verify_token", side_effect=Exception("Invalid token")
        ):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(refresh_data, mock_db)

            assert exc_info.value.status_code == 401
            assert "无效的刷新令牌" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_token_no_user_id(self, mock_db):
        """Test refresh token without user ID."""
        # Arrange
        refresh_data = RefreshTokenRequest(refresh_token="token_without_sub")

        with patch.object(AuthService, "verify_token", return_value={}):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(refresh_data, mock_db)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_user_not_found(self, mock_db):
        """Test refresh token with non-existent user."""
        # Arrange
        refresh_data = RefreshTokenRequest(refresh_token="valid_token")

        with (
            patch.object(AuthService, "verify_token", return_value={"sub": "999"}),
            patch.object(AuthService, "get_user_by_id", return_value=None),
        ):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(refresh_data, mock_db)

            assert exc_info.value.status_code == 401
            assert "用户不存在或已禁用" in str(exc_info.value.detail)


class TestLogoutEndpoint:
    """Test cases for logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(self):
        """Test successful logout."""
        # Act
        result = await logout()

        # Assert
        assert result["message"] == "登出成功"


class TestChangePasswordEndpoint:
    """Test cases for change password endpoint."""

    @pytest.mark.asyncio
    async def test_change_password_success(self, mock_db, mock_user):
        """Test successful password change."""
        # Arrange
        password_data = ChangePasswordRequest(
            old_password="old_password", new_password="NewSecurePass123"
        )
        mock_user.hashed_password = "old_hashed_password"

        with (
            patch.object(AuthService, "verify_password", return_value=True),
            patch.object(
                AuthService, "get_password_hash", return_value="new_hashed_password"
            ),
        ):
            # Act
            result = await change_password(password_data, mock_user, mock_db)

            # Assert
            assert result["message"] == "密码修改成功"
            assert mock_user.hashed_password == "new_hashed_password"
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(self, mock_db, mock_user):
        """Test change password with wrong old password."""
        # Arrange
        password_data = ChangePasswordRequest(
            old_password="wrong_password", new_password="NewPassword123"
        )

        with patch.object(AuthService, "verify_password", return_value=False):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await change_password(password_data, mock_user, mock_db)

            assert exc_info.value.status_code == 400
            assert "旧密码错误" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_change_password_weak_new(self, mock_db, mock_user):
        """Test change password with weak new password."""
        # Arrange
        password_data = ChangePasswordRequest(
            old_password="old_password",
            new_password="weak123",  # Valid for schema but weak for validation
        )

        with patch.object(AuthService, "verify_password", return_value=True):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await change_password(password_data, mock_user, mock_db)

            assert exc_info.value.status_code == 400
            assert "密码长度至少8位" in str(exc_info.value.detail)


class TestResetPasswordEndpoint:
    """Test cases for reset password endpoints."""

    @pytest.mark.asyncio
    async def test_reset_password_request_success(self, mock_db, mock_user):
        """Test successful password reset request."""
        # Arrange
        reset_data = ResetPasswordRequest(email="test@example.com")

        with (
            patch.object(AuthService, "get_user_by_email", return_value=mock_user),
            patch.object(
                AuthService, "create_access_token", return_value="reset_token"
            ),
            patch("app.core.config.settings.DEBUG", False),
        ):
            # Act
            result = await reset_password(reset_data, mock_db)

            # Assert
            assert result["message"] == "如果邮箱存在，重置链接已发送"

    @pytest.mark.asyncio
    async def test_reset_password_user_not_found(self, mock_db):
        """Test reset password with non-existent email."""
        # Arrange
        reset_data = ResetPasswordRequest(email="nonexistent@example.com")

        with patch.object(AuthService, "get_user_by_email", return_value=None):
            # Act
            result = await reset_password(reset_data, mock_db)

            # Assert
            # Security: Same message even if user doesn't exist
            assert result["message"] == "如果邮箱存在，重置链接已发送"

    @pytest.mark.asyncio
    async def test_reset_password_debug_mode(self, mock_db, mock_user):
        """Test reset password in debug mode returns token."""
        # Arrange
        reset_data = ResetPasswordRequest(email="test@example.com")

        with (
            patch.object(AuthService, "get_user_by_email", return_value=mock_user),
            patch.object(
                AuthService, "create_access_token", return_value="debug_reset_token"
            ),
            patch("app.core.config.settings.DEBUG", True),
        ):
            # Act
            result = await reset_password(reset_data, mock_db)

            # Assert
            assert result["reset_token"] == "debug_reset_token"

    @pytest.mark.asyncio
    async def test_confirm_reset_password_success(self, mock_db, mock_user):
        """Test successful password reset confirmation."""
        # Arrange
        confirm_data = ResetPasswordConfirm(
            token="valid_reset_token", new_password="NewSecurePassword123"
        )

        with (
            patch.object(
                AuthService,
                "verify_token",
                return_value={"sub": "1", "type": "password_reset"},
            ),
            patch.object(AuthService, "get_user_by_id", return_value=mock_user),
            patch.object(
                AuthService, "get_password_hash", return_value="new_hashed_password"
            ),
        ):
            # Act
            result = await confirm_reset_password(confirm_data, mock_db)

            # Assert
            assert result["message"] == "密码重置成功"
            assert mock_user.hashed_password == "new_hashed_password"
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirm_reset_password_invalid_token(self, mock_db):
        """Test reset password confirmation with invalid token."""
        # Arrange
        confirm_data = ResetPasswordConfirm(
            token="invalid_token", new_password="NewPassword123"
        )

        with patch.object(
            AuthService, "verify_token", side_effect=Exception("Invalid token")
        ):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await confirm_reset_password(confirm_data, mock_db)

            assert exc_info.value.status_code == 400
            assert "无效的重置令牌" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_confirm_reset_password_wrong_token_type(self, mock_db):
        """Test reset password confirmation with wrong token type."""
        # Arrange
        confirm_data = ResetPasswordConfirm(
            token="valid_token", new_password="NewPassword123"
        )

        with patch.object(
            AuthService, "verify_token", return_value={"sub": "1", "type": "access"}
        ):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await confirm_reset_password(confirm_data, mock_db)

            assert exc_info.value.status_code == 400
