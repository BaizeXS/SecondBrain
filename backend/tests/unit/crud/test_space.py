"""Unit tests for space CRUD operations.

To run these tests:
    uv run pytest tests/unit/crud/test_space.py -v
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.space import crud_space
from app.crud.user import crud_user
from app.schemas.spaces import SpaceCreate, SpaceUpdate
from app.schemas.users import UserCreate


@pytest.fixture
async def test_user(async_test_db: AsyncSession):
    """Create a test user."""
    user_in = UserCreate(
        username="spaceowner",
        email="spaceowner@example.com",
        password="password123",
        full_name="Space Owner"
    )
    user = await crud_user.create(async_test_db, obj_in=user_in)
    return user


@pytest.fixture
async def test_collaborator(async_test_db: AsyncSession):
    """Create a test collaborator user."""
    user_in = UserCreate(
        username="collaborator",
        email="collaborator@example.com",
        password="password123",
        full_name="Collaborator"
    )
    user = await crud_user.create(async_test_db, obj_in=user_in)
    return user


@pytest.fixture
async def test_space_data():
    """Test space data."""
    return {
        "name": "My Research Space",
        "description": "A space for research notes",
        "color": "#FF5733",
        "icon": "🔬",
        "is_public": False,
        "allow_collaboration": True,
        "tags": ["research", "science"],
        "meta_data": {"field": "biology"}
    }


class TestCRUDSpace:
    """Test suite for Space CRUD operations."""

    async def test_create_space(
        self, async_test_db: AsyncSession, test_user, test_space_data
    ):
        """Test creating a space."""
        # Create space
        space_in = SpaceCreate(**test_space_data)
        space = await crud_space.create(
            async_test_db, obj_in=space_in, user_id=test_user.id
        )

        # Assertions
        assert space.name == test_space_data["name"]
        assert space.description == test_space_data["description"]
        assert space.color == test_space_data["color"]
        assert space.user_id == test_user.id
        assert space.document_count == 0
        assert space.note_count == 0
        assert space.total_size == 0

    async def test_get_user_spaces(
        self, async_test_db: AsyncSession, test_user, test_space_data
    ):
        """Test getting user's spaces."""
        # Create multiple spaces
        for i in range(3):
            space_data = test_space_data.copy()
            space_data["name"] = f"Space {i}"
            space_in = SpaceCreate(**space_data)
            await crud_space.create(
                async_test_db, obj_in=space_in, user_id=test_user.id
            )

        # Get user's spaces
        spaces = await crud_space.get_user_spaces(
            async_test_db, user_id=test_user.id
        )

        # Assertions
        assert len(spaces) == 3
        # Check all names are present
        space_names = [s.name for s in spaces]
        assert "Space 0" in space_names
        assert "Space 1" in space_names
        assert "Space 2" in space_names

    async def test_get_user_spaces_with_public(
        self, async_test_db: AsyncSession, test_user, test_collaborator, test_space_data
    ):
        """Test getting user's spaces including public ones."""
        # Create user's private space
        private_space_in = SpaceCreate(**test_space_data)
        await crud_space.create(
            async_test_db, obj_in=private_space_in, user_id=test_user.id
        )

        # Create another user's public space
        public_space_data = test_space_data.copy()
        public_space_data["name"] = "Public Space"
        public_space_data["is_public"] = True
        public_space_in = SpaceCreate(**public_space_data)
        await crud_space.create(
            async_test_db, obj_in=public_space_in, user_id=test_collaborator.id
        )

        # Get spaces without public
        spaces = await crud_space.get_user_spaces(
            async_test_db, user_id=test_user.id, include_public=False
        )
        assert len(spaces) == 1

        # Get spaces with public
        spaces_with_public = await crud_space.get_user_spaces(
            async_test_db, user_id=test_user.id, include_public=True
        )
        assert len(spaces_with_public) == 2

    async def test_get_by_name(
        self, async_test_db: AsyncSession, test_user, test_space_data
    ):
        """Test getting space by name."""
        # Create space
        space_in = SpaceCreate(**test_space_data)
        created_space = await crud_space.create(
            async_test_db, obj_in=space_in, user_id=test_user.id
        )

        # Get by name
        space = await crud_space.get_by_name(
            async_test_db,
            name=test_space_data["name"],
            user_id=test_user.id
        )

        # Assertions
        assert space is not None
        assert space.id == created_space.id
        assert space.name == test_space_data["name"]

    async def test_get_by_name_different_user(
        self, async_test_db: AsyncSession, test_user, test_collaborator, test_space_data
    ):
        """Test that spaces are isolated by user."""
        # Create space for test_user
        space_in = SpaceCreate(**test_space_data)
        await crud_space.create(
            async_test_db, obj_in=space_in, user_id=test_user.id
        )

        # Try to get by name with different user
        space = await crud_space.get_by_name(
            async_test_db,
            name=test_space_data["name"],
            user_id=test_collaborator.id
        )

        # Should not find it
        assert space is None

    async def test_update_space(
        self, async_test_db: AsyncSession, test_user, test_space_data
    ):
        """Test updating a space."""
        # Create space
        space_in = SpaceCreate(**test_space_data)
        space = await crud_space.create(
            async_test_db, obj_in=space_in, user_id=test_user.id
        )

        # Update space
        update_data = SpaceUpdate(
            name="Updated Space",
            description="Updated description",
            color="#00FF00"
        ) # type: ignore
        updated_space = await crud_space.update(
            async_test_db, db_obj=space, obj_in=update_data
        )

        # Assertions
        assert updated_space.name == "Updated Space"
        assert updated_space.description == "Updated description"
        assert updated_space.color == "#00FF00"
        # Unchanged fields
        assert updated_space.icon == test_space_data["icon"]

    async def test_delete_space(
        self, async_test_db: AsyncSession, test_user, test_space_data
    ):
        """Test deleting a space."""
        # Create space
        space_in = SpaceCreate(**test_space_data)
        space = await crud_space.create(
            async_test_db, obj_in=space_in, user_id=test_user.id
        )

        # Delete space
        deleted_space = await crud_space.remove(async_test_db, id=space.id)

        # Assertions
        assert deleted_space is not None
        assert deleted_space.id == space.id

        # Verify it's deleted
        space_check = await crud_space.get(async_test_db, space.id)
        assert space_check is None

    async def test_update_stats(
        self, async_test_db: AsyncSession, test_user, test_space_data
    ):
        """Test updating space statistics."""
        # Create space
        space_in = SpaceCreate(**test_space_data)
        space = await crud_space.create(
            async_test_db, obj_in=space_in, user_id=test_user.id
        )

        # Update stats
        updated_space = await crud_space.update_stats(
            async_test_db,
            space_id=space.id,
            document_delta=5,
            note_delta=10,
            size_delta=1024
        )

        # Assertions
        assert updated_space is not None
        assert updated_space.document_count == 5
        assert updated_space.note_count == 10
        assert updated_space.total_size == 1024

        # Update again with negative delta
        updated_space = await crud_space.update_stats(
            async_test_db,
            space_id=space.id,
            document_delta=-2,
            note_delta=-3,
            size_delta=-512
        )

        assert updated_space.document_count == 3 # type: ignore
        assert updated_space.note_count == 7 # type: ignore
        assert updated_space.total_size == 512 # type: ignore

    async def test_add_collaborator(
        self, async_test_db: AsyncSession, test_user, test_collaborator, test_space_data
    ):
        """Test adding a collaborator to a space."""
        # Create space
        space_in = SpaceCreate(**test_space_data)
        space = await crud_space.create(
            async_test_db, obj_in=space_in, user_id=test_user.id
        )

        # Add collaborator
        collaboration = await crud_space.add_collaborator(
            async_test_db,
            space_id=space.id,
            user_id=test_collaborator.id,
            invited_by=test_user.id,
            role="editor",
            can_edit=True,
            can_delete=False,
            can_invite=False
        )

        # Assertions
        assert collaboration.space_id == space.id # type: ignore
        assert collaboration.user_id == test_collaborator.id # type: ignore
        assert collaboration.invited_by == test_user.id # type: ignore
        assert collaboration.role == "editor" # type: ignore
        assert collaboration.can_edit is True # type: ignore
        assert collaboration.can_delete is False # type: ignore

    async def test_get_collaborations(
        self, async_test_db: AsyncSession, test_user, test_collaborator, test_space_data
    ):
        """Test getting all collaborations for a space."""
        # Create space
        space_in = SpaceCreate(**test_space_data)
        space = await crud_space.create(
            async_test_db, obj_in=space_in, user_id=test_user.id
        )

        # Add multiple collaborators
        # Create another collaborator
        another_user_in = UserCreate(
            username="another",
            email="another@example.com",
            password="password123"
        ) # type: ignore
        another_user = await crud_user.create(async_test_db, obj_in=another_user_in)

        # Add collaborators
        await crud_space.add_collaborator(
            async_test_db,
            space_id=space.id,
            user_id=test_collaborator.id,
            invited_by=test_user.id,
            role="editor"
        )
        await crud_space.add_collaborator(
            async_test_db,
            space_id=space.id,
            user_id=another_user.id,
            invited_by=test_user.id,
            role="viewer"
        )

        # Get collaborations
        collaborations = await crud_space.get_collaborations(
            async_test_db, space_id=space.id
        )

        # Assertions
        assert len(collaborations) == 2
        assert collaborations[0].role == "editor"
        assert collaborations[1].role == "viewer"

    async def test_get_user_access(
        self, async_test_db: AsyncSession, test_user, test_collaborator, test_space_data
    ):
        """Test checking user access to a space."""
        # Create space
        space_in = SpaceCreate(**test_space_data)
        space = await crud_space.create(
            async_test_db, obj_in=space_in, user_id=test_user.id
        )

        # Initially no access
        access = await crud_space.get_user_access(
            async_test_db,
            space_id=space.id,
            user_id=test_collaborator.id
        )
        assert access is None

        # Add collaborator
        await crud_space.add_collaborator(
            async_test_db,
            space_id=space.id,
            user_id=test_collaborator.id,
            invited_by=test_user.id,
            role="editor"
        )

        # Now should have access
        access = await crud_space.get_user_access(
            async_test_db,
            space_id=space.id,
            user_id=test_collaborator.id
        )
        assert access is not None
        assert access.role == "editor"

    async def test_pagination(
        self, async_test_db: AsyncSession, test_user, test_space_data
    ):
        """Test pagination of user spaces."""
        # Create 10 spaces
        for i in range(10):
            space_data = test_space_data.copy()
            space_data["name"] = f"Space {i:02d}"
            space_in = SpaceCreate(**space_data)
            await crud_space.create(
                async_test_db, obj_in=space_in, user_id=test_user.id
            )

        # Test pagination
        first_page = await crud_space.get_user_spaces(
            async_test_db, user_id=test_user.id, skip=0, limit=5
        )
        assert len(first_page) == 5

        second_page = await crud_space.get_user_spaces(
            async_test_db, user_id=test_user.id, skip=5, limit=5
        )
        assert len(second_page) == 5

        # Verify no overlap between pages
        first_page_names = {s.name for s in first_page}
        second_page_names = {s.name for s in second_page}
        assert len(first_page_names & second_page_names) == 0

        # Verify all 10 spaces are accounted for
        all_names = first_page_names | second_page_names
        assert len(all_names) == 10

    async def test_add_duplicate_collaborator(
        self, async_test_db: AsyncSession, test_user, test_collaborator, test_space_data
    ):
        """Test that adding the same collaborator twice returns None."""
        # Create space
        space_in = SpaceCreate(**test_space_data)
        space = await crud_space.create(
            async_test_db, obj_in=space_in, user_id=test_user.id
        )

        # Add collaborator first time
        collaboration = await crud_space.add_collaborator(
            async_test_db,
            space_id=space.id,
            user_id=test_collaborator.id,
            invited_by=test_user.id,
            role="editor",
            can_edit=True
        )
        assert collaboration is not None
        assert collaboration.user_id == test_collaborator.id

        # Try to add the same collaborator again
        duplicate = await crud_space.add_collaborator(
            async_test_db,
            space_id=space.id,
            user_id=test_collaborator.id,
            invited_by=test_user.id,
            role="admin",  # Even with different role
            can_edit=True,
            can_delete=True
        )
        assert duplicate is None

        # Verify there's still only one collaboration
        collaborations = await crud_space.get_collaborations(
            async_test_db, space_id=space.id
        )
        assert len(collaborations) == 1
        assert collaborations[0].role == "editor"  # Original role preserved
