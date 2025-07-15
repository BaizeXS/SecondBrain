"""Simplified unit tests for document CRUD operations.

To run these tests:
    uv run pytest tests/unit/crud/test_document_simple.py -v
"""

import hashlib

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.document import crud_document
from app.crud.space import crud_space
from app.crud.user import crud_user
from app.schemas.documents import DocumentCreate, DocumentUpdate
from app.schemas.spaces import SpaceCreate
from app.schemas.users import UserCreate


@pytest.fixture
async def test_user(async_test_db: AsyncSession):
    """Create a test user."""
    user_in = UserCreate(
        username="documentuser",
        email="documentuser@example.com",
        password="password123",
        full_name="Document User"
    )
    user = await crud_user.create(async_test_db, obj_in=user_in)
    return user


@pytest.fixture
async def test_space(async_test_db: AsyncSession, test_user):
    """Create a test space."""
    space_in = SpaceCreate(
        name="Test Document Space",
        description="A space for testing documents"
    )  # type: ignore
    space = await crud_space.create(async_test_db, obj_in=space_in, user_id=test_user.id)
    return space


class TestCRUDDocument:
    """Simplified test suite for Document CRUD operations."""

    async def test_create_and_get_document(self, async_test_db: AsyncSession, test_user, test_space):
        """Test creating and retrieving a document."""
        # Create document
        doc_in = DocumentCreate(
            filename="test.pdf",
            content_type="application/pdf",
            size=1024,
            space_id=test_space.id,
            description="Test document",
            tags=["test"]
        )  # type: ignore

        document = await crud_document.create(
            async_test_db,
            obj_in=doc_in,
            user_id=test_user.id,
            file_path=f"spaces/{test_space.id}/test.pdf",
            file_hash=hashlib.sha256(b"test").hexdigest()
        )

        # Verify creation
        assert document.id is not None
        assert document.filename == "test.pdf"
        assert document.file_size == 1024
        assert document.space_id == test_space.id
        assert document.user_id == test_user.id

        # Test get
        retrieved = await crud_document.get(async_test_db, document.id)
        assert retrieved is not None
        assert retrieved.id == document.id

    async def test_get_by_space(self, async_test_db: AsyncSession, test_user, test_space):
        """Test getting documents by space."""
        # Create multiple documents
        for i in range(3):
            doc_in = DocumentCreate(
                filename=f"doc_{i}.pdf",
                content_type="application/pdf",
                size=1000,
                space_id=test_space.id
            )  # type: ignore
            await crud_document.create(
                async_test_db,
                obj_in=doc_in,
                user_id=test_user.id,
                file_path=f"spaces/{test_space.id}/doc_{i}.pdf",
                file_hash=hashlib.sha256(f"doc_{i}".encode()).hexdigest()
            )

        # Get documents
        documents = await crud_document.get_by_space(
            async_test_db, space_id=test_space.id
        )
        assert len(documents) == 3

    async def test_get_by_hash(self, async_test_db: AsyncSession, test_user, test_space):
        """Test getting document by file hash."""
        file_hash = hashlib.sha256(b"unique").hexdigest()

        # Create document
        doc_in = DocumentCreate(
            filename="unique.pdf",
            content_type="application/pdf",
            size=2000,
            space_id=test_space.id
        )  # type: ignore

        await crud_document.create(
            async_test_db,
            obj_in=doc_in,
            user_id=test_user.id,
            file_path=f"spaces/{test_space.id}/unique.pdf",
            file_hash=file_hash
        )

        # Find by hash
        found = await crud_document.get_by_hash(
            async_test_db, file_hash=file_hash, space_id=test_space.id
        )
        assert found is not None
        assert found.file_hash == file_hash

    async def test_search_documents(self, async_test_db: AsyncSession, test_user, test_space):
        """Test searching documents."""
        # Create document with searchable content
        doc_in = DocumentCreate(
            filename="python_guide.pdf",
            content_type="application/pdf",
            size=5000,
            space_id=test_space.id
        )  # type: ignore

        await crud_document.create(
            async_test_db,
            obj_in=doc_in,
            user_id=test_user.id,
            file_path=f"spaces/{test_space.id}/python_guide.pdf",
            file_hash=hashlib.sha256(b"python").hexdigest(),
            title="Python Programming Guide",
            content="Learn Python programming"
        )

        # Search by title/content
        results = await crud_document.search(
            async_test_db, space_id=test_space.id, query="Python"
        )
        assert len(results) == 1
        assert results[0].title == "Python Programming Guide"

    async def test_update_processing_status(self, async_test_db: AsyncSession, test_user, test_space):
        """Test updating document processing status."""
        # Create document
        doc_in = DocumentCreate(
            filename="processing.pdf",
            content_type="application/pdf",
            size=1000,
            space_id=test_space.id
        )  # type: ignore

        document = await crud_document.create(
            async_test_db,
            obj_in=doc_in,
            user_id=test_user.id,
            file_path=f"spaces/{test_space.id}/processing.pdf",
            file_hash=hashlib.sha256(b"processing").hexdigest()
        )

        # Check initial status
        assert document.processing_status == "pending"

        # Update status
        updated = await crud_document.update_processing_status(
            async_test_db,
            document_id=document.id,
            processing_status="completed",
            extraction_status="completed",
            embedding_status="completed"
        )

        assert updated is not None
        assert updated.processing_status == "completed"
        assert updated.extraction_status == "completed"
        assert updated.embedding_status == "completed"

    async def test_parent_child_documents(self, async_test_db: AsyncSession, test_user, test_space):
        """Test parent-child document relationships."""
        # Create parent
        parent_in = DocumentCreate(
            filename="original.pdf",
            content_type="application/pdf",
            size=1000,
            space_id=test_space.id
        )  # type: ignore

        parent = await crud_document.create(
            async_test_db,
            obj_in=parent_in,
            user_id=test_user.id,
            file_path=f"spaces/{test_space.id}/original.pdf",
            file_hash=hashlib.sha256(b"original").hexdigest()
        )

        # Create child (translation)
        child_in = DocumentCreate(
            filename="translation.pdf",
            content_type="application/pdf",
            size=1100,
            space_id=test_space.id
        )  # type: ignore

        await crud_document.create(
            async_test_db,
            obj_in=child_in,
            user_id=test_user.id,
            file_path=f"spaces/{test_space.id}/translation.pdf",
            file_hash=hashlib.sha256(b"translation").hexdigest(),
            parent_id=parent.id,
            language="fr"
        )

        # Get children
        children = await crud_document.get_by_parent(
            async_test_db, parent_id=parent.id
        )
        assert len(children) == 1
        assert children[0].language == "fr"

    async def test_update_document(self, async_test_db: AsyncSession, test_user, test_space):
        """Test updating a document."""
        # Create document
        doc_in = DocumentCreate(
            filename="to_update.pdf",
            content_type="application/pdf",
            size=1000,
            space_id=test_space.id
        )  # type: ignore

        document = await crud_document.create(
            async_test_db,
            obj_in=doc_in,
            user_id=test_user.id,
            file_path=f"spaces/{test_space.id}/to_update.pdf",
            file_hash=hashlib.sha256(b"update").hexdigest()
        )

        # Update
        update_data = DocumentUpdate(
            description="Updated description",
            tags=["updated", "test"]
        )  # type: ignore

        updated = await crud_document.update(
            async_test_db, db_obj=document, obj_in=update_data
        )

        assert updated.tags == ["updated", "test"]

    async def test_delete_document(self, async_test_db: AsyncSession, test_user, test_space):
        """Test deleting a document."""
        # Create document
        doc_in = DocumentCreate(
            filename="to_delete.pdf",
            content_type="application/pdf",
            size=1000,
            space_id=test_space.id
        )  # type: ignore

        document = await crud_document.create(
            async_test_db,
            obj_in=doc_in,
            user_id=test_user.id,
            file_path=f"spaces/{test_space.id}/to_delete.pdf",
            file_hash=hashlib.sha256(b"delete").hexdigest()
        )

        # Delete
        deleted = await crud_document.remove(async_test_db, id=document.id)
        assert deleted is not None

        # Verify
        retrieved = await crud_document.get(async_test_db, document.id)
        assert retrieved is None
