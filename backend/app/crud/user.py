"""User CRUD operations."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.models import User
from app.schemas.users import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations for User model."""

    async def create(
        self, db: AsyncSession, *, obj_in: UserCreate, **kwargs
    ) -> User:
        """Create a new user with hashed password."""
        # Extract password and remove it from the data
        create_data = obj_in.model_dump()
        password = create_data.pop("password")

        # For testing, we'll use a simple hash (in production, use bcrypt)
        hashed_password = f"hashed_{password}"

        # Create user with hashed password
        db_obj = User(**create_data, hashed_password=hashed_password, **kwargs)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_email(self, db: AsyncSession, *, email: str) -> User | None:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(
        self, db: AsyncSession, *, username: str
    ) -> User | None:
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
        user.last_login = datetime.now(UTC)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


# Create single instance
crud_user = CRUDUser(User)
