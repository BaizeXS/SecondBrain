"""Unit tests for note version CRUD operations.

To run these tests:
    uv run pytest tests/unit/crud/test_note_version.py -v
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.note import crud_note
from app.crud.note_version import crud_note_version
from app.crud.space import crud_space
from app.crud.user import crud_user
from app.schemas.note import NoteCreate
from app.schemas.note_version import NoteVersionCreate
from app.schemas.spaces import SpaceCreate
from app.schemas.users import UserCreate


@pytest.fixture
async def test_user(async_test_db: AsyncSession):
    """Create a test user."""
    user_in = UserCreate(
        username="versionuser",
        email="versionuser@example.com",
        password="password123",
        full_name="Version User"
    )
    user = await crud_user.create(async_test_db, obj_in=user_in)
    return user


@pytest.fixture
async def test_space(async_test_db: AsyncSession, test_user):
    """Create a test space."""
    space_in = SpaceCreate(
        name="Test Version Space",
        description="A space for testing note versions"
    )  # type: ignore
    space = await crud_space.create(async_test_db, obj_in=space_in, user_id=test_user.id)
    return space


@pytest.fixture
async def test_note(async_test_db: AsyncSession, test_user, test_space):
    """Create a test note."""
    note_in = NoteCreate(
        title="Test Note",
        content="Original content",
        space_id=test_space.id
    )  # type: ignore
    note = await crud_note.create(async_test_db, obj_in=note_in, user_id=test_user.id)
    return note


class TestCRUDNoteVersion:
    """Test suite for NoteVersion CRUD operations."""

    async def test_create_version(self, async_test_db: AsyncSession, test_user, test_note):
        """Test creating a note version."""
        version = await crud_note_version.create_version(
            async_test_db,
            note_id=test_note.id,
            user_id=test_user.id,
            title="Version 1 Title",
            content="Version 1 content",
            content_html="<p>Version 1 content</p>",
            change_summary="Initial version",
            change_type="edit",
            word_count=3,
            tags=["version", "test"],
            metadata={"author": "test_user"}
        )

        # Assertions
        assert version.id is not None
        assert version.note_id == test_note.id
        assert version.user_id == test_user.id
        assert version.version_number == 1
        assert version.title == "Version 1 Title"
        assert version.content == "Version 1 content"
        assert version.content_html == "<p>Version 1 content</p>"
        assert version.change_summary == "Initial version"
        assert version.change_type == "edit"
        assert version.word_count == 3
        assert version.tags == ["version", "test"]
        assert version.meta_data == {"author": "test_user"}

    async def test_create_multiple_versions(self, async_test_db: AsyncSession, test_user, test_note):
        """Test creating multiple versions."""
        # Create first version
        version1 = await crud_note_version.create_version(
            async_test_db,
            note_id=test_note.id,
            user_id=test_user.id,
            title="Version 1",
            content="Content 1",
            change_type="edit"
        )
        assert version1.version_number == 1

        # Create second version
        version2 = await crud_note_version.create_version(
            async_test_db,
            note_id=test_note.id,
            user_id=test_user.id,
            title="Version 2",
            content="Content 2",
            change_type="edit"
        )
        assert version2.version_number == 2

        # Create third version
        version3 = await crud_note_version.create_version(
            async_test_db,
            note_id=test_note.id,
            user_id=test_user.id,
            title="Version 3",
            content="Content 3",
            change_type="ai_generate",
            ai_model="gpt-4",
            ai_prompt="Generate summary"
        )
        assert version3.version_number == 3
        assert version3.ai_model == "gpt-4"
        assert version3.ai_prompt == "Generate summary"

    async def test_get_by_note(self, async_test_db: AsyncSession, test_user, test_note):
        """Test getting versions by note."""
        # Create multiple versions
        for i in range(5):
            await crud_note_version.create_version(
                async_test_db,
                note_id=test_note.id,
                user_id=test_user.id,
                title=f"Version {i+1}",
                content=f"Content {i+1}",
                change_type="edit"
            )

        # Get all versions
        versions = await crud_note_version.get_by_note(
            async_test_db, note_id=test_note.id
        )
        assert len(versions) == 5
        # Should be ordered by version_number desc
        assert versions[0].version_number == 5
        assert versions[4].version_number == 1

        # Test pagination
        first_page = await crud_note_version.get_by_note(
            async_test_db, note_id=test_note.id, skip=0, limit=3
        )
        assert len(first_page) == 3
        assert first_page[0].version_number == 5

        second_page = await crud_note_version.get_by_note(
            async_test_db, note_id=test_note.id, skip=3, limit=3
        )
        assert len(second_page) == 2
        assert second_page[0].version_number == 2

    async def test_get_latest_version(self, async_test_db: AsyncSession, test_user, test_note):
        """Test getting the latest version."""
        # Initially no versions
        latest = await crud_note_version.get_latest_version(
            async_test_db, note_id=test_note.id
        )
        assert latest is None

        # Create versions
        for i in range(3):
            await crud_note_version.create_version(
                async_test_db,
                note_id=test_note.id,
                user_id=test_user.id,
                title=f"Version {i+1}",
                content=f"Content {i+1}",
                change_type="edit"
            )

        # Get latest version
        latest = await crud_note_version.get_latest_version(
            async_test_db, note_id=test_note.id
        )
        assert latest is not None
        assert latest.version_number == 3
        assert latest.title == "Version 3"

    async def test_get_by_version_number(self, async_test_db: AsyncSession, test_user, test_note):
        """Test getting version by version number."""
        # Create versions
        for i in range(3):
            await crud_note_version.create_version(
                async_test_db,
                note_id=test_note.id,
                user_id=test_user.id,
                title=f"Version {i+1}",
                content=f"Content {i+1}",
                change_type="edit"
            )

        # Get specific version
        version2 = await crud_note_version.get_by_version_number(
            async_test_db, note_id=test_note.id, version_number=2
        )
        assert version2 is not None
        assert version2.version_number == 2
        assert version2.title == "Version 2"

        # Test non-existent version
        non_existent = await crud_note_version.get_by_version_number(
            async_test_db, note_id=test_note.id, version_number=999
        )
        assert non_existent is None

    async def test_get_next_version_number(self, async_test_db: AsyncSession, test_user, test_note):
        """Test getting next version number."""
        # Initially should be 1
        next_version = await crud_note_version.get_next_version_number(
            async_test_db, note_id=test_note.id
        )
        assert next_version == 1

        # Create a version
        await crud_note_version.create_version(
            async_test_db,
            note_id=test_note.id,
            user_id=test_user.id,
            title="Version 1",
            content="Content 1",
            change_type="edit"
        )

        # Next should be 2
        next_version = await crud_note_version.get_next_version_number(
            async_test_db, note_id=test_note.id
        )
        assert next_version == 2

        # Create another version
        await crud_note_version.create_version(
            async_test_db,
            note_id=test_note.id,
            user_id=test_user.id,
            title="Version 2",
            content="Content 2",
            change_type="edit"
        )

        # Next should be 3
        next_version = await crud_note_version.get_next_version_number(
            async_test_db, note_id=test_note.id
        )
        assert next_version == 3

    async def test_get_versions_between(self, async_test_db: AsyncSession, test_user, test_note):
        """Test getting versions between range."""
        # Create versions
        for i in range(10):
            await crud_note_version.create_version(
                async_test_db,
                note_id=test_note.id,
                user_id=test_user.id,
                title=f"Version {i+1}",
                content=f"Content {i+1}",
                change_type="edit"
            )

        # Get versions between 3 and 7
        versions = await crud_note_version.get_versions_between(
            async_test_db,
            note_id=test_note.id,
            start_version=3,
            end_version=7
        )
        assert len(versions) == 5
        # Should be ordered by version_number asc
        assert versions[0].version_number == 3
        assert versions[4].version_number == 7

        # Test single version range
        single_version = await crud_note_version.get_versions_between(
            async_test_db,
            note_id=test_note.id,
            start_version=5,
            end_version=5
        )
        assert len(single_version) == 1
        assert single_version[0].version_number == 5

        # Test non-existent range
        empty_range = await crud_note_version.get_versions_between(
            async_test_db,
            note_id=test_note.id,
            start_version=20,
            end_version=25
        )
        assert len(empty_range) == 0

    async def test_cleanup_old_versions(self, async_test_db: AsyncSession, test_user, test_note):
        """Test cleaning up old versions."""
        # Create 15 versions
        for i in range(15):
            await crud_note_version.create_version(
                async_test_db,
                note_id=test_note.id,
                user_id=test_user.id,
                title=f"Version {i+1}",
                content=f"Content {i+1}",
                change_type="edit"
            )

        # Verify all versions exist
        all_versions = await crud_note_version.get_by_note(
            async_test_db, note_id=test_note.id, limit=20
        )
        assert len(all_versions) == 15

        # Clean up, keeping only 5 versions
        deleted_count = await crud_note_version.cleanup_old_versions(
            async_test_db, note_id=test_note.id, keep_count=5
        )
        assert deleted_count == 10

        # Verify only 5 versions remain
        remaining_versions = await crud_note_version.get_by_note(
            async_test_db, note_id=test_note.id, limit=20
        )
        assert len(remaining_versions) == 5

        # Should keep the latest 5 versions (11-15)
        version_numbers = [v.version_number for v in remaining_versions]
        assert sorted(version_numbers) == [11, 12, 13, 14, 15]

        # Test cleanup when versions <= keep_count
        deleted_count = await crud_note_version.cleanup_old_versions(
            async_test_db, note_id=test_note.id, keep_count=10
        )
        assert deleted_count == 0

    async def test_different_change_types(self, async_test_db: AsyncSession, test_user, test_note):
        """Test different change types."""
        # Create versions with different change types
        change_types = [
            ("edit", None, None),
            ("ai_generate", "gpt-4", "Generate summary"),
            ("restore", None, None)
        ]

        for i, (change_type, ai_model, ai_prompt) in enumerate(change_types):
            version = await crud_note_version.create_version(
                async_test_db,
                note_id=test_note.id,
                user_id=test_user.id,
                title=f"Version {i+1}",
                content=f"Content {i+1}",
                change_type=change_type,
                ai_model=ai_model,
                ai_prompt=ai_prompt
            )
            assert version.change_type == change_type
            assert version.ai_model == ai_model
            assert version.ai_prompt == ai_prompt

    async def test_version_with_metadata(self, async_test_db: AsyncSession, test_user, test_note):
        """Test version with metadata."""
        metadata = {
            "editor": "vim",
            "language": "markdown",
            "source": "manual",
            "tags_updated": True,
            "links_added": [1, 2, 3]
        }

        version = await crud_note_version.create_version(
            async_test_db,
            note_id=test_note.id,
            user_id=test_user.id,
            title="Metadata Version",
            content="Content with metadata",
            change_type="edit",
            metadata=metadata
        )

        assert version.meta_data == metadata

    async def test_multiple_notes_versions(self, async_test_db: AsyncSession, test_user, test_space, test_note):
        """Test versions for multiple notes."""
        # Create another note
        note2_in = NoteCreate(
            title="Second Note",
            content="Second note content",
            space_id=test_space.id
        )  # type: ignore
        note2 = await crud_note.create(async_test_db, obj_in=note2_in, user_id=test_user.id)

        # Create versions for both notes
        await crud_note_version.create_version(
            async_test_db,
            note_id=test_note.id,
            user_id=test_user.id,
            title="Note 1 Version 1",
            content="Note 1 content",
            change_type="edit"
        )

        await crud_note_version.create_version(
            async_test_db,
            note_id=note2.id,
            user_id=test_user.id,
            title="Note 2 Version 1",
            content="Note 2 content",
            change_type="edit"
        )

        # Get versions for each note
        note1_versions = await crud_note_version.get_by_note(
            async_test_db, note_id=test_note.id
        )
        note2_versions = await crud_note_version.get_by_note(
            async_test_db, note_id=note2.id
        )

        assert len(note1_versions) == 1
        assert len(note2_versions) == 1
        assert note1_versions[0].note_id == test_note.id
        assert note2_versions[0].note_id == note2.id

    async def test_word_count_tracking(self, async_test_db: AsyncSession, test_user, test_note):
        """Test word count tracking in versions."""
        # Create versions with different word counts
        word_counts = [0, 10, 50, 100, 250]

        for i, count in enumerate(word_counts):
            version = await crud_note_version.create_version(
                async_test_db,
                note_id=test_note.id,
                user_id=test_user.id,
                title=f"Version {i+1}",
                content=f"Content with {count} words",
                word_count=count,
                change_type="edit"
            )
            assert version.word_count == count

        # Verify latest version has correct word count
        latest = await crud_note_version.get_latest_version(
            async_test_db, note_id=test_note.id
        )
        assert latest is not None
        assert latest.word_count == 250

    async def test_create_version_with_schema(self, async_test_db: AsyncSession, test_user, test_note):
        """Test creating version using schema."""
        version_data = NoteVersionCreate(
            note_id=test_note.id,
            version_number=1,
            title="Schema Version",
            content="Content created with schema",
            change_type="edit",
            meta_data={"created_with": "schema"}
        )

        version = await crud_note_version.create(
            async_test_db,
            obj_in=version_data,
            user_id=test_user.id
        )

        assert version.note_id == test_note.id
        assert version.title == "Schema Version"
        assert version.content == "Content created with schema"
        assert version.meta_data == {"created_with": "schema"}

    async def test_edge_cases_and_error_handling(self, async_test_db: AsyncSession, test_user, test_note):
        """Test edge cases and error handling."""
        # Test cleanup with fewer versions than keep_count
        await crud_note_version.create_version(
            async_test_db,
            note_id=test_note.id,
            user_id=test_user.id,
            title="Only Version",
            content="Single version",
            change_type="edit"
        )

        # Should not delete anything
        deleted = await crud_note_version.cleanup_old_versions(
            async_test_db, note_id=test_note.id, keep_count=5
        )
        assert deleted == 0

        # Test get_by_version_number with non-existing note
        version = await crud_note_version.get_by_version_number(
            async_test_db, note_id=99999, version_number=1
        )
        assert version is None

        # Test get_latest_version with non-existing note
        latest = await crud_note_version.get_latest_version(
            async_test_db, note_id=99999
        )
        assert latest is None

        # Test get_next_version_number with non-existing note
        next_version = await crud_note_version.get_next_version_number(
            async_test_db, note_id=99999
        )
        assert next_version == 1

    async def test_version_ordering_and_limits(self, async_test_db: AsyncSession, test_user, test_note):
        """Test version ordering and limits."""
        # Create versions in specific order
        for i in range(3):
            await crud_note_version.create_version(
                async_test_db,
                note_id=test_note.id,
                user_id=test_user.id,
                title=f"Version {i+1}",
                content=f"Content {i+1}",
                change_type="edit"
            )

        # Test get_by_note with limit
        versions = await crud_note_version.get_by_note(
            async_test_db, note_id=test_note.id, limit=2
        )
        assert len(versions) == 2
        assert versions[0].version_number == 3  # Latest first
        assert versions[1].version_number == 2

        # Test get_by_note with skip
        versions = await crud_note_version.get_by_note(
            async_test_db, note_id=test_note.id, skip=1, limit=2
        )
        assert len(versions) == 2
        assert versions[0].version_number == 2
        assert versions[1].version_number == 1
