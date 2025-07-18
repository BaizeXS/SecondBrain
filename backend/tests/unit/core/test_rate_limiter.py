"""Test rate limiter functionality."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limiter import RateLimiter, rate_limiter
from app.models.models import UsageLog, User


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.is_premium = False
    user.daily_usage = 0
    user.last_reset_date = datetime.now(UTC).date()
    return user


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def rate_limiter_instance():
    """Create a rate limiter instance."""
    return RateLimiter()


class TestRateLimiterInit:
    """Test RateLimiter initialization."""

    def test_rate_limiter_init(self, rate_limiter_instance):
        """Test rate limiter initialization."""
        assert rate_limiter_instance.free_user_limit == settings.RATE_LIMIT_FREE_USER
        assert (
            rate_limiter_instance.premium_user_limit == settings.RATE_LIMIT_PREMIUM_USER
        )


class TestCheckUserLimit:
    """Test check_user_limit method."""

    @pytest.mark.asyncio
    async def test_check_user_limit_user_not_found(
        self, mock_db, rate_limiter_instance
    ):
        """Test check_user_limit when user not found."""
        # Mock user query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter_instance.check_user_limit(1, "chat", mock_db)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "用户不存在"

    @pytest.mark.asyncio
    async def test_check_user_limit_within_limit(
        self, mock_db, mock_user, rate_limiter_instance
    ):
        """Test check_user_limit when within limit."""
        # Mock user query
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user

        # Mock usage query
        mock_usage_result = MagicMock()
        mock_usage_result.scalar.return_value = 5  # Under limit

        mock_db.execute.side_effect = [mock_user_result, mock_usage_result]

        # Should not raise exception
        await rate_limiter_instance.check_user_limit(1, "chat", mock_db)

    @pytest.mark.asyncio
    async def test_check_user_limit_exceeded_free_user(
        self, mock_db, mock_user, rate_limiter_instance
    ):
        """Test check_user_limit when limit exceeded for free user."""
        mock_user.is_premium = False

        # Mock user query
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user

        # Mock usage query - at limit
        mock_usage_result = MagicMock()
        mock_usage_result.scalar.return_value = settings.RATE_LIMIT_FREE_USER

        mock_db.execute.side_effect = [mock_user_result, mock_usage_result]

        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter_instance.check_user_limit(1, "chat", mock_db)

        assert exc_info.value.status_code == 429
        assert "今日chat使用次数已达上限" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_check_user_limit_premium_user(
        self, mock_db, mock_user, rate_limiter_instance
    ):
        """Test check_user_limit for premium user."""
        mock_user.is_premium = True

        # Mock user query
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user

        # Mock usage query - above free limit but under premium
        mock_usage_result = MagicMock()
        mock_usage_result.scalar.return_value = settings.RATE_LIMIT_FREE_USER + 10

        mock_db.execute.side_effect = [mock_user_result, mock_usage_result]

        # Should not raise exception
        await rate_limiter_instance.check_user_limit(1, "chat", mock_db)


class TestIncrementUsage:
    """Test increment_usage method."""

    @pytest.mark.asyncio
    async def test_increment_usage_success(self, mock_db, rate_limiter_instance):
        """Test successful usage increment."""
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()

        with patch.object(
            rate_limiter_instance, "_update_user_daily_usage", new_callable=AsyncMock
        ):
            await rate_limiter_instance.increment_usage(
                user_id=1,
                action="chat",
                db=mock_db,
                model="gpt-4",
                provider="openai",
                token_count=100,
                cost=0.01,
            )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        # Check the UsageLog object
        usage_log = mock_db.add.call_args[0][0]
        assert isinstance(usage_log, UsageLog)
        assert usage_log.user_id == 1
        assert usage_log.action == "chat"
        assert usage_log.model == "gpt-4"
        assert usage_log.provider == "openai"
        assert usage_log.token_count == 100
        assert usage_log.cost == 0.01

    @pytest.mark.asyncio
    async def test_increment_usage_failure(self, mock_db, rate_limiter_instance):
        """Test usage increment with database error."""
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock(side_effect=Exception("Database error"))
        mock_db.rollback = AsyncMock()

        # Should not raise exception, just log error
        await rate_limiter_instance.increment_usage(
            user_id=1, action="chat", db=mock_db
        )

        mock_db.rollback.assert_called_once()


class TestUpdateUserDailyUsage:
    """Test _update_user_daily_usage method."""

    @pytest.mark.asyncio
    async def test_update_user_daily_usage_reset_needed(
        self, mock_db, mock_user, rate_limiter_instance
    ):
        """Test updating daily usage when reset is needed."""
        # Set last reset to yesterday
        mock_user.last_reset_date = datetime.now(UTC).date() - timedelta(days=1)

        # Mock user query
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user

        # Mock usage count query
        mock_usage_result = MagicMock()
        mock_usage_result.scalar.return_value = 10

        mock_db.execute.side_effect = [mock_user_result, mock_usage_result]
        mock_db.commit = AsyncMock()

        await rate_limiter_instance._update_user_daily_usage(1, mock_db)

        # Check reset happened
        assert mock_user.daily_usage == 10
        # last_reset_date is now a datetime, not just date
        assert isinstance(mock_user.last_reset_date, datetime)
        assert mock_user.last_reset_date.date() == datetime.now(UTC).date()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_daily_usage_no_reset(
        self, mock_db, mock_user, rate_limiter_instance
    ):
        """Test updating daily usage when no reset needed."""
        # Set last reset to today
        mock_user.last_reset_date = datetime.now(UTC).date()
        mock_user.daily_usage = 5

        # Mock user query
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user

        # Mock usage count query
        mock_usage_result = MagicMock()
        mock_usage_result.scalar.return_value = 15

        mock_db.execute.side_effect = [mock_user_result, mock_usage_result]
        mock_db.commit = AsyncMock()

        await rate_limiter_instance._update_user_daily_usage(1, mock_db)

        # Check no reset happened
        assert mock_user.daily_usage == 15
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_daily_usage_user_not_found(
        self, mock_db, rate_limiter_instance
    ):
        """Test updating daily usage when user not found."""
        # Mock user query
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = None

        mock_db.execute.return_value = mock_user_result

        # Should return without error
        await rate_limiter_instance._update_user_daily_usage(1, mock_db)

        # Commit should not be called
        mock_db.commit.assert_not_called()


class TestGetUserUsageStats:
    """Test get_user_usage_stats method."""

    @pytest.mark.asyncio
    async def test_get_user_usage_stats_success(self, mock_db, rate_limiter_instance):
        """Test getting user usage stats successfully."""
        # Create mock usage logs
        mock_logs = []
        for i in range(5):
            log = MagicMock(spec=UsageLog)
            log.action = "chat"
            log.model = "gpt-4"
            log.provider = "openai"
            log.token_count = 100
            log.cost = 0.01
            log.created_at = datetime.now(UTC) - timedelta(days=i)
            mock_logs.append(log)

        # Mock query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_db.execute.return_value = mock_result

        stats = await rate_limiter_instance.get_user_usage_stats(1, mock_db, days=7)

        assert stats["total_requests"] == 5
        assert stats["total_tokens"] == 500
        assert stats["total_cost"] == 0.05
        assert stats["actions"]["chat"] == 5
        assert stats["models"]["gpt-4"] == 5
        assert stats["providers"]["openai"] == 5
        assert len(stats["daily_usage"]) == 5

    @pytest.mark.asyncio
    async def test_get_user_usage_stats_empty(self, mock_db, rate_limiter_instance):
        """Test getting user usage stats with no data."""
        # Mock empty result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        stats = await rate_limiter_instance.get_user_usage_stats(1, mock_db)

        assert stats["total_requests"] == 0
        assert stats["total_tokens"] == 0
        assert stats["total_cost"] == 0
        assert stats["actions"] == {}
        assert stats["models"] == {}
        assert stats["providers"] == {}
        assert stats["daily_usage"] == {}

    @pytest.mark.asyncio
    async def test_get_user_usage_stats_error(self, mock_db, rate_limiter_instance):
        """Test getting user usage stats with error."""
        mock_db.execute.side_effect = Exception("Database error")

        stats = await rate_limiter_instance.get_user_usage_stats(1, mock_db)

        # Should return empty stats
        assert stats["total_requests"] == 0
        assert stats["total_tokens"] == 0
        assert stats["total_cost"] == 0.0


class TestResetUserDailyUsage:
    """Test reset_user_daily_usage method."""

    @pytest.mark.asyncio
    async def test_reset_user_daily_usage_success(
        self, mock_db, mock_user, rate_limiter_instance
    ):
        """Test resetting user daily usage successfully."""
        mock_user.daily_usage = 100

        # Mock user query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        await rate_limiter_instance.reset_user_daily_usage(1, mock_db)

        assert mock_user.daily_usage == 0
        # last_reset_date is now a datetime, not just date
        assert isinstance(mock_user.last_reset_date, datetime)
        assert mock_user.last_reset_date.date() == datetime.now(UTC).date()
        assert mock_user.last_reset_date.hour == 0
        assert mock_user.last_reset_date.minute == 0
        assert mock_user.last_reset_date.second == 0
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_user_daily_usage_user_not_found(
        self, mock_db, rate_limiter_instance
    ):
        """Test resetting daily usage when user not found."""
        # Mock user query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        await rate_limiter_instance.reset_user_daily_usage(1, mock_db)

        # Commit should not be called if user not found
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_reset_user_daily_usage_error(
        self, mock_db, mock_user, rate_limiter_instance
    ):
        """Test resetting daily usage with error."""
        # Mock user query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock(side_effect=Exception("Database error"))
        mock_db.rollback = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter_instance.reset_user_daily_usage(1, mock_db)

        assert exc_info.value.status_code == 500
        assert "重置使用量失败" in exc_info.value.detail
        mock_db.rollback.assert_called_once()


class TestGlobalInstance:
    """Test global rate limiter instance."""

    def test_global_rate_limiter_instance(self):
        """Test that global instance is created."""
        assert rate_limiter is not None
        assert isinstance(rate_limiter, RateLimiter)
        assert rate_limiter.free_user_limit == settings.RATE_LIMIT_FREE_USER
        assert rate_limiter.premium_user_limit == settings.RATE_LIMIT_PREMIUM_USER
