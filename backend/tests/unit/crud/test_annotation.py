"""Unit tests for annotation CRUD operations.

To run these tests:
    uv run pytest tests/unit/crud/test_annotation.py -v
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.annotation import crud_annotation
from app.crud.document import crud_document
from app.crud.space import crud_space
from app.crud.user import crud_user
from app.schemas.annotation import AnnotationCreate, AnnotationUpdate
from app.schemas.documents import DocumentCreate
from app.schemas.spaces import SpaceCreate
from app.schemas.users import UserCreate


def create_annotation(**kwargs) -> AnnotationCreate:
    """Helper function to create AnnotationCreate with sensible defaults."""
    defaults = {
        "document_id": 1,  # Will be overridden in tests
        "type": "highlight",
        "content": "Default annotation content",
    }
    defaults.update(kwargs)
    return AnnotationCreate(**defaults)


@pytest.fixture
async def test_user(async_test_db: AsyncSession):
    """Create a test user."""
    user_in = UserCreate(
        username="annotationuser",
        email="annotationuser@example.com",
        password="password123",
        full_name="Annotation User"
    )
    user = await crud_user.create(async_test_db, obj_in=user_in)
    return user


@pytest.fixture
async def test_space(async_test_db: AsyncSession, test_user):
    """Create a test space."""
    space_in = SpaceCreate(
        name="Test Annotation Space",
        description="A space for testing annotations"
    )  # type: ignore
    space = await crud_space.create(async_test_db, obj_in=space_in, user_id=test_user.id)
    return space


@pytest.fixture
async def test_document(async_test_db: AsyncSession, test_user, test_space):
    """Create a test document."""
    doc_in = DocumentCreate(
        filename="test_document.pdf",
        content_type="application/pdf",
        size=1024000,
        space_id=test_space.id
    )  # type: ignore
    document = await crud_document.create(
        async_test_db,
        obj_in=doc_in,
        user_id=test_user.id,
        file_path="test/path.pdf",
        file_hash="test_hash"
    )
    return document


class TestCRUDAnnotation:
    """Test suite for Annotation CRUD operations."""

    async def test_create_annotation(self, async_test_db: AsyncSession, test_user, test_document):
        """Test creating an annotation."""
        annotation_in = AnnotationCreate(
            document_id=test_document.id,
            type="highlight",
            content="This is a highlight annotation",
            selected_text="Selected text for highlighting",
            page_number=1,
            position_data={"x": 100, "y": 200, "width": 150, "height": 20},
            color="#FFFF00"
        )

        annotation = await crud_annotation.create(
            async_test_db, obj_in=annotation_in, user_id=test_user.id
        )

        # Assertions
        assert annotation.id is not None
        assert annotation.document_id == test_document.id
        assert annotation.user_id == test_user.id
        assert annotation.type == "highlight"
        assert annotation.content == "This is a highlight annotation"
        assert annotation.selected_text == "Selected text for highlighting"
        assert annotation.page_number == 1
        assert annotation.position_data == {"x": 100, "y": 200, "width": 150, "height": 20}
        assert annotation.color == "#FFFF00"
        assert annotation.is_private is False  # Default value

    async def test_create_different_annotation_types(self, async_test_db: AsyncSession, test_user, test_document):
        """Test creating different types of annotations."""
        annotation_types = [
            ("highlight", "Highlighted text", "#FFFF00"),
            ("underline", "Underlined text", "#FF0000"),
            ("note", "This is a note annotation", None),
            ("bookmark", "Bookmarked section", None)
        ]

        for ann_type, content, color in annotation_types:
            annotation_in = AnnotationCreate(
                document_id=test_document.id,
                type=ann_type,
                content=content,
                selected_text=None,
                page_number=1,
                position_data=None,
                color=color
            )

            annotation = await crud_annotation.create(
                async_test_db, obj_in=annotation_in, user_id=test_user.id
            )

            assert annotation.type == ann_type
            assert annotation.content == content
            assert annotation.color == color

    async def test_get_by_document(self, async_test_db: AsyncSession, test_user, test_document):
        """Test getting annotations by document."""
        # Create multiple annotations
        for i in range(5):
            annotation_in = AnnotationCreate(
                document_id=test_document.id,
                type="highlight" if i % 2 == 0 else "note",
                content=f"Annotation {i}",
                selected_text=None,
                page_number=i + 1,
                position_data=None,
                color=None
            )
            await crud_annotation.create(
                async_test_db, obj_in=annotation_in, user_id=test_user.id
            )

        # Get all annotations for document
        annotations = await crud_annotation.get_by_document(
            async_test_db, document_id=test_document.id, user_id=test_user.id
        )
        assert len(annotations) == 5

        # Test pagination
        first_page = await crud_annotation.get_by_document(
            async_test_db, document_id=test_document.id, user_id=test_user.id, skip=0, limit=3
        )
        assert len(first_page) == 3

        second_page = await crud_annotation.get_by_document(
            async_test_db, document_id=test_document.id, user_id=test_user.id, skip=3, limit=3
        )
        assert len(second_page) == 2

    async def test_get_by_document_with_filters(self, async_test_db: AsyncSession, test_user, test_document):
        """Test getting annotations with filters."""
        # Create annotations on different pages and types
        annotations_data = [
            ("highlight", 1, "Highlight on page 1"),
            ("note", 1, "Note on page 1"),
            ("highlight", 2, "Highlight on page 2"),
            ("underline", 2, "Underline on page 2"),
        ]

        for ann_type, page, content in annotations_data:
            annotation_in = AnnotationCreate(
                document_id=test_document.id,
                type=ann_type,
                content=content,
                selected_text=None,
                page_number=page,
                position_data=None,
                color=None
            )
            await crud_annotation.create(
                async_test_db, obj_in=annotation_in, user_id=test_user.id
            )

        # Filter by page number
        page1_annotations = await crud_annotation.get_by_document(
            async_test_db, document_id=test_document.id, user_id=test_user.id, page_number=1
        )
        assert len(page1_annotations) == 2

        # Filter by annotation type
        highlights = await crud_annotation.get_by_document(
            async_test_db, document_id=test_document.id, user_id=test_user.id, annotation_type="highlight"
        )
        assert len(highlights) == 2
        assert all(ann.type == "highlight" for ann in highlights)

        # Combine filters
        page2_underlines = await crud_annotation.get_by_document(
            async_test_db, document_id=test_document.id, user_id=test_user.id,
            page_number=2, annotation_type="underline"
        )
        assert len(page2_underlines) == 1
        assert page2_underlines[0].type == "underline"
        assert page2_underlines[0].page_number == 2

    async def test_get_by_document_pages(self, async_test_db: AsyncSession, test_user, test_document):
        """Test getting annotations by page range."""
        # Create annotations on pages 1-5
        for page in range(1, 6):
            for i in range(2):  # 2 annotations per page
                annotation_in = AnnotationCreate(
                    document_id=test_document.id,
                    type="highlight",
                    content=f"Annotation {i} on page {page}",
                    page_number=page,
                    selected_text=None,
                    position_data=None,
                    color=None
                )
                await crud_annotation.create(
                    async_test_db, obj_in=annotation_in, user_id=test_user.id
                )

        # Get annotations for pages 2-4
        annotations = await crud_annotation.get_by_document_pages(
            async_test_db,
            document_id=test_document.id,
            user_id=test_user.id,
            start_page=2,
            end_page=4
        )
        assert len(annotations) == 6  # 3 pages * 2 annotations each
        page_numbers = {ann.page_number for ann in annotations}
        assert page_numbers == {2, 3, 4}

    async def test_get_user_annotations(self, async_test_db: AsyncSession, test_user, test_document):
        """Test getting all user annotations."""
        # Create annotations of different types
        annotation_types = ["highlight", "note", "highlight", "underline", "bookmark"]
        for ann_type in annotation_types:
            annotation_in = AnnotationCreate(
                document_id=test_document.id,
                type=ann_type,
                content=f"Content for {ann_type}",
                page_number=1,
                selected_text=None,
                position_data=None,
                color=None
            )
            await crud_annotation.create(
                async_test_db, obj_in=annotation_in, user_id=test_user.id
            )

        # Get all user annotations
        annotations, total = await crud_annotation.get_user_annotations(
            async_test_db, user_id=test_user.id
        )
        assert len(annotations) == 5
        assert total == 5

        # Filter by type
        highlights, total_highlights = await crud_annotation.get_user_annotations(
            async_test_db, user_id=test_user.id, annotation_type="highlight"
        )
        assert len(highlights) == 2
        assert total_highlights == 2
        assert all(ann.type == "highlight" for ann in highlights)

        # Test pagination
        first_page, total = await crud_annotation.get_user_annotations(
            async_test_db, user_id=test_user.id, skip=0, limit=3
        )
        assert len(first_page) == 3
        assert total == 5

    async def test_batch_create(self, async_test_db: AsyncSession, test_user, test_document):
        """Test batch creating annotations."""
        annotations_data = [
            AnnotationCreate(
                document_id=test_document.id,
                type="highlight",
                content="Batch annotation 1",
                page_number=1,
                selected_text=None,
                position_data=None,
                color=None
            ),
            AnnotationCreate(
                document_id=test_document.id,
                type="note",
                content="Batch annotation 2",
                page_number=2,
                selected_text=None,
                position_data=None,
                color=None
            ),
            AnnotationCreate(
                document_id=test_document.id,
                type="underline",
                content="Batch annotation 3",
                page_number=3,
                selected_text=None,
                position_data=None,
                color=None
            ),
        ]

        annotations = await crud_annotation.batch_create(
            async_test_db,
            document_id=test_document.id,
            user_id=test_user.id,
            annotations_data=annotations_data
        )

        assert len(annotations) == 3
        assert annotations[0].content == "Batch annotation 1"
        assert annotations[1].content == "Batch annotation 2"
        assert annotations[2].content == "Batch annotation 3"

        # Verify all have correct document_id and user_id
        for annotation in annotations:
            assert annotation.document_id == test_document.id
            assert annotation.user_id == test_user.id

    async def test_search_annotations(self, async_test_db: AsyncSession, test_user, test_document):
        """Test searching annotations."""
        # Create searchable annotations
        search_data = [
            ("Python programming is awesome", "Python is great"),
            ("JavaScript development tips", "JavaScript rocks"),
            ("Database design patterns", "SQL databases"),
            ("Machine learning algorithms", "AI and ML"),
        ]

        for content, selected_text in search_data:
            annotation_in = AnnotationCreate(
                document_id=test_document.id,
                type="note",
                content=content,
                selected_text=selected_text,
                page_number=1,
                position_data=None,
                color=None
            )
            await crud_annotation.create(
                async_test_db, obj_in=annotation_in, user_id=test_user.id
            )

        # Search by content
        python_annotations, total = await crud_annotation.search_annotations(
            async_test_db, query="Python", user_id=test_user.id
        )
        assert len(python_annotations) == 1
        assert total == 1
        assert python_annotations[0].content is not None and "Python" in python_annotations[0].content

        # Search by selected text
        js_annotations, total = await crud_annotation.search_annotations(
            async_test_db, query="JavaScript", user_id=test_user.id
        )
        assert len(js_annotations) == 1
        assert js_annotations[0].selected_text is not None and "JavaScript" in js_annotations[0].selected_text

        # Search with document filter
        all_annotations, total = await crud_annotation.search_annotations(
            async_test_db,
            query="",  # Empty query to get all
            user_id=test_user.id,
            document_ids=[test_document.id]
        )
        assert len(all_annotations) == 4

    async def test_get_statistics(self, async_test_db: AsyncSession, test_user, test_document):
        """Test getting annotation statistics."""
        # Create diverse annotations
        annotations_data = [
            ("highlight", "#FFFF00"),
            ("highlight", "#FF0000"),
            ("note", None),
            ("underline", "#00FF00"),
            ("bookmark", None),
            ("highlight", "#FFFF00"),  # Duplicate color
        ]

        for ann_type, color in annotations_data:
            annotation_in = AnnotationCreate(
                document_id=test_document.id,
                type=ann_type,
                content=f"Content for {ann_type}",
                page_number=1,
                selected_text=None,
                position_data=None,
                color=color
            )
            await crud_annotation.create(
                async_test_db, obj_in=annotation_in, user_id=test_user.id
            )

        # Get statistics
        stats = await crud_annotation.get_statistics(
            async_test_db, user_id=test_user.id
        )

        assert stats["total_annotations"] == 6
        assert stats["by_type"]["highlight"] == 3
        assert stats["by_type"]["note"] == 1
        assert stats["by_type"]["underline"] == 1
        assert stats["by_type"]["bookmark"] == 1

        # Color statistics (only for highlight and underline)
        assert stats["by_color"]["#FFFF00"] == 2
        assert stats["by_color"]["#FF0000"] == 1
        assert stats["by_color"]["#00FF00"] == 1

        # Recent activity
        assert len(stats["recent_activity"]) == 6
        assert all("id" in activity for activity in stats["recent_activity"])

        # Test document-specific statistics
        doc_stats = await crud_annotation.get_statistics(
            async_test_db, user_id=test_user.id, document_id=test_document.id
        )
        assert doc_stats["total_annotations"] == 6

    async def test_copy_annotations(self, async_test_db: AsyncSession, test_user, test_space):
        """Test copying annotations between documents."""
        # Create source document
        source_doc_in = DocumentCreate(
            filename="source.pdf",
            content_type="application/pdf",
            size=1024,
            space_id=test_space.id
        )  # type: ignore
        source_doc = await crud_document.create(
            async_test_db,
            obj_in=source_doc_in,
            user_id=test_user.id,
            file_path="source/path.pdf",
            file_hash="source_hash"
        )

        # Create target document
        target_doc_in = DocumentCreate(
            filename="target.pdf",
            content_type="application/pdf",
            size=1024,
            space_id=test_space.id
        )  # type: ignore
        target_doc = await crud_document.create(
            async_test_db,
            obj_in=target_doc_in,
            user_id=test_user.id,
            file_path="target/path.pdf",
            file_hash="target_hash"
        )

        # Create annotations in source document
        source_annotations_data = [
            ("highlight", "Source highlight", "#FFFF00"),
            ("note", "Source note", None),
            ("underline", "Source underline", "#FF0000"),
        ]

        for ann_type, content, color in source_annotations_data:
            annotation_in = AnnotationCreate(
                document_id=source_doc.id,
                type=ann_type,
                content=content,
                page_number=1,
                selected_text=None,
                position_data=None,
                color=color
            )
            await crud_annotation.create(
                async_test_db, obj_in=annotation_in, user_id=test_user.id
            )

        # Copy annotations
        copied_annotations = await crud_annotation.copy_annotations(
            async_test_db,
            source_document_id=source_doc.id,
            target_document_id=target_doc.id,
            user_id=test_user.id
        )

        assert len(copied_annotations) == 3

        # Verify copied annotations
        for annotation in copied_annotations:
            assert annotation.document_id == target_doc.id
            assert annotation.user_id == test_user.id

        # Verify content is preserved
        contents = [ann.content for ann in copied_annotations]
        assert "Source highlight" in contents
        assert "Source note" in contents
        assert "Source underline" in contents

    async def test_update_annotation(self, async_test_db: AsyncSession, test_user, test_document):
        """Test updating an annotation."""
        # Create annotation
        annotation_in = AnnotationCreate(
            document_id=test_document.id,
            type="highlight",
            content="Original content",
            color="#FFFF00",
            page_number=1,
            selected_text=None,
            position_data=None
        )
        annotation = await crud_annotation.create(
            async_test_db, obj_in=annotation_in, user_id=test_user.id
        )

        # Update annotation
        update_data = AnnotationUpdate(
            content="Updated content",
            color="#FF0000",
            position_data={"x": 50, "y": 100}
        )
        updated_annotation = await crud_annotation.update(
            async_test_db, db_obj=annotation, obj_in=update_data
        )

        assert updated_annotation.content == "Updated content"
        assert updated_annotation.color == "#FF0000"
        assert updated_annotation.position_data == {"x": 50, "y": 100}
        # Original fields should remain unchanged
        assert updated_annotation.type == "highlight"
        assert updated_annotation.page_number == 1

    async def test_delete_annotation(self, async_test_db: AsyncSession, test_user, test_document):
        """Test deleting an annotation."""
        # Create annotation
        annotation_in = AnnotationCreate(
            document_id=test_document.id,
            type="note",
            content="To be deleted",
            page_number=1,
            selected_text=None,
            position_data=None,
            color=None
        )
        annotation = await crud_annotation.create(
            async_test_db, obj_in=annotation_in, user_id=test_user.id
        )
        annotation_id = annotation.id

        # Delete annotation
        deleted_annotation = await crud_annotation.remove(async_test_db, id=annotation_id)
        assert deleted_annotation is not None

        # Verify deletion
        retrieved_annotation = await crud_annotation.get(async_test_db, annotation_id)
        assert retrieved_annotation is None

    async def test_user_isolation(self, async_test_db: AsyncSession, test_document, test_space):
        """Test that users can only access their own annotations."""
        # Create two users
        user1_in = UserCreate(
            username="user1",
            email="user1@example.com",
            password="password123",
            full_name="User One"
        )
        user1 = await crud_user.create(async_test_db, obj_in=user1_in)

        user2_in = UserCreate(
            username="user2",
            email="user2@example.com",
            password="password123",
            full_name="User Two"
        )
        user2 = await crud_user.create(async_test_db, obj_in=user2_in)

        # Create annotations for each user
        annotation1_in = AnnotationCreate(
            document_id=test_document.id,
            type="highlight",
            content="User 1 annotation",
            page_number=1,
            selected_text=None,
            position_data=None,
            color=None
        )
        await crud_annotation.create(async_test_db, obj_in=annotation1_in, user_id=user1.id)

        annotation2_in = AnnotationCreate(
            document_id=test_document.id,
            type="note",
            content="User 2 annotation",
            page_number=2,
            selected_text=None,
            position_data=None,
            color=None
        )
        await crud_annotation.create(async_test_db, obj_in=annotation2_in, user_id=user2.id)

        # Each user should only see their own annotations
        user1_annotations = await crud_annotation.get_by_document(
            async_test_db, document_id=test_document.id, user_id=user1.id
        )
        assert len(user1_annotations) == 1
        assert user1_annotations[0].content == "User 1 annotation"

        user2_annotations = await crud_annotation.get_by_document(
            async_test_db, document_id=test_document.id, user_id=user2.id
        )
        assert len(user2_annotations) == 1
        assert user2_annotations[0].content == "User 2 annotation"

    async def test_private_annotations(self, async_test_db: AsyncSession, test_user, test_document):
        """Test private annotation functionality."""
        # Create private annotation
        private_annotation_in = AnnotationCreate(
            document_id=test_document.id,
            type="note",
            content="Private annotation",
            page_number=1,
            selected_text=None,
            position_data=None,
            color=None
        )

        # The model sets is_private=False by default, let's test this
        annotation = await crud_annotation.create(
            async_test_db, obj_in=private_annotation_in, user_id=test_user.id
        )

        assert annotation.is_private is False  # Default value

    async def test_annotation_with_tags(self, async_test_db: AsyncSession, test_user, test_document):
        """Test annotations with tags."""
        # Create annotation with tags (using direct model creation since schema doesn't support tags)
        from app.models.models import Annotation

        annotation = Annotation(
            document_id=test_document.id,
            user_id=test_user.id,
            type="highlight",
            content="Tagged annotation",
            page_number=1,
            tags=["important", "review", "todo"]
        )
        async_test_db.add(annotation)
        await async_test_db.commit()
        await async_test_db.refresh(annotation)

        assert annotation.tags == ["important", "review", "todo"]

        # Verify it can be retrieved
        retrieved = await crud_annotation.get(async_test_db, annotation.id)
        assert retrieved is not None
        assert retrieved.tags == ["important", "review", "todo"]
