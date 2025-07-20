"""
认证流程集成测试。

测试完整的用户注册、登录、刷新令牌和权限验证流程。
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestAuthenticationFlow:
    """测试认证流程。"""

    async def test_user_registration_flow(self, client: AsyncClient):
        """测试用户注册流程。"""
        # 1. 注册新用户
        register_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "NewPass123!",
        }

        response = await client.post("/api/v1/auth/register", json=register_data)
        if response.status_code not in [200, 201]:
            print(f"Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
        assert (
            response.status_code == 201
        )  # 201 Created is the correct status for creating a new resource
        user_data = response.json()
        assert user_data["username"] == "newuser"
        assert user_data["email"] == "newuser@example.com"
        assert "id" in user_data
        assert "password" not in user_data

        # 2. 尝试使用相同用户名注册（应该失败）
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 400
        assert response.json()["detail"] in [
            "already registered",
            "用户名已存在",
            "Username already registered",
        ]

        # 3. 使用新账户登录
        login_data = {"username": "newuser", "password": "NewPass123!"}

        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["token_type"] == "bearer"

    async def test_login_with_email(self, client: AsyncClient, test_user):
        """测试使用邮箱登录。"""
        # test_user fixture 确保测试用户已创建
        assert test_user is not None
        # 使用邮箱登录
        login_data = {
            "username": "test@example.com",  # 使用邮箱而不是用户名
            "password": "TestPass123!",
        }

        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data

    async def test_login_invalid_credentials(self, client: AsyncClient, test_user):
        """测试无效凭证登录。"""
        # test_user fixture 确保测试用户已创建
        assert test_user is not None
        # 错误的密码
        login_data = {"username": "testuser", "password": "WrongPassword123!"}

        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert response.json()["detail"] in [
            "Incorrect username or password",
            "用户名或密码错误",
        ]

        # 不存在的用户
        login_data = {"username": "nonexistent", "password": "SomePassword123!"}

        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert response.json()["detail"] in [
            "Incorrect username or password",
            "用户名或密码错误",
        ]

    async def test_token_refresh_flow(self, client: AsyncClient, test_user):
        """测试令牌刷新流程。"""
        # test_user fixture 确保测试用户已创建
        assert test_user is not None
        # 1. 登录获取令牌
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "TestPass123!"},
        )
        assert login_response.status_code == 200
        tokens = login_response.json()

        # 2. 使用刷新令牌获取新的访问令牌
        refresh_response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        # Note: The new token might be the same if the old one hasn't expired yet
        # But we at least verify the refresh endpoint works

        # 3. 验证新令牌可用
        headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
        me_response = await client.get("/api/v1/users/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "testuser"

    async def test_protected_endpoint_access(self, client: AsyncClient, auth_headers):
        """测试受保护端点的访问。"""
        # 1. 无令牌访问（应该失败）
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

        # 2. 使用有效令牌访问
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["username"] == "testuser"

        # 3. 使用无效令牌访问
        bad_headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/api/v1/users/me", headers=bad_headers)
        assert response.status_code == 401

    async def test_logout_flow(self, client: AsyncClient, auth_headers):
        """测试登出流程。"""
        # 1. 验证令牌有效
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200

        # 2. 登出
        response = await client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] in ["Successfully logged out", "登出成功"]

        # 注意：由于JWT是无状态的，登出后令牌仍然有效，直到过期
        # 实际的登出需要前端删除令牌
        # 3. 验证令牌仍然有效（这是JWT的特性）
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200

    async def test_change_password_flow(self, client: AsyncClient, auth_headers):
        """测试修改密码流程。"""
        # 1. 修改密码
        change_data = {
            "old_password": "TestPass123!",
            "new_password": "NewPass456!",
        }

        response = await client.post(
            "/api/v1/auth/change-password", json=change_data, headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] in [
            "Password updated successfully",
            "密码修改成功",
        ]

        # 2. 使用旧密码登录（应该失败）
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "TestPass123!"},
        )
        assert login_response.status_code == 401

        # 3. 使用新密码登录
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "NewPass456!"},
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()

    async def test_premium_user_access(self, client: AsyncClient, premium_auth_headers):
        """测试高级用户访问权限。"""
        # 访问需要高级权限的端点
        response = await client.get("/api/v1/users/me", headers=premium_auth_headers)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["is_premium"] is True

        # TODO: 添加更多高级用户特定功能的测试


@pytest.mark.asyncio
class TestUserManagement:
    """测试用户管理功能。"""

    async def test_update_user_profile(self, client: AsyncClient, auth_headers):
        """测试更新用户资料。"""
        update_data = {
            "full_name": "Updated Name",
            "avatar_url": "https://example.com/avatar.jpg",
        }

        response = await client.put(
            "/api/v1/users/me", json=update_data, headers=auth_headers
        )
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["full_name"] == "Updated Name"
        assert updated_user["avatar_url"] == "https://example.com/avatar.jpg"

    async def test_user_deactivation(
        self, client: AsyncClient, auth_headers, db_session: AsyncSession
    ):
        """测试用户停用功能。"""
        # db_session 用于直接数据库操作
        assert db_session is not None

        # 获取当前用户信息
        me_response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert me_response.status_code == 200
        # user_id = me_response.json()["id"]  # TODO: 当实现停用账户功能时使用

        # 停用账户
        # TODO: 实现停用账户的端点

        # 验证无法登录
        # TODO: 验证停用后的行为
