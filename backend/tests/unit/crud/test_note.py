"""Unit tests for note CRUD operations.

To run these tests:
    uv run pytest tests/unit/crud/test_note.py -v
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.note import crud_note
from app.crud.space import crud_space
from app.crud.user import crud_user
from app.schemas.note import NoteCreate, NoteUpdate
from app.schemas.spaces import SpaceCreate
from app.schemas.users import UserCreate


@pytest.fixture
async def test_user(async_test_db: AsyncSession):
    """Create a test user."""
    user_in = UserCreate(
        username="noteuser",
        email="noteuser@example.com",
        password="password123",
        full_name="Note User"
    )
    user = await crud_user.create(async_test_db, obj_in=user_in)
    return user


@pytest.fixture
async def test_space(async_test_db: AsyncSession, test_user):
    """Create a test space."""
    space_in = SpaceCreate(
        name="Test Note Space",
        description="A space for testing notes"
    )  # type: ignore
    space = await crud_space.create(async_test_db, obj_in=space_in, user_id=test_user.id)
    return space


class TestCRUDNote:
    """Test suite for Note CRUD operations."""

    async def test_create_note(self, async_test_db: AsyncSession, test_user, test_space):
        """Test creating a note."""
        note_in = NoteCreate(
            title="Test Note",
            content="This is a test note content",
            content_type="markdown",
            space_id=test_space.id,
            note_type="manual",
            tags=["test", "note"]
        )  # type: ignore

        note = await crud_note.create(async_test_db, obj_in=note_in, user_id=test_user.id)

        # Assertions
        assert note.id is not None
        assert note.title == "Test Note"
        assert note.content == "This is a test note content"
        assert note.content_type == "markdown"
        assert note.space_id == test_space.id
        assert note.user_id == test_user.id
        assert note.note_type == "manual"
        assert note.tags == ["test", "note"]
        assert note.version == 1
        assert note.is_draft is False

    async def test_create_minimal_note(self, async_test_db: AsyncSession, test_user, test_space):
        """Test creating a note with minimal data."""
        note_in = NoteCreate(
            title="Minimal Note",
            content="Minimal content",
            space_id=test_space.id
        )  # type: ignore

        note = await crud_note.create(async_test_db, obj_in=note_in, user_id=test_user.id)

        assert note.id is not None
        assert note.title == "Minimal Note"
        assert note.content == "Minimal content"
        assert note.content_type == "markdown"  # Default value
        assert note.note_type == "manual"  # Default value
        assert note.tags is None
        assert note.linked_documents is None
        assert note.linked_notes is None

    async def test_get_by_space(self, async_test_db: AsyncSession, test_user, test_space):
        """Test getting notes by space."""
        # Create multiple notes
        for i in range(5):
            note_in = NoteCreate(
                title=f"Note {i}",
                content=f"Content {i}",
                space_id=test_space.id,
                tags=[f"tag{i}"]
            )  # type: ignore
            await crud_note.create(async_test_db, obj_in=note_in, user_id=test_user.id)

        # Get all notes in space
        notes = await crud_note.get_by_space(
            async_test_db, space_id=test_space.id, user_id=test_user.id
        )
        assert len(notes) == 5

        # Test pagination
        first_page = await crud_note.get_by_space(
            async_test_db, space_id=test_space.id, user_id=test_user.id, skip=0, limit=3
        )
        assert len(first_page) == 3

        second_page = await crud_note.get_by_space(
            async_test_db, space_id=test_space.id, user_id=test_user.id, skip=3, limit=3
        )
        assert len(second_page) == 2

    async def test_get_by_space_sorting(self, async_test_db: AsyncSession, test_user, test_space):
        """Test sorting notes by different fields."""
        # Create notes with different titles
        titles = ["Charlie", "Alice", "Bob"]
        for title in titles:
            note_in = NoteCreate(
                title=title,
                content=f"Content for {title}",
                space_id=test_space.id
            )  # type: ignore
            await crud_note.create(async_test_db, obj_in=note_in, user_id=test_user.id)

        # Test sorting by title ascending
        notes = await crud_note.get_by_space(
            async_test_db,
            space_id=test_space.id,
            user_id=test_user.id,
            sort_by="title",
            sort_order="asc"
        )
        assert len(notes) == 3
        assert notes[0].title == "Alice"
        assert notes[1].title == "Bob"
        assert notes[2].title == "Charlie"

    async def test_search_notes(self, async_test_db: AsyncSession, test_user, test_space):
        """Test searching notes."""
        # Create notes with searchable content
        notes_data = [
            {"title": "Python Guide", "content": "Learn Python programming"},
            {"title": "JavaScript Tutorial", "content": "Modern JavaScript development"},
            {"title": "Python Advanced", "content": "Advanced Python techniques"},
            {"title": "Data Science", "content": "Data analysis with Python"}
        ]

        for data in notes_data:
            note_in = NoteCreate(
                title=data["title"],
                content=data["content"],
                space_id=test_space.id
            )  # type: ignore
            await crud_note.create(async_test_db, obj_in=note_in, user_id=test_user.id)

        # Search for Python
        python_notes, total = await crud_note.search(
            async_test_db, query="Python", user_id=test_user.id
        )
        assert len(python_notes) == 3
        assert total == 3

        # Search by title
        guide_notes, total = await crud_note.search(
            async_test_db, query="Guide", user_id=test_user.id
        )
        assert len(guide_notes) == 1
        assert guide_notes[0].title == "Python Guide"

    async def test_search_with_filters(self, async_test_db: AsyncSession, test_user, test_space):
        """Test searching notes with filters."""
        # Create another space
        space2_in = SpaceCreate(
            name="Another Space",
            description="Another space"
        )  # type: ignore
        space2 = await crud_space.create(async_test_db, obj_in=space2_in, user_id=test_user.id)

        # Create notes in different spaces and types
        note1_in = NoteCreate(
            title="Manual Note",
            content="Manual content",
            space_id=test_space.id,
            note_type="manual",
            content_type="markdown"
        )  # type: ignore
        await crud_note.create(async_test_db, obj_in=note1_in, user_id=test_user.id)

        note2_in = NoteCreate(
            title="AI Note",
            content="AI generated content",
            space_id=space2.id,
            note_type="ai",
            content_type="html"
        )  # type: ignore
        await crud_note.create(async_test_db, obj_in=note2_in, user_id=test_user.id)

        # Search with space filter
        notes, total = await crud_note.search(
            async_test_db,
            query="content",
            user_id=test_user.id,
            space_ids=[test_space.id]
        )
        assert len(notes) == 1
        assert notes[0].title == "Manual Note"

        # Search with note type filter
        notes, total = await crud_note.search(
            async_test_db,
            query="content",
            user_id=test_user.id,
            note_types=["ai"]
        )
        assert len(notes) == 1
        assert notes[0].title == "AI Note"

        # Search with content type filter
        notes, total = await crud_note.search(
            async_test_db,
            query="content",
            user_id=test_user.id,
            content_types=["html"]
        )
        assert len(notes) == 1
        assert notes[0].title == "AI Note"

    async def test_linked_notes(self, async_test_db: AsyncSession, test_user, test_space):
        """Test linked notes functionality."""
        # Create parent note
        parent_note_in = NoteCreate(
            title="Parent Note",
            content="Parent content",
            space_id=test_space.id
        )  # type: ignore
        parent_note = await crud_note.create(async_test_db, obj_in=parent_note_in, user_id=test_user.id)

        # Create child notes
        child1_in = NoteCreate(
            title="Child Note 1",
            content="Child content 1",
            space_id=test_space.id
        )  # type: ignore
        child1 = await crud_note.create(async_test_db, obj_in=child1_in, user_id=test_user.id)

        child2_in = NoteCreate(
            title="Child Note 2",
            content="Child content 2",
            space_id=test_space.id
        )  # type: ignore
        child2 = await crud_note.create(async_test_db, obj_in=child2_in, user_id=test_user.id)

        # Update parent note with linked notes
        updated_parent = await crud_note.update_links(
            async_test_db,
            note_id=parent_note.id,
            linked_notes=[child1.id, child2.id]
        )
        assert updated_parent is not None
        assert updated_parent.linked_notes == [child1.id, child2.id]

        # Get linked notes
        linked_notes = await crud_note.get_linked_notes(
            async_test_db, note_id=parent_note.id, user_id=test_user.id
        )
        assert len(linked_notes) == 2
        linked_titles = {note.title for note in linked_notes}
        assert linked_titles == {"Child Note 1", "Child Note 2"}

    async def test_get_recent_notes(self, async_test_db: AsyncSession, test_user, test_space):
        """Test getting recent notes."""
        # Create notes of different types
        note_types = ["manual", "ai", "linked"]
        for i, note_type in enumerate(note_types):
            note_in = NoteCreate(
                title=f"Note {i}",
                content=f"Content {i}",
                space_id=test_space.id,
                note_type=note_type
            )  # type: ignore
            await crud_note.create(async_test_db, obj_in=note_in, user_id=test_user.id)

        # Get all recent notes
        recent_notes = await crud_note.get_recent_notes(
            async_test_db, user_id=test_user.id, limit=5
        )
        assert len(recent_notes) == 3

        # Get recent notes by type
        ai_notes = await crud_note.get_recent_notes(
            async_test_db, user_id=test_user.id, note_type="ai", limit=5
        )
        assert len(ai_notes) == 1
        assert ai_notes[0].note_type == "ai"

    async def test_tag_operations(self, async_test_db: AsyncSession, test_user, test_space):
        """Test tag operations."""
        # Create note
        note_in = NoteCreate(
            title="Tagged Note",
            content="Tagged content",
            space_id=test_space.id,
            tags=["initial"]
        )  # type: ignore
        note = await crud_note.create(async_test_db, obj_in=note_in, user_id=test_user.id)

        # Add tag
        updated_note = await crud_note.add_tag(
            async_test_db, note_id=note.id, tag="new-tag"
        )
        assert updated_note is not None
        assert updated_note.tags is not None
        assert "new-tag" in updated_note.tags
        assert "initial" in updated_note.tags

        # Add duplicate tag (should not duplicate)
        updated_note = await crud_note.add_tag(
            async_test_db, note_id=note.id, tag="new-tag"
        )
        assert updated_note is not None
        assert updated_note.tags is not None
        assert updated_note.tags.count("new-tag") == 1

        # Remove tag
        updated_note = await crud_note.remove_tag(
            async_test_db, note_id=note.id, tag="initial"
        )
        assert updated_note is not None
        assert updated_note.tags is not None
        assert "initial" not in updated_note.tags
        assert "new-tag" in updated_note.tags

    async def test_update_note(self, async_test_db: AsyncSession, test_user, test_space):
        """Test updating a note."""
        # Create note
        note_in = NoteCreate(
            title="Original Title",
            content="Original content",
            space_id=test_space.id,
            tags=["original"]
        )  # type: ignore
        note = await crud_note.create(async_test_db, obj_in=note_in, user_id=test_user.id)

        # Update note
        update_data = NoteUpdate(
            title="Updated Title",
            content="Updated content",
            tags=["updated", "modified"]
        )  # type: ignore

        updated_note = await crud_note.update(
            async_test_db, db_obj=note, obj_in=update_data
        )

        assert updated_note.title == "Updated Title"
        assert updated_note.content == "Updated content"
        assert updated_note.tags == ["updated", "modified"]
        # Space and user should remain unchanged
        assert updated_note.space_id == test_space.id
        assert updated_note.user_id == test_user.id

    async def test_delete_note(self, async_test_db: AsyncSession, test_user, test_space):
        """Test deleting a note."""
        # Create note
        note_in = NoteCreate(
            title="To Delete",
            content="To be deleted",
            space_id=test_space.id
        )  # type: ignore
        note = await crud_note.create(async_test_db, obj_in=note_in, user_id=test_user.id)
        note_id = note.id

        # Delete note
        deleted_note = await crud_note.remove(async_test_db, id=note_id)
        assert deleted_note is not None

        # Verify deletion
        retrieved_note = await crud_note.get(async_test_db, note_id)
        assert retrieved_note is None

    async def test_get_by_document(self, async_test_db: AsyncSession, test_user, test_space):
        """Test getting notes by document."""
        # Create notes with document links
        note1_in = NoteCreate(
            title="Note 1",
            content="Content 1",
            space_id=test_space.id,
            linked_documents=[1, 2]
        )  # type: ignore
        await crud_note.create(async_test_db, obj_in=note1_in, user_id=test_user.id)

        note2_in = NoteCreate(
            title="Note 2",
            content="Content 2",
            space_id=test_space.id,
            linked_documents=[2, 3]
        )  # type: ignore
        await crud_note.create(async_test_db, obj_in=note2_in, user_id=test_user.id)

        note3_in = NoteCreate(
            title="Note 3",
            content="Content 3",
            space_id=test_space.id,
            linked_documents=[4]
        )  # type: ignore
        await crud_note.create(async_test_db, obj_in=note3_in, user_id=test_user.id)

        # Get notes linked to document 2
        notes = await crud_note.get_by_document(
            async_test_db, document_id=2, user_id=test_user.id
        )
        assert len(notes) == 2
        note_titles = {note.title for note in notes}
        assert note_titles == {"Note 1", "Note 2"}

    async def test_user_isolation(self, async_test_db: AsyncSession, test_space):
        """Test that users can only access their own notes."""
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

        # Create notes for each user
        note1_in = NoteCreate(
            title="User 1 Note",
            content="User 1 content",
            space_id=test_space.id
        )  # type: ignore
        await crud_note.create(async_test_db, obj_in=note1_in, user_id=user1.id)

        note2_in = NoteCreate(
            title="User 2 Note",
            content="User 2 content",
            space_id=test_space.id
        )  # type: ignore
        await crud_note.create(async_test_db, obj_in=note2_in, user_id=user2.id)

        # Each user should only see their own notes
        user1_notes = await crud_note.get_by_space(
            async_test_db, space_id=test_space.id, user_id=user1.id
        )
        assert len(user1_notes) == 1
        assert user1_notes[0].title == "User 1 Note"

        user2_notes = await crud_note.get_by_space(
            async_test_db, space_id=test_space.id, user_id=user2.id
        )
        assert len(user2_notes) == 1
        assert user2_notes[0].title == "User 2 Note"

    async def test_search_with_tag_filter(self, async_test_db: AsyncSession, test_user, test_space):
        """Test searching notes with tag filter."""
        # Create notes with different tags
        note1_in = NoteCreate(
            title="Note 1",
            content="Content 1",
            space_id=test_space.id,
            tags=["python", "programming"]
        )  # type: ignore
        await crud_note.create(async_test_db, obj_in=note1_in, user_id=test_user.id)

        note2_in = NoteCreate(
            title="Note 2",
            content="Content 2",
            space_id=test_space.id,
            tags=["javascript", "programming"]
        )  # type: ignore
        await crud_note.create(async_test_db, obj_in=note2_in, user_id=test_user.id)

        note3_in = NoteCreate(
            title="Note 3",
            content="Content 3",
            space_id=test_space.id,
            tags=["design"]
        )  # type: ignore
        await crud_note.create(async_test_db, obj_in=note3_in, user_id=test_user.id)

        # Search with tag filter
        notes, total = await crud_note.search(
            async_test_db,
            query="Content",
            user_id=test_user.id,
            tags=["python"]
        )
        assert len(notes) == 1
        assert notes[0].title == "Note 1"

        # Search with multiple tag filter
        notes, total = await crud_note.search(
            async_test_db,
            query="Content",
            user_id=test_user.id,
            tags=["programming"]
        )
        assert len(notes) == 2

    async def test_get_linked_notes_edge_cases(self, async_test_db: AsyncSession, test_user, test_space):
        """Test edge cases for linked notes."""
        # Create a note
        note_in = NoteCreate(
            title="Parent Note",
            content="Parent content",
            space_id=test_space.id
        )  # type: ignore
        note = await crud_note.create(async_test_db, obj_in=note_in, user_id=test_user.id)

        # Test with non-existent note
        linked_notes = await crud_note.get_linked_notes(
            async_test_db, note_id=999999, user_id=test_user.id
        )
        assert linked_notes == []

        # Test with different user
        other_user_in = UserCreate(
            username="otheruser",
            email="other@example.com",
            password="password123",
            full_name="Other User"
        )
        other_user = await crud_user.create(async_test_db, obj_in=other_user_in)

        linked_notes = await crud_note.get_linked_notes(
            async_test_db, note_id=note.id, user_id=other_user.id
        )
        assert linked_notes == []

        # Test with note that has no linked notes
        linked_notes = await crud_note.get_linked_notes(
            async_test_db, note_id=note.id, user_id=test_user.id
        )
        assert linked_notes == []

    async def test_update_links_functionality(self, async_test_db: AsyncSession, test_user, test_space):
        """Test update_links functionality."""
        # Create notes
        note1_in = NoteCreate(
            title="Note 1",
            content="Content 1",
            space_id=test_space.id
        )  # type: ignore
        note1 = await crud_note.create(async_test_db, obj_in=note1_in, user_id=test_user.id)

        note2_in = NoteCreate(
            title="Note 2",
            content="Content 2",
            space_id=test_space.id
        )  # type: ignore
        note2 = await crud_note.create(async_test_db, obj_in=note2_in, user_id=test_user.id)

        # Test updating linked documents
        updated_note = await crud_note.update_links(
            async_test_db,
            note_id=note1.id,
            linked_documents=[1, 2, 3]
        )
        assert updated_note is not None
        assert updated_note.linked_documents == [1, 2, 3]

        # Test updating linked notes
        updated_note = await crud_note.update_links(
            async_test_db,
            note_id=note1.id,
            linked_notes=[note2.id]
        )
        assert updated_note is not None
        assert updated_note.linked_notes == [note2.id]

        # Test with non-existent note
        result = await crud_note.update_links(
            async_test_db,
            note_id=999999,
            linked_documents=[1]
        )
        assert result is None

    async def test_tag_operations_edge_cases(self, async_test_db: AsyncSession, test_user, test_space):
        """Test edge cases for tag operations."""
        # Create note without tags
        note_in = NoteCreate(
            title="No Tags Note",
            content="No tags content",
            space_id=test_space.id
        )  # type: ignore
        note = await crud_note.create(async_test_db, obj_in=note_in, user_id=test_user.id)

        # Test adding tag to note with no tags
        updated_note = await crud_note.add_tag(
            async_test_db, note_id=note.id, tag="first-tag"
        )
        assert updated_note is not None
        assert updated_note.tags == ["first-tag"]

        # Test adding tag to non-existent note
        result = await crud_note.add_tag(
            async_test_db, note_id=999999, tag="tag"
        )
        assert result is None

        # Test removing tag from non-existent note
        result = await crud_note.remove_tag(
            async_test_db, note_id=999999, tag="tag"
        )
        assert result is None

        # Test removing non-existent tag
        result = await crud_note.remove_tag(
            async_test_db, note_id=note.id, tag="non-existent"
        )
        assert result is not None  # Should still return the note

    async def test_get_tags_functionality(self, async_test_db: AsyncSession, test_user, test_space):
        """Test get_tags functionality."""
        # Create another space
        space2_in = SpaceCreate(
            name="Another Space",
            description="Another space for tags"
        )  # type: ignore
        space2 = await crud_space.create(async_test_db, obj_in=space2_in, user_id=test_user.id)

        # Create notes with tags in different spaces
        note1_in = NoteCreate(
            title="Note 1",
            content="Content 1",
            space_id=test_space.id,
            tags=["python", "programming", "python"]  # duplicate tag
        )  # type: ignore
        await crud_note.create(async_test_db, obj_in=note1_in, user_id=test_user.id)

        note2_in = NoteCreate(
            title="Note 2",
            content="Content 2",
            space_id=test_space.id,
            tags=["javascript", "programming"]
        )  # type: ignore
        await crud_note.create(async_test_db, obj_in=note2_in, user_id=test_user.id)

        note3_in = NoteCreate(
            title="Note 3",
            content="Content 3",
            space_id=space2.id,
            tags=["design", "ui"]
        )  # type: ignore
        await crud_note.create(async_test_db, obj_in=note3_in, user_id=test_user.id)

        # Get all tags for user
        all_tags = await crud_note.get_tags(async_test_db, user_id=test_user.id)
        assert len(all_tags) == 5  # python, programming, javascript, design, ui

        # Check that programming appears twice (most frequent)
        programming_tag = next(tag for tag in all_tags if tag["tag"] == "programming")
        assert programming_tag["count"] == 2

        # Get tags for specific space
        space_tags = await crud_note.get_tags(
            async_test_db, user_id=test_user.id, space_id=test_space.id
        )
        assert len(space_tags) == 3  # python, programming, javascript
        tag_names = [tag["tag"] for tag in space_tags]
        assert "design" not in tag_names
        assert "ui" not in tag_names
