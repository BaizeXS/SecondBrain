"""Database configuration and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import DATABASE_CONFIG, settings


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
    """获取数据库会话依赖注入函数."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库表."""
    async with engine.begin() as conn:
        # 导入所有模型以确保它们被注册
        from app.models import models  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库连接."""
    await engine.dispose()
