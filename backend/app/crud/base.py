"""Base CRUD class with common database operations."""

from typing import Any, Generic, TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base class for CRUD operations."""

    def __init__(self, model: type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        Args:
            model: A SQLAlchemy model class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> ModelType | None:
        """Get a single record by ID."""
        result = await db.execute(select(self.model).where(self.model.id == id))  # type: ignore[attr-defined]
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        query: Select | None = None,
    ) -> list[ModelType]:
        """Get multiple records."""
        if query is None:
            query = select(self.model)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_count(
        self, db: AsyncSession, *, query: Select | None = None
    ) -> int:
        """Get total count of records."""
        if query is None:
            query = select(func.count()).select_from(self.model)
        else:
            query = select(func.count()).select_from(query.subquery())
        result = await db.execute(query)
        return result.scalar() or 0

    async def create(
        self, db: AsyncSession, *, obj_in: CreateSchemaType, **kwargs
    ) -> ModelType:
        """Create a new record."""
        obj_in_data = jsonable_encoder(obj_in)
        obj_in_data.update(kwargs)
        db_obj = self.model(**obj_in_data)  # type: ignore[call-arg]
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        """Update a record."""
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> ModelType | None:
        """Delete a record."""
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def exists(self, db: AsyncSession, id: Any) -> bool:
        """Check if a record exists."""
        query = select(self.model.id).where(self.model.id == id)  # type: ignore[attr-defined]
        result = await db.execute(query)
        return result.scalar() is not None
