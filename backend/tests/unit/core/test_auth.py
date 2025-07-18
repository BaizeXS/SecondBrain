"""Test authentication and authorization services."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    AuthService,
    get_current_active_user,
    get_current_premium_user,
    get_current_user,
    oauth2_scheme,
    pwd_context,
)
from app.core.config import settings
from app.models.models import User


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.hashed_password = pwd_context.hash("TestPass123")
    user.full_name = "Test User"
    user.is_active = True
    user.is_premium = False
    user.daily_usage = 0
    user.last_reset_date = datetime.now(UTC)
    user.preferences = {"theme": "light", "language": "zh-cn"}
    return user


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock(spec=AsyncSession)


class TestAuthService:
    """Test AuthService class."""

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        hashed = AuthService.get_password_hash("TestPass123")
        assert AuthService.verify_password("TestPass123", hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        hashed = AuthService.get_password_hash("TestPass123")
        assert AuthService.verify_password("WrongPass456", hashed) is False

    def test_get_password_hash(self):
        """Test password hashing."""
        password = "TestPass123"
        hashed = AuthService.get_password_hash(password)

        # Hash should be different from plain password
        assert hashed != password
        # Should be able to verify it
        assert AuthService.verify_password(password, hashed) is True

    def test_create_access_token(self):
        """Test creating access token."""
        data = {"sub": "1"}
        token = AuthService.create_access_token(data)

        # Decode and verify
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == "1"
        assert "exp" in payload

    def test_create_access_token_with_custom_expiry(self):
        """Test creating access token with custom expiry."""
        data = {"sub": "1"}
        expires_delta = timedelta(hours=1)
        token = AuthService.create_access_token(data, expires_delta)

        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
        now = datetime.now(UTC)

        # Should expire in about 1 hour
        assert 55 <= (exp_time - now).total_seconds() / 60 <= 65

    def test_create_refresh_token(self):
        """Test creating refresh token."""
        data = {"sub": "1"}
        token = AuthService.create_refresh_token(data)

        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == "1"
        assert "exp" in payload

        # Check expiry is set correctly
        exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
        now = datetime.now(UTC)
        days_diff = (exp_time - now).days
        assert (
            days_diff == settings.REFRESH_TOKEN_EXPIRE_DAYS - 1
        )  # Allow for time passing

    def test_verify_token_valid(self):
        """Test verifying valid token."""
        data = {"sub": "1", "type": "access"}
        token = AuthService.create_access_token(data)

        payload = AuthService.verify_token(token)
        assert payload["sub"] == "1"
        assert payload["type"] == "access"

    def test_verify_token_invalid(self):
        """Test verifying invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            AuthService.verify_token("invalid_token")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "无效的令牌"

    def test_verify_token_expired(self):
        """Test verifying expired token."""
        # Create token that expires immediately
        data = {"sub": "1"}
        expired_token = AuthService.create_access_token(data, timedelta(seconds=-1))

        with pytest.raises(HTTPException) as exc_info:
            AuthService.verify_token(expired_token)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_by_username(self, mock_db, mock_user):
        """Test getting user by username."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        user = await AuthService.get_user_by_username(mock_db, "testuser")

        assert user == mock_user
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, mock_db, mock_user):
        """Test getting user by email."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        user = await AuthService.get_user_by_email(mock_db, "test@example.com")

        assert user == mock_user
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, mock_db, mock_user):
        """Test getting user by ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        user = await AuthService.get_user_by_id(mock_db, 1)

        assert user == mock_user
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user_with_username(self, mock_db, mock_user):
        """Test authenticating user with username."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        user = await AuthService.authenticate_user(mock_db, "testuser", "TestPass123")

        assert user == mock_user

    @pytest.mark.asyncio
    async def test_authenticate_user_with_email(self, mock_db, mock_user):
        """Test authenticating user with email."""
        mock_result = MagicMock()
        # First call returns None (username not found)
        # Second call returns user (email found)
        mock_result.scalar_one_or_none.side_effect = [None, mock_user]
        mock_db.execute.return_value = mock_result

        user = await AuthService.authenticate_user(
            mock_db, "test@example.com", "TestPass123"
        )

        assert user == mock_user
        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, mock_db, mock_user):
        """Test authenticating user with wrong password."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        user = await AuthService.authenticate_user(mock_db, "testuser", "wrongpassword")

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, mock_db):
        """Test authenticating non-existent user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        user = await AuthService.authenticate_user(mock_db, "nonexistent", "password")

        assert user is None

    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_db):
        """Test creating new user successfully."""
        # Mock that no existing user is found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        user = await AuthService.create_user(
            mock_db,
            username="newuser",
            email="new@example.com",
            password="NewPass123",
            full_name="New User",
        )

        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.full_name == "New User"
        assert user.preferences == {"theme": "light", "language": "zh-cn"}
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_username_exists(self, mock_db, mock_user):
        """Test creating user with existing username."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await AuthService.create_user(
                mock_db,
                username="testuser",
                email="new@example.com",
                password="NewPass123",
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "用户名已存在"

    @pytest.mark.asyncio
    async def test_create_user_email_exists(self, mock_db, mock_user):
        """Test creating user with existing email."""
        mock_result = MagicMock()
        # First call returns None (username not found)
        # Second call returns user (email exists)
        mock_result.scalar_one_or_none.side_effect = [None, mock_user]
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await AuthService.create_user(
                mock_db,
                username="newuser",
                email="test@example.com",
                password="NewPass123",
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "邮箱已存在"


class TestDependencyFunctions:
    """Test dependency injection functions."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid(self, mock_db, mock_user):
        """Test getting current user with valid token."""
        # Create valid token
        token_data = {"sub": "1"}
        token = AuthService.create_access_token(token_data)

        # Mock database response
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        user = await get_current_user(token, mock_db)

        assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_db):
        """Test getting current user with invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("invalid_token", mock_db)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "无法验证凭据"

    @pytest.mark.asyncio
    async def test_get_current_user_no_sub(self, mock_db):
        """Test getting current user with token missing sub."""
        # Create token without sub
        token_data = {"type": "access"}
        token = AuthService.create_access_token(token_data)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token, mock_db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, mock_db):
        """Test getting current user when user not found in database."""
        # Create valid token
        token_data = {"sub": "999"}
        token = AuthService.create_access_token(token_data)

        # Mock database response - user not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token, mock_db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_active_user_active(self, mock_user):
        """Test getting current active user when user is active."""
        mock_user.is_active = True

        user = await get_current_active_user(mock_user)

        assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self, mock_user):
        """Test getting current active user when user is inactive."""
        mock_user.is_active = False

        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(mock_user)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "用户账户已禁用"

    @pytest.mark.asyncio
    async def test_get_current_premium_user_premium(self, mock_user):
        """Test getting current premium user when user is premium."""
        mock_user.is_active = True
        mock_user.is_premium = True

        user = await get_current_premium_user(mock_user)

        assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_current_premium_user_not_premium(self, mock_user):
        """Test getting current premium user when user is not premium."""
        mock_user.is_active = True
        mock_user.is_premium = False

        with pytest.raises(HTTPException) as exc_info:
            await get_current_premium_user(mock_user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "需要高级会员权限"


# RateLimiter tests moved to test_rate_limiter.py


class TestConfiguration:
    """Test module configuration."""

    def test_oauth2_scheme_configuration(self):
        """Test OAuth2 scheme is configured correctly."""
        # OAuth2PasswordBearer stores token URL internally
        assert oauth2_scheme.scheme_name == "OAuth2PasswordBearer"
        # The tokenUrl is passed in constructor
        assert hasattr(oauth2_scheme, "scheme_name")

    def test_password_context_configuration(self):
        """Test password context is configured correctly."""
        # CryptContext stores schemes as a list
        assert pwd_context.identify("$2b$12$test") == "bcrypt"
        # Test that bcrypt is available
        test_hash = pwd_context.hash("test")
        assert pwd_context.verify("test", test_hash)


class TestPasswordValidation:
    """Test password validation."""

    def test_validate_password_strength_valid(self):
        """Test validating a strong password."""
        # Should not raise any exception
        AuthService.validate_password_strength("Test123Pass")

    def test_validate_password_strength_too_short(self):
        """Test password that is too short."""
        with pytest.raises(HTTPException) as exc_info:
            AuthService.validate_password_strength("Test1")

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "密码长度至少为8个字符"

    def test_validate_password_strength_no_uppercase(self):
        """Test password without uppercase."""
        with pytest.raises(HTTPException) as exc_info:
            AuthService.validate_password_strength("test123pass")

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "密码必须包含至少一个大写字母"

    def test_validate_password_strength_no_lowercase(self):
        """Test password without lowercase."""
        with pytest.raises(HTTPException) as exc_info:
            AuthService.validate_password_strength("TEST123PASS")

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "密码必须包含至少一个小写字母"

    def test_validate_password_strength_no_digit(self):
        """Test password without digit."""
        with pytest.raises(HTTPException) as exc_info:
            AuthService.validate_password_strength("TestPassWord")

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "密码必须包含至少一个数字"
