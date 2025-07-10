"""User CRUD operations."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.models import User
from app.schemas.users import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations for User model."""

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(
        self, db: AsyncSession, *, username: str
    ) -> Optional[User]:
        """Get user by username."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active

    async def is_premium(self, user: User) -> bool:
        """Check if user is premium."""
        return user.is_premium

    async def update_last_login(self, db: AsyncSession, *, user: User) -> User:
        """Update user's last login time."""
        from datetime import datetime

        user.last_login = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        return user


# Create single instance
user = CRUDUser(User)