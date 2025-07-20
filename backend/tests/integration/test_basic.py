"""
基础集成测试，验证测试环境配置正确。
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_test_environment(db_session: AsyncSession):
    """测试测试环境是否正确配置。"""
    # 测试数据库连接
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1

    # 测试事务回滚
    await db_session.execute(text("CREATE TABLE test_table (id INT)"))
    # 这个表应该在测试结束后自动回滚


@pytest.mark.asyncio
async def test_client_setup(client: AsyncClient):
    """测试测试客户端是否正确配置。"""
    # 测试可以访问 API
    response = await client.get("/api/v1/auth/login")
    # 应该返回 405 (Method Not Allowed) 而不是 404
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_fixtures_work(
    client: AsyncClient, test_user, auth_headers: dict, sample_space_data: dict
):
    """测试所有 fixtures 是否正常工作。"""
    # 测试用户已创建
    assert test_user.id is not None
    assert test_user.username == "testuser"

    # 测试认证头部
    assert "Authorization" in auth_headers
    assert auth_headers["Authorization"].startswith("Bearer ")

    # 测试可以使用认证访问受保护端点
    response = await client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

    # 测试示例数据
    assert "name" in sample_space_data
    assert "description" in sample_space_data
