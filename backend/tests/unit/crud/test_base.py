"""Unit tests for base CRUD operations.

To run these tests:
    # Run all tests in this file
    uv run pytest tests/test_crud_base.py -v

    # Run a specific test
    uv run pytest tests/test_crud_base.py::_TestCRUDBase::test_create -v

    # Run with coverage
    uv run pytest tests/test_crud_base.py --cov=app.crud.base
"""

import pytest
from pydantic import BaseModel
from sqlalchemy import Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.crud.base import CRUDBase


# Test models
class _TestModel(Base):
    """Test model for CRUD operations."""
    __tablename__ = "test_model"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)


class _TestCreateSchema(BaseModel):
    """Schema for creating test records."""
    name: str
    description: str | None = None


class _TestUpdateSchema(BaseModel):
    """Schema for updating test records."""
    name: str | None = None
    description: str | None = None


# Test CRUD class
class _TestCRUD(CRUDBase[_TestModel, _TestCreateSchema, _TestUpdateSchema]):
    """Test CRUD implementation."""
    pass


# Fixtures
@pytest.fixture
async def async_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.fixture
def crud_test():
    """Create a test CRUD instance."""
    return _TestCRUD(_TestModel)


# Tests
class TestCRUDBase:
    """Test suite for CRUDBase."""

    async def test_create(self, async_db: AsyncSession, crud_test: _TestCRUD):
        """Test creating a record."""
        # Create test data
        obj_in = _TestCreateSchema(name="Test Item", description="Test Description")

        # Create record
        db_obj = await crud_test.create(async_db, obj_in=obj_in)

        # Assertions
        assert db_obj.id is not None
        assert db_obj.name == "Test Item"
        assert db_obj.description == "Test Description"

    async def test_get(self, async_db: AsyncSession, crud_test: _TestCRUD):
        """Test getting a record by ID."""
        # Create a record first
        obj_in = _TestCreateSchema(name="Test Item")
        created = await crud_test.create(async_db, obj_in=obj_in)

        # Get the record
        retrieved = await crud_test.get(async_db, created.id)

        # Assertions
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    async def test_get_nonexistent(self, async_db: AsyncSession, crud_test: _TestCRUD):
        """Test getting a non-existent record."""
        result = await crud_test.get(async_db, 9999)
        assert result is None

    async def test_get_multi(self, async_db: AsyncSession, crud_test: _TestCRUD):
        """Test getting multiple records."""
        # Create multiple records
        for i in range(5):
            obj_in = _TestCreateSchema(name=f"Item {i}")
            await crud_test.create(async_db, obj_in=obj_in)

        # Get records with pagination
        items = await crud_test.get_multi(async_db, skip=1, limit=3)

        # Assertions
        assert len(items) == 3
        assert items[0].name == "Item 1"
        assert items[-1].name == "Item 3"

    async def test_get_count(self, async_db: AsyncSession, crud_test: _TestCRUD):
        """Test counting records."""
        # Create records
        for i in range(3):
            obj_in = _TestCreateSchema(name=f"Item {i}")
            await crud_test.create(async_db, obj_in=obj_in)

        # Get count
        count = await crud_test.get_count(async_db)

        # Assertion
        assert count == 3

    async def test_update(self, async_db: AsyncSession, crud_test: _TestCRUD):
        """Test updating a record."""
        # Create a record
        obj_in = _TestCreateSchema(name="Original", description="Original Desc")
        created = await crud_test.create(async_db, obj_in=obj_in)

        # Update using schema
        update_data = _TestUpdateSchema(name="Updated")
        updated = await crud_test.update(
            async_db, db_obj=created, obj_in=update_data
        )

        # Assertions
        assert updated.name == "Updated"
        assert updated.description == "Original Desc"  # Should remain unchanged

    async def test_update_with_dict(self, async_db: AsyncSession, crud_test: _TestCRUD):
        """Test updating a record with dictionary."""
        # Create a record
        obj_in = _TestCreateSchema(name="Original")
        created = await crud_test.create(async_db, obj_in=obj_in)

        # Update using dict
        update_dict = {"name": "Updated", "description": "New Desc"}
        updated = await crud_test.update(
            async_db, db_obj=created, obj_in=update_dict
        )

        # Assertions
        assert updated.name == "Updated"
        assert updated.description == "New Desc"

    async def test_remove(self, async_db: AsyncSession, crud_test: _TestCRUD):
        """Test deleting a record."""
        # Create a record
        obj_in = _TestCreateSchema(name="To Delete")
        created = await crud_test.create(async_db, obj_in=obj_in)

        # Delete the record
        deleted = await crud_test.remove(async_db, id=created.id)

        # Verify deletion
        assert deleted is not None
        assert deleted.id == created.id

        # Verify it's gone
        retrieved = await crud_test.get(async_db, created.id)
        assert retrieved is None

    async def test_remove_nonexistent(self, async_db: AsyncSession, crud_test: _TestCRUD):
        """Test deleting a non-existent record."""
        result = await crud_test.remove(async_db, id=9999)
        assert result is None

    async def test_exists(self, async_db: AsyncSession, crud_test: _TestCRUD):
        """Test checking if a record exists."""
        # Create a record
        obj_in = _TestCreateSchema(name="Exists")
        created = await crud_test.create(async_db, obj_in=obj_in)

        # Check existence
        exists = await crud_test.exists(async_db, id=created.id)
        not_exists = await crud_test.exists(async_db, id=9999)

        # Assertions
        assert exists is True
        assert not_exists is False

    async def test_create_with_kwargs(self, async_db: AsyncSession, crud_test: _TestCRUD):
        """Test creating a record with additional kwargs."""
        # Create with extra fields
        obj_in = _TestCreateSchema(name="Test")
        db_obj = await crud_test.create(
            async_db, obj_in=obj_in, description="Added via kwargs"
        )

        # Assertions
        assert db_obj.name == "Test"
        assert db_obj.description == "Added via kwargs"
