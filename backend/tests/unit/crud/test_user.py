"""Unit tests for user CRUD operations.

To run these tests:
    uv run pytest tests/unit/crud/test_user.py -v
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import crud_user
from app.schemas.users import UserCreate, UserUpdate


@pytest.fixture
async def test_user_data():
    """Test user data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "securepassword123"
    }


class TestCRUDUser:
    """Test suite for User CRUD operations."""

    async def test_create_user(self, async_test_db: AsyncSession, test_user_data):
        """Test creating a user."""
        # Create user
        user_in = UserCreate(**test_user_data)
        user = await crud_user.create(async_test_db, obj_in=user_in)

        # Assertions
        assert user.username == test_user_data["username"]
        assert user.email == test_user_data["email"]
        assert user.full_name == test_user_data["full_name"]
        assert user.is_active is True
        assert user.is_premium is False
        assert user.id is not None

    async def test_get_user_by_email(self, async_test_db: AsyncSession, test_user_data):
        """Test getting user by email."""
        # Create user first
        user_in = UserCreate(**test_user_data)
        created_user = await crud_user.create(async_test_db, obj_in=user_in)

        # Get by email
        user = await crud_user.get_by_email(
            async_test_db, email=test_user_data["email"]
        )

        # Assertions
        assert user is not None
        assert user.id == created_user.id
        assert user.email == test_user_data["email"]

    async def test_get_user_by_email_not_found(self, async_test_db: AsyncSession):
        """Test getting non-existent user by email."""
        user = await crud_user.get_by_email(
            async_test_db, email="nonexistent@example.com"
        )
        assert user is None

    async def test_get_user_by_username(self, async_test_db: AsyncSession, test_user_data):
        """Test getting user by username."""
        # Create user first
        user_in = UserCreate(**test_user_data)
        created_user = await crud_user.create(async_test_db, obj_in=user_in)

        # Get by username
        user = await crud_user.get_by_username(
            async_test_db, username=test_user_data["username"]
        )

        # Assertions
        assert user is not None
        assert user.id == created_user.id
        assert user.username == test_user_data["username"]

    async def test_update_user(self, async_test_db: AsyncSession, test_user_data):
        """Test updating a user."""
        # Create user
        user_in = UserCreate(**test_user_data)
        user = await crud_user.create(async_test_db, obj_in=user_in)

        # Update user
        update_data = UserUpdate(
            full_name="Updated Name",
            avatar_url="https://example.com/avatar.jpg"
        ) # type: ignore
        updated_user = await crud_user.update(
            async_test_db, db_obj=user, obj_in=update_data
        )

        # Assertions
        assert updated_user.full_name == "Updated Name"
        assert updated_user.avatar_url == "https://example.com/avatar.jpg"
        assert updated_user.username == test_user_data["username"]  # Unchanged

    async def test_delete_user(self, async_test_db: AsyncSession, test_user_data):
        """Test deleting a user."""
        # Create user
        user_in = UserCreate(**test_user_data)
        user = await crud_user.create(async_test_db, obj_in=user_in)

        # Delete user
        deleted_user = await crud_user.remove(async_test_db, id=user.id)

        # Assertions
        assert deleted_user is not None
        assert deleted_user.id == user.id

        # Verify user is deleted
        user_check = await crud_user.get(async_test_db, user.id)
        assert user_check is None

    async def test_is_active(self, async_test_db: AsyncSession, test_user_data):
        """Test checking if user is active."""
        # Create user
        user_in = UserCreate(**test_user_data)
        user = await crud_user.create(async_test_db, obj_in=user_in)

        # Check is_active
        is_active = await crud_user.is_active(user)
        assert is_active is True

    async def test_is_premium(self, async_test_db: AsyncSession, test_user_data):
        """Test checking if user is premium."""
        # Create user
        user_in = UserCreate(**test_user_data)
        user = await crud_user.create(async_test_db, obj_in=user_in)

        # Check is_premium
        is_premium = await crud_user.is_premium(user)
        assert is_premium is False

    async def test_update_last_login(self, async_test_db: AsyncSession, test_user_data):
        """Test updating user's last login time."""
        # Create user
        user_in = UserCreate(**test_user_data)
        user = await crud_user.create(async_test_db, obj_in=user_in)

        # Initial last_login should be None
        assert user.last_login is None

        # Update last login
        updated_user = await crud_user.update_last_login(async_test_db, user=user)

        # Assertions
        assert updated_user.last_login is not None
        # Just check that it's recent (within last minute)
        time_diff = datetime.now(UTC) - updated_user.last_login.replace(tzinfo=UTC)
        assert time_diff.total_seconds() < 60

    async def test_create_duplicate_email(self, async_test_db: AsyncSession, test_user_data):
        """Test creating user with duplicate email."""
        # Create first user
        user_in = UserCreate(**test_user_data)
        await crud_user.create(async_test_db, obj_in=user_in)

        # Try to create another user with same email
        duplicate_user_data = test_user_data.copy()
        duplicate_user_data["username"] = "anotheruser"
        duplicate_user_in = UserCreate(**duplicate_user_data)

        # This should raise an exception due to unique constraint
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            await crud_user.create(async_test_db, obj_in=duplicate_user_in)

    async def test_create_duplicate_username(self, async_test_db: AsyncSession, test_user_data):
        """Test creating user with duplicate username."""
        # Create first user
        user_in = UserCreate(**test_user_data)
        await crud_user.create(async_test_db, obj_in=user_in)

        # Try to create another user with same username
        duplicate_user_data = test_user_data.copy()
        duplicate_user_data["email"] = "another@example.com"
        duplicate_user_in = UserCreate(**duplicate_user_data)

        # This should raise an exception due to unique constraint
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            await crud_user.create(async_test_db, obj_in=duplicate_user_in)

    async def test_get_multi_users(self, async_test_db: AsyncSession):
        """Test getting multiple users."""
        # Create multiple users
        for i in range(5):
            user_in = UserCreate(
                username=f"user{i}",
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                password="password123"
            )
            await crud_user.create(async_test_db, obj_in=user_in)

        # Get users with pagination
        users = await crud_user.get_multi(async_test_db, skip=1, limit=3)

        # Assertions
        assert len(users) == 3
        assert users[0].username == "user1"
        assert users[-1].username == "user3"

    async def test_count_users(self, async_test_db: AsyncSession):
        """Test counting users."""
        # Create users
        for i in range(3):
            user_in = UserCreate(
                username=f"countuser{i}",
                email=f"count{i}@example.com",
                full_name=f"Count User {i}",
                password="password123"
            )
            await crud_user.create(async_test_db, obj_in=user_in)

        # Get count
        count = await crud_user.get_count(async_test_db)
        assert count == 3
