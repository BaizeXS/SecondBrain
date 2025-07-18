"""Test database configuration and session management."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import (
    Base,
    async_session_factory,
    check_db_health,
    close_db,
    engine,
    get_db,
    init_db,
)


class TestDatabaseConfiguration:
    """Test database configuration."""

    def test_base_class(self):
        """Test Base class is properly defined."""
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")
        # Base should be a DeclarativeBase
        assert Base.__name__ == "Base"

    def test_engine_creation(self):
        """Test engine is created with correct configuration."""
        assert engine is not None
        # Check engine URL (without exposing credentials)
        assert "postgresql" in str(engine.url)
        assert "asyncpg" in str(engine.url)

    def test_session_factory_configuration(self):
        """Test session factory is configured correctly."""
        assert async_session_factory is not None
        # Check session factory configuration
        assert async_session_factory.kw.get("expire_on_commit") is False
        # The class_ is set during initialization, not in kw
        assert async_session_factory.class_ is AsyncSession


class TestGetDb:
    """Test get_db dependency injection function."""

    @pytest.mark.asyncio
    async def test_get_db_success(self):
        """Test successful database session creation."""
        # Create a mock session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.close = AsyncMock()

        # Mock the session factory
        with patch("app.core.database.async_session_factory") as mock_factory:
            # Configure the async context manager
            mock_factory.return_value.__aenter__.return_value = mock_session
            mock_factory.return_value.__aexit__.return_value = None

            # Test the generator
            async for session in get_db():
                assert session == mock_session

            # Verify close was called
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_with_exception(self):
        """Test database session rollback on exception."""
        # Create a mock session with rollback
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        # Mock the session factory
        with patch("app.core.database.async_session_factory") as mock_factory:
            mock_factory.return_value.__aenter__.return_value = mock_session
            mock_factory.return_value.__aexit__.return_value = None

            # Test exception handling
            gen = get_db()
            await gen.__anext__()  # Get the session but don't use it

            # Simulate an exception
            with pytest.raises(ValueError):
                await gen.athrow(ValueError("Test error"))

            # Verify rollback and close were called
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_cleanup_on_normal_exit(self):
        """Test that session is properly closed on normal exit."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.close = AsyncMock()

        with patch("app.core.database.async_session_factory") as mock_factory:
            mock_factory.return_value.__aenter__.return_value = mock_session
            mock_factory.return_value.__aexit__.return_value = None

            # Use the session normally
            async for session in get_db():
                assert session == mock_session
                # Normal exit

            # Verify close was called even without exception
            mock_session.close.assert_called_once()


class TestInitDb:
    """Test database initialization."""

    @pytest.mark.asyncio
    async def test_init_db_success(self):
        """Test successful database initialization."""
        # We'll test that init_db executes without error
        # In a real scenario, this would create tables
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock()

        with patch("app.core.database.engine") as mock_engine:
            # Setup the mock to return an async context manager
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None

            # Run init_db
            await init_db()

            # Verify begin was called
            mock_engine.begin.assert_called_once()

            # Verify run_sync was called with create_all
            mock_conn.run_sync.assert_called_once()
            args = mock_conn.run_sync.call_args[0]
            assert args[0] == Base.metadata.create_all

    @pytest.mark.asyncio
    async def test_init_db_error_handling(self):
        """Test init_db error handling."""
        with patch("app.core.database.engine") as mock_engine:
            # Make begin raise an exception
            mock_engine.begin.side_effect = Exception("Database error")

            # Should propagate the exception
            with pytest.raises(Exception) as exc_info:
                await init_db()

            assert "Database error" in str(exc_info.value)


class TestCloseDb:
    """Test database connection closing."""

    @pytest.mark.asyncio
    async def test_close_db(self):
        """Test closing database connections."""
        with patch("app.core.database.engine") as mock_engine:
            mock_engine.dispose = AsyncMock()

            await close_db()

            mock_engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_db_error_handling(self):
        """Test error handling during connection closing."""
        with patch("app.core.database.engine") as mock_engine:
            mock_engine.dispose = AsyncMock(side_effect=Exception("Connection error"))

            # Should raise the exception
            with pytest.raises(Exception) as exc_info:
                await close_db()

            assert "Connection error" in str(exc_info.value)


