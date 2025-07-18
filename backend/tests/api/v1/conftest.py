"""API测试的共享fixtures"""

import pytest
from typing import AsyncGenerator, Dict
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.models import User
from app.core.auth import AuthService
from app.crud import user as crud_user


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """创建异步HTTP客户端"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_user(async_db: AsyncSession) -> User:
    """创建测试用户"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "hashed_password": AuthService.get_password_hash("testpassword123"),
        "is_active": True,
        "is_superuser": False
    }
    user = await crud_user.create(async_db, obj_in=user_data)
    await async_db.commit()
    return user


@pytest.fixture
async def test_superuser(async_db: AsyncSession) -> User:
    """创建测试超级用户"""
    user_data = {
        "email": "admin@example.com",
        "username": "admin",
        "hashed_password": AuthService.get_password_hash("adminpassword123"),
        "is_active": True,
        "is_superuser": True
    }
    user = await crud_user.create(async_db, obj_in=user_data)
    await async_db.commit()
    return user


@pytest.fixture
def auth_headers(test_user: User) -> Dict[str, str]:
    """创建认证headers"""
    access_token = AuthService.create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def superuser_auth_headers(test_superuser: User) -> Dict[str, str]:
    """创建超级用户认证headers"""
    access_token = AuthService.create_access_token(data={"sub": str(test_superuser.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def expired_token() -> str:
    """创建过期的token"""
    import datetime
    from app.core.config import settings
    
    # 创建一个已经过期的token
    expires_delta = datetime.timedelta(minutes=-30)
    expired_token = AuthService.create_access_token(
        data={"sub": "1"},
        expires_delta=expires_delta
    )
    return expired_token