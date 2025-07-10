"""Alembic environment configuration."""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 导入模型
from app.core.config import settings
from app.models.models import Base

# Alembic Config对象，提供对.ini文件中值的访问
config = context.config

# 设置数据库URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# 解释日志配置文件的Python日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加模型的元数据对象以支持"autogenerate"
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """在"离线"模式下运行迁移.

    这配置上下文只有一个URL
    而不需要Engine，虽然Engine也是可以接受的
    在这里。通过跳过Engine创建
    我们甚至不需要DBAPI可用。

    从字面上调用context.execute()将发出给定的字符串到
    脚本输出。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """运行迁移."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """在异步模式下创建Engine并将连接与上下文关联."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在"在线"模式下运行迁移."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