class TestDatabaseIntegration:
    """Test database integration scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_sessions(self):
        """Test creating multiple sessions."""
        sessions = []
        mock_session1 = AsyncMock(spec=AsyncSession)
        mock_session2 = AsyncMock(spec=AsyncSession)
        mock_sessions = [mock_session1, mock_session2]

        with patch("app.core.database.async_session_factory") as mock_factory:
            # Return different sessions
            for mock_session in mock_sessions:
                mock_session.close = AsyncMock()

            # Configure factory to return different sessions
            mock_factory.side_effect = [
                AsyncMock(
                    __aenter__=AsyncMock(return_value=mock_session1),
                    __aexit__=AsyncMock(return_value=None),
                ),
                AsyncMock(
                    __aenter__=AsyncMock(return_value=mock_session2),
                    __aexit__=AsyncMock(return_value=None),
                ),
            ]

            # Get multiple sessions
            async for session in get_db():
                sessions.append(session)

            async for session in get_db():
                sessions.append(session)

            assert len(sessions) == 2
            assert sessions[0] == mock_session1
            assert sessions[1] == mock_session2

    def test_database_url_configuration(self):
        """Test that database URL is properly configured."""
        from app.core.config import settings

        # Should have a DATABASE_URL
        assert hasattr(settings, "DATABASE_URL")
        assert settings.DATABASE_URL is not None
        assert "postgresql" in settings.DATABASE_URL

    def test_database_config_applied(self):
        """Test that DATABASE_CONFIG is applied to engine."""
        from app.core.config import DATABASE_CONFIG

        # Check some important configs
        assert "pool_pre_ping" in DATABASE_CONFIG
        assert DATABASE_CONFIG["pool_pre_ping"] is True
        assert "pool_recycle" in DATABASE_CONFIG
        assert DATABASE_CONFIG["pool_recycle"] == 3600


class TestDatabaseRetry:
    """Test database retry mechanisms."""

    @pytest.mark.asyncio
    async def test_get_db_with_retry_on_connection_error(self):
        """Test that get_db retries on connection errors."""
        call_count = 0
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.close = AsyncMock()

        def side_effect():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                # First attempt fails with connection error
                raise Exception("connection refused")
            # Second attempt succeeds
            return AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=None),
            )

        with patch("app.core.database.async_session_factory") as mock_factory:
            mock_factory.side_effect = side_effect

            # Should retry and succeed
            async for session in get_db():
                assert session == mock_session

            # Verify it was called twice (first failed, second succeeded)
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_get_db_max_retries_exceeded(self):
        """Test that get_db fails after max retries."""
        with patch("app.core.database.async_session_factory") as mock_factory:
            # Always fail with connection error
            mock_factory.side_effect = Exception("connection refused")

            # Should fail after max retries
            with pytest.raises(Exception) as exc_info:
                async for _ in get_db():
                    pass

            assert "connection refused" in str(exc_info.value)
            # Should be called 3 times (max_retries)
            assert mock_factory.call_count == 3

    @pytest.mark.asyncio
    async def test_get_db_non_retryable_error(self):
        """Test that non-retryable errors are raised immediately."""
        with patch("app.core.database.async_session_factory") as mock_factory:
            # Fail with non-retryable error
            mock_factory.side_effect = ValueError("Invalid configuration")

            # Should fail immediately without retry
            with pytest.raises(ValueError):
                async for _ in get_db():
                    pass

            # Should only be called once
            assert mock_factory.call_count == 1


class TestHealthCheck:
    """Test database health check functionality."""

    @pytest.mark.asyncio
    async def test_check_db_health_success(self):
        """Test successful health check."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_result)

        mock_pool = MagicMock()
        mock_pool.status.return_value = "Pool size: 5 Connections in use: 1"

        with patch("app.core.database.engine") as mock_engine:
            mock_engine.connect.return_value.__aenter__.return_value = mock_conn
            mock_engine.connect.return_value.__aexit__.return_value = None
            mock_engine.pool = mock_pool

            health = await check_db_health()

            assert health["status"] == "healthy"
            assert health["latency_ms"] is not None
            assert health["pool_status"] is not None
            assert health["error"] is None

    @pytest.mark.asyncio
    async def test_check_db_health_failure(self):
        """Test health check with database failure."""
        with patch("app.core.database.engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("Database unreachable")

            health = await check_db_health()

            assert health["status"] == "unhealthy"
            assert health["error"] == "Database unreachable"
            assert health["latency_ms"] is None


class TestLoggingIntegration:
    """Test logging functionality."""

    @pytest.mark.asyncio
    async def test_init_db_logging(self):
        """Test that init_db logs appropriately."""
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock()

        with (
            patch("app.core.database.engine") as mock_engine,
            patch("app.core.database.logger") as mock_logger,
        ):
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None

            await init_db()

            # Verify logging calls
            mock_logger.info.assert_any_call("Initializing database tables...")
            mock_logger.info.assert_any_call("Database tables initialized successfully")

    @pytest.mark.asyncio
    async def test_close_db_logging(self):
        """Test that close_db logs appropriately."""
        with (
            patch("app.core.database.engine") as mock_engine,
            patch("app.core.database.logger") as mock_logger,
        ):
            mock_engine.dispose = AsyncMock()

            await close_db()

            # Verify logging calls
            mock_logger.info.assert_any_call("Closing database connections...")
            mock_logger.info.assert_any_call("Database connections closed successfully")

    @pytest.mark.asyncio
    async def test_error_logging(self):
        """Test error logging in database operations."""
        with (
            patch("app.core.database.engine") as mock_engine,
            patch("app.core.database.logger") as mock_logger,
        ):
            mock_engine.begin.side_effect = Exception("Init failed")

            with pytest.raises(Exception, match="Init failed"):
                await init_db()

            # Verify error was logged
            mock_logger.error.assert_called_with(
                "Failed to initialize database: Init failed"
            )
