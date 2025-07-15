"""Unit tests for document CRUD operations.

To run these tests:
    uv run pytest tests/unit/crud/test_document.py -v
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


def create_doc_schema(filename: str, space_id: int, **kwargs):
    """Helper to create DocumentCreate with defaults."""
    defaults = {
        "content_type": "application/pdf",
        "size": 1000
    }
    defaults.update(kwargs)
    return DocumentCreate(
        filename=filename,
        space_id=space_id,
        **defaults
    )  # type: ignore


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
    """Test suite for Document CRUD operations."""

    async def test_create_document(self, async_test_db: AsyncSession, test_user, test_space):
        """Test creating a document."""
        doc_in = DocumentCreate(
            filename="test_document.pdf",
            content_type="application/pdf",
            size=1024000,  # 1MB
            space_id=test_space.id,
            description="A test document",
            tags=["test", "pdf"]
        )  # type: ignore

        document = await crud_document.create(
            async_test_db,
            obj_in=doc_in,
            user_id=test_user.id,
            file_path="spaces/1/documents/test_document.pdf",
            file_hash=hashlib.sha256(b"test content").hexdigest(),
            original_filename="My Test Document.pdf",
            title="Test Document",
            content="This is a test document content",
            summary="A brief summary of the test document",
            language="en"
        )

        # Assertions
        assert document.id is not None
        assert document.filename == "test_document.pdf"
        assert document.original_filename == "My Test Document.pdf"
        assert document.user_id == test_user.id
        assert document.space_id == test_space.id
        assert document.file_size == 1024000
        assert document.content_type == "application/pdf"
        assert document.processing_status == "pending"
        assert document.extraction_status == "pending"
        assert document.embedding_status == "pending"
        assert document.tags == ["test", "pdf"]
        assert document.title == "Test Document"
        assert document.content == "This is a test document content"
        assert document.summary == "A brief summary of the test document"
        assert document.language == "en"

    async def test_create_minimal_document(self, async_test_db: AsyncSession, test_user, test_space):
        """Test creating a document with minimal data."""
        doc_in = DocumentCreate(
            filename="minimal.txt",
            content_type="text/plain",
            size=100,
            space_id=test_space.id
        )  # type: ignore

        document = await crud_document.create(
            async_test_db,
            obj_in=doc_in,
            user_id=test_user.id,
            file_path="spaces/1/documents/minimal.txt",
            file_hash=hashlib.sha256(b"minimal").hexdigest()
        )

        assert document.id is not None
        assert document.title is None
        assert document.content is None
        assert document.summary is None
        assert document.language is None
        assert document.tags is None

    async def test_get_by_space(self, async_test_db: AsyncSession, test_user, test_space):
        """Test getting documents by space."""
        # Create multiple documents
        for i in range(5):
            doc_in = create_doc_schema(f"doc_{i}.pdf", test_space.id, size=1000 + i)
            await crud_document.create(
                async_test_db,
                obj_in=doc_in,
                user_id=test_user.id,
                file_path=f"spaces/{test_space.id}/documents/doc_{i}.pdf",
                file_hash=hashlib.sha256(f"content_{i}".encode()).hexdigest()
            )

        # Get all documents in space
        documents = await crud_document.get_by_space(
            async_test_db, space_id=test_space.id
        )
        assert len(documents) == 5

        # Test pagination
        first_page = await crud_document.get_by_space(
            async_test_db, space_id=test_space.id, skip=0, limit=3
        )
        assert len(first_page) == 3

        second_page = await crud_document.get_by_space(
            async_test_db, space_id=test_space.id, skip=3, limit=3
        )
        assert len(second_page) == 2

    async def test_get_by_space_with_status_filter(self, async_test_db: AsyncSession, test_user, test_space):
        """Test filtering documents by processing status."""
        # Create documents with different statuses
        statuses = ["pending", "processing", "completed", "failed"]
        for status in statuses:
            doc_in = DocumentCreate(
                filename=f"doc_{status}.pdf",
                content_type="application/pdf",
                size=1000,
                space_id=test_space.id
            )  # type: ignore
            doc = await crud_document.create(
                async_test_db,
                obj_in=doc_in,
                user_id=test_user.id,
                file_path=f"spaces/{test_space.id}/documents/doc_{status}.pdf",
                file_hash=hashlib.sha256(f"content_{status}".encode()).hexdigest(),
                original_filename=f"Document {status}.pdf"
            )
            # Update status
            await crud_document.update_processing_status(
                async_test_db,
                document_id=doc.id,
                processing_status=status
            )

        # Get only completed documents
        completed = await crud_document.get_by_space(
            async_test_db, space_id=test_space.id, status="completed"
        )
        assert len(completed) == 1
        assert completed[0].processing_status == "completed"

        # Get only failed documents
        failed = await crud_document.get_by_space(
            async_test_db, space_id=test_space.id, status="failed"
        )
        assert len(failed) == 1
        assert failed[0].processing_status == "failed"

    async def test_get_by_hash(self, async_test_db: AsyncSession, test_user, test_space):
        """Test getting document by file hash."""
        # Create a document
        file_hash = hashlib.sha256(b"unique content").hexdigest()
        doc_in = DocumentCreate(
            filename="unique.pdf",
            content_type="application/pdf",
            size=2000,
            space_id=test_space.id
        )  # type: ignore

        created = await crud_document.create(
            async_test_db,
            obj_in=doc_in,
            user_id=test_user.id,
            file_path="spaces/1/documents/unique.pdf",
            file_hash=file_hash,
            original_filename="Unique Document.pdf"
        )

        # Get by hash
        found = await crud_document.get_by_hash(
            async_test_db, file_hash=file_hash, space_id=test_space.id
        )
        assert found is not None
        assert found.id == created.id
        assert found.file_hash == file_hash

        # Try non-existent hash
        not_found = await crud_document.get_by_hash(
            async_test_db, file_hash="nonexistent", space_id=test_space.id
        )
        assert not_found is None

    async def test_search_documents(self, async_test_db: AsyncSession, test_user, test_space):
        """Test searching documents."""
        # Create documents with searchable content
        documents_data = [
            {
                "filename": "python_guide.pdf",
                "title": "Python Programming Guide",
                "content": "Learn Python programming from basics to advanced"
            },
            {
                "filename": "javascript_tutorial.pdf",
                "title": "JavaScript Tutorial",
                "content": "Modern JavaScript development techniques"
            },
            {
                "filename": "python_advanced.pdf",
                "title": "Advanced Python Techniques",
                "content": "Deep dive into Python internals"
            },
            {
                "filename": "data_science.pdf",
                "title": "Data Science with Python",
                "content": "Using Python for data analysis"
            }
        ]

        for data in documents_data:
            doc_in = DocumentCreate(
                filename=data["filename"],
                content_type="application/pdf",
                size=1000,
                space_id=test_space.id
            )  # type: ignore
            await crud_document.create(
                async_test_db,
                obj_in=doc_in,
                user_id=test_user.id,
                file_path=f"spaces/{test_space.id}/documents/{data['filename']}",
                file_hash=hashlib.sha256(data["filename"].encode()).hexdigest(),
                original_filename=data["filename"],
                title=data["title"],
                content=data["content"]
            )

        # Search for Python
        python_results = await crud_document.search(
            async_test_db, space_id=test_space.id, query="Python"
        )
        assert len(python_results) == 3

        # Search by filename
        guide_results = await crud_document.search(
            async_test_db, space_id=test_space.id, query="guide"
        )
        assert len(guide_results) == 1
        assert guide_results[0].filename == "python_guide.pdf"

        # Search in content
        analysis_results = await crud_document.search(
            async_test_db, space_id=test_space.id, query="analysis"
        )
        assert len(analysis_results) == 1
        assert analysis_results[0].content is not None
        assert "data analysis" in analysis_results[0].content

    async def test_update_processing_status(self, async_test_db: AsyncSession, test_user, test_space):
        """Test updating document processing status."""
        # Create a document
        doc_in = DocumentCreate(
            filename="processing_test.pdf",
            content_type="application/pdf",
            size=1000,
            space_id=test_space.id
        )  # type: ignore

        document = await crud_document.create(
            async_test_db,
            obj_in=doc_in,
            user_id=test_user.id,
            file_path="spaces/1/documents/processing_test.pdf",
            file_hash=hashlib.sha256(b"processing").hexdigest(),
            original_filename="Processing Test.pdf"
        )

        # Initial status should be pending
        assert document.processing_status == "pending"
        assert document.extraction_status == "pending"
        assert document.embedding_status == "pending"

        # Update to processing
        updated = await crud_document.update_processing_status(
            async_test_db,
            document_id=document.id,
            processing_status="processing",
            extraction_status="processing"
        )
        assert updated is not None
        assert updated.processing_status == "processing"
        assert updated.extraction_status == "processing"
        assert updated.embedding_status == "pending"  # Not updated

        # Update to completed
        completed = await crud_document.update_processing_status(
            async_test_db,
            document_id=document.id,
            processing_status="completed",
            extraction_status="completed",
            embedding_status="completed"
        )
        assert completed is not None
        assert completed.processing_status == "completed"
        assert completed.extraction_status == "completed"
        assert completed.embedding_status == "completed"

    async def test_parent_child_documents(self, async_test_db: AsyncSession, test_user, test_space):
        """Test parent-child document relationships."""
        # Create parent document
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
            file_path="spaces/1/documents/original.pdf",
            file_hash=hashlib.sha256(b"original").hexdigest(),
            original_filename="Original Document.pdf",
            language="en"
        )

        # Create child documents (translations)
        languages = ["fr", "es", "de"]
        for lang in languages:
            child_in = DocumentCreate(
                filename=f"translated_{lang}.pdf",
                content_type="application/pdf",
                size=1100,
                space_id=test_space.id
            )  # type: ignore
            await crud_document.create(
                async_test_db,
                obj_in=child_in,
                user_id=test_user.id,
                file_path=f"spaces/1/documents/translated_{lang}.pdf",
                file_hash=hashlib.sha256(f"translated_{lang}".encode()).hexdigest(),
                original_filename=f"Translated Document {lang}.pdf",
                language=lang,
                parent_id=parent.id
            )

        # Get children
        children = await crud_document.get_by_parent(
            async_test_db, parent_id=parent.id
        )
        assert len(children) == 3
        child_languages = {child.language for child in children}
        assert child_languages == {"fr", "es", "de"}

    async def test_get_user_documents(self, async_test_db: AsyncSession, test_user, test_space):
        """Test getting all documents by user."""
        # Create another user and space
        other_user_in = UserCreate(
            username="otheruser",
            email="other@example.com",
            password="password123",
            full_name="Other User"
        )
        other_user = await crud_user.create(async_test_db, obj_in=other_user_in)

        other_space_in = SpaceCreate(
            name="Other Space",
            description="Another space"
        )  # type: ignore
        other_space = await crud_space.create(
            async_test_db, obj_in=other_space_in, user_id=other_user.id
        )

        # Create documents for test user
        for i in range(3):
            doc_in = DocumentCreate(
                filename=f"user_doc_{i}.pdf",
                content_type="application/pdf",
                size=1000,
                space_id=test_space.id
            )  # type: ignore
            await crud_document.create(
                async_test_db,
                obj_in=doc_in,
                user_id=test_user.id,
                file_path=f"spaces/{test_space.id}/documents/user_doc_{i}.pdf",
                file_hash=hashlib.sha256(f"user_{i}".encode()).hexdigest(),
                original_filename=f"User Document {i}.pdf"
            )

        # Create documents for other user
        for i in range(2):
            doc_in = DocumentCreate(
                filename=f"other_doc_{i}.pdf",
                content_type="application/pdf",
                size=1000,
                space_id=other_space.id
            )  # type: ignore
            await crud_document.create(
                async_test_db,
                obj_in=doc_in,
                user_id=other_user.id,
                file_path=f"spaces/{other_space.id}/documents/other_doc_{i}.pdf",
                file_hash=hashlib.sha256(f"other_{i}".encode()).hexdigest(),
                original_filename=f"Other Document {i}.pdf"
            )

        # Get test user's documents
        user_docs = await crud_document.get_user_documents(
            async_test_db, user_id=test_user.id
        )
        assert len(user_docs) == 3
        assert all(doc.user_id == test_user.id for doc in user_docs)

        # Get other user's documents
        other_docs = await crud_document.get_user_documents(
            async_test_db, user_id=other_user.id
        )
        assert len(other_docs) == 2
        assert all(doc.user_id == other_user.id for doc in other_docs)

    async def test_update_document(self, async_test_db: AsyncSession, test_user, test_space):
        """Test updating a document."""
        # Create a document
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
            file_path="spaces/1/documents/to_update.pdf",
            file_hash=hashlib.sha256(b"to_update").hexdigest(),
            original_filename="To Update.pdf"
        )

        # Update document
        update_data = DocumentUpdate(
            description="Updated description",
            tags=["updated", "test"]
        )  # type: ignore

        updated = await crud_document.update(
            async_test_db, db_obj=document, obj_in=update_data
        )

        assert updated.tags == ["updated", "test"]
        # Original fields should not change
        assert updated.filename == "to_update.pdf"
        assert updated.file_size == 1000

    async def test_delete_document(self, async_test_db: AsyncSession, test_user, test_space):
        """Test deleting a document."""
        # Create a document
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
            file_path="spaces/1/documents/to_delete.pdf",
            file_hash=hashlib.sha256(b"to_delete").hexdigest(),
            original_filename="To Delete.pdf"
        )
        doc_id = document.id

        # Delete document
        deleted = await crud_document.remove(async_test_db, id=doc_id)
        assert deleted is not None

        # Verify deletion
        retrieved = await crud_document.get(async_test_db, doc_id)
        assert retrieved is None

        # Verify it's not in space documents
        space_docs = await crud_document.get_by_space(
            async_test_db, space_id=test_space.id
        )
        assert len(space_docs) == 0
