"""
Core utilities and configurations for the Second Brain application.

This module provides essential components including:
- Authentication and security utilities
- Application configuration management
- Database connection and session management
- Rate limiting functionality
"""

from app.core.auth import (
    AuthService,
    get_current_active_user,
    get_current_premium_user,
    get_current_user,
    oauth2_scheme,
)
from app.core.config import settings
from app.core.database import (
    Base,
    async_session_factory,
    check_db_health,
    close_db,
    engine,
    get_db,
    init_db,
)
from app.core.rate_limiter import (
    RateLimiter,
    rate_limiter,
)

__all__ = [
    # Auth exports
    "AuthService",
    "get_current_user",
    "get_current_active_user",
    "get_current_premium_user",
    "oauth2_scheme",
    # Config exports
    "settings",
    # Database exports
    "Base",
    "engine",
    "async_session_factory",
    "get_db",
    "init_db",
    "close_db",
    "check_db_health",
    # Rate limiter exports
    "RateLimiter",
    "rate_limiter",
]
