"""Space CRUD operations."""

from typing import List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.models import Space, SpaceCollaboration, User
from app.schemas.spaces import SpaceCreate, SpaceUpdate


class CRUDSpace(CRUDBase[Space, SpaceCreate, SpaceUpdate]):
    """CRUD operations for Space model."""

    async def get_user_spaces(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        include_public: bool = False,
    ) -> List[Space]:
        """Get spaces for a specific user."""
        query = select(Space).where(Space.user_id == user_id)
        
        if include_public:
            query = select(Space).where(
                (Space.user_id == user_id) | (Space.is_public == True)
            )
        
        query = query.order_by(Space.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_name(
        self, db: AsyncSession, *, name: str, user_id: int
    ) -> Optional[Space]:
        """Get space by name for a specific user."""
        result = await db.execute(
            select(Space).where(
                and_(Space.name == name, Space.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def update_stats(
        self,
        db: AsyncSession,
        *,
        space_id: int,
        document_delta: int = 0,
        note_delta: int = 0,
        size_delta: int = 0,
    ) -> Optional[Space]:
        """Update space statistics."""
        space = await self.get(db, space_id)
        if space:
            space.document_count += document_delta
            space.note_count += note_delta
            space.total_size += size_delta
            await db.commit()
            await db.refresh(space)
        return space

    async def get_collaborations(
        self, db: AsyncSession, *, space_id: int
    ) -> List[SpaceCollaboration]:
        """Get all collaborations for a space."""
        result = await db.execute(
            select(SpaceCollaboration)
            .where(SpaceCollaboration.space_id == space_id)
            .order_by(SpaceCollaboration.created_at)
        )
        return result.scalars().all()

    async def add_collaborator(
        self,
        db: AsyncSession,
        *,
        space_id: int,
        user_id: int,
        invited_by: int,
        role: str = "viewer",
        can_edit: bool = False,
        can_delete: bool = False,
        can_invite: bool = False,
    ) -> SpaceCollaboration:
        """Add a collaborator to a space."""
        collaboration = SpaceCollaboration(
            space_id=space_id,
            user_id=user_id,
            invited_by=invited_by,
            role=role,
            can_edit=can_edit,
            can_delete=can_delete,
            can_invite=can_invite,
        )
        db.add(collaboration)
        await db.commit()
        await db.refresh(collaboration)
        return collaboration

    async def get_user_access(
        self, db: AsyncSession, *, space_id: int, user_id: int
    ) -> Optional[SpaceCollaboration]:
        """Check if user has access to a space."""
        result = await db.execute(
            select(SpaceCollaboration).where(
                and_(
                    SpaceCollaboration.space_id == space_id,
                    SpaceCollaboration.user_id == user_id,
                    SpaceCollaboration.status == "active",
                )
            )
        )
        return result.scalar_one_or_none()


# Create single instance
space = CRUDSpace(Space)