"""Database configuration and session management."""

import logging
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import DATABASE_CONFIG, settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


# 创建异步数据库引擎
engine = create_async_engine(settings.DATABASE_URL, **DATABASE_CONFIG)

# 创建异步会话工厂
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话依赖注入函数.

    包含自动重试机制，处理临时连接错误。
    """
    max_retries = 3
    retry_delay = 1.0  # seconds

    for attempt in range(max_retries):
        try:
            async with async_session_factory() as session:
                try:
                    yield session
                    break  # 成功，退出重试循环
                except Exception as e:
                    logger.error(f"Database session error: {e}")
                    await session.rollback()
                    raise
                finally:
                    await session.close()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Database connection failed after {max_retries} attempts: {e}")
                raise

            # 检查是否是可重试的错误
            error_msg = str(e).lower()
            retryable_errors = [
                "connection refused",
                "connection reset",
                "temporary failure",
                "too many connections",
                "connection timeout"
            ]

            if any(err in error_msg for err in retryable_errors):
                logger.warning(f"Retryable database error on attempt {attempt + 1}/{max_retries}: {e}")
                import asyncio
                await asyncio.sleep(retry_delay * (attempt + 1))  # 指数退避
                continue
            else:
                # 非重试错误，直接抛出
                raise


async def init_db() -> None:
    """初始化数据库表."""
    logger.info("Initializing database tables...")
    try:
        async with engine.begin() as conn:
            # 导入所有模型以确保它们被注册
            from app.models import models  # noqa: F401

            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db() -> None:
    """关闭数据库连接."""
    logger.info("Closing database connections...")
    try:
        await engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise


async def check_db_health() -> dict[str, Any]:
    """检查数据库健康状态.

    Returns:
        包含健康状态信息的字典
    """
    from sqlalchemy import text

    health_info = {
        "status": "unknown",
        "latency_ms": None,
        "connection_count": None,
        "error": None
    }

    try:
        import time
        start_time = time.time()

        async with engine.connect() as conn:
            # 测试基本连接
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

            # 获取连接池状态
            pool_status = engine.pool.status()  # type: ignore[attr-defined]

        latency_ms = (time.time() - start_time) * 1000

        health_info.update({
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "pool_status": pool_status,
        })

        logger.info(f"Database health check passed, latency: {latency_ms:.2f}ms")

    except Exception as e:
        health_info.update({
            "status": "unhealthy",
            "error": str(e)
        })
        logger.error(f"Database health check failed: {e}")

    return health_info
