"""Unit tests for message CRUD operations.

To run these tests:
    uv run pytest tests/unit/crud/test_message.py -v
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.message import crud_message
from app.crud.user import crud_user
from app.models.models import Message
from app.schemas.conversations import ConversationCreate, MessageCreate
from app.schemas.users import UserCreate


@pytest.fixture
async def test_user(async_test_db: AsyncSession):
    """Create a test user."""
    user_in = UserCreate(
        username="messageuser",
        email="messageuser@example.com",
        password="password123",
        full_name="Message User"
    )
    user = await crud_user.create(async_test_db, obj_in=user_in)
    return user


@pytest.fixture
async def test_conversation(async_test_db: AsyncSession, test_user):
    """Create a test conversation."""
    conv_in = ConversationCreate(
        title="Test Conversation",
        mode="chat"
    ) # type: ignore
    # Create conversation manually since ConversationCreate might not have user_id
    from app.models.models import Conversation
    conversation = Conversation(
        user_id=test_user.id,
        title=conv_in.title,
        mode=conv_in.mode,
        message_count=0,
        total_tokens=0
    )
    async_test_db.add(conversation)
    await async_test_db.commit()
    await async_test_db.refresh(conversation)
    return conversation


class TestCRUDMessage:
    """Test suite for Message CRUD operations."""

    async def test_create_message(self, async_test_db: AsyncSession, test_conversation):
        """Test creating a message."""
        # Create message using CRUD create method
        message_in = MessageCreate(
            conversation_id=test_conversation.id,
            role="user",
            content="Hello, this is a test message",
            model="gpt-4o-mini",
            provider="openai"
        ) # type: ignore
        message = await crud_message.create(async_test_db, obj_in=message_in)

        # Assertions
        assert message.id is not None
        assert message.content == "Hello, this is a test message"
        assert message.role == "user"
        assert message.is_active_branch is True
        assert message.branch_name is None
        assert message.parent_message_id is None
        assert message.model == "gpt-4o-mini"
        assert message.provider == "openai"

    async def test_create_message_with_metadata(self, async_test_db: AsyncSession, test_conversation):
        """Test creating a message with metadata."""
        # Create message with metadata
        message_in = MessageCreate(
            conversation_id=test_conversation.id,
            role="assistant",
            content="Response with metadata",
            model="gpt-4o-mini",
            provider="openai",
            meta_data={"custom_field": "test_value", "temperature": 0.7}
        ) # type: ignore
        message = await crud_message.create(async_test_db, obj_in=message_in)

        # Assertions
        assert message.id is not None
        assert message.content == "Response with metadata"
        assert message.meta_data == {"custom_field": "test_value", "temperature": 0.7}

    async def test_get_by_conversation(self, async_test_db: AsyncSession, test_conversation):
        """Test getting messages by conversation."""
        # Create multiple messages
        for i in range(5):
            message = Message(
                conversation_id=test_conversation.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}"
            )
            async_test_db.add(message)
        await async_test_db.commit()

        # Get messages
        messages = await crud_message.get_by_conversation(
            async_test_db, conversation_id=test_conversation.id
        )

        # Assertions
        assert len(messages) == 5
        # Verify all messages are present
        message_contents = [m.content for m in messages]
        for i in range(5):
            assert f"Message {i}" in message_contents

    async def test_get_by_conversation_with_limit(self, async_test_db: AsyncSession, test_conversation):
        """Test getting messages with pagination."""
        # Create 10 messages
        for i in range(10):
            message = Message(
                conversation_id=test_conversation.id,
                role="user",
                content=f"Message {i}"
            )
            async_test_db.add(message)
        await async_test_db.commit()

        # Get first page
        first_page = await crud_message.get_by_conversation(
            async_test_db, conversation_id=test_conversation.id, limit=5, skip=0
        )
        assert len(first_page) == 5

        # Get second page
        second_page = await crud_message.get_by_conversation(
            async_test_db, conversation_id=test_conversation.id, limit=5, skip=5
        )
        assert len(second_page) == 5

    async def test_branch_messages(self, async_test_db: AsyncSession, test_conversation):
        """Test branch message functionality."""
        # Create main branch messages
        msg1 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="Main message 1",
            branch_name="main",
            is_active_branch=True
        )
        async_test_db.add(msg1)
        await async_test_db.commit()
        await async_test_db.refresh(msg1)

        # Create branch point
        msg2 = Message(
            conversation_id=test_conversation.id,
            role="assistant",
            content="Main message 2",
            branch_name="main",
            parent_message_id=msg1.id,
            is_active_branch=True
        )
        async_test_db.add(msg2)
        await async_test_db.commit()
        await async_test_db.refresh(msg2)

        # Create alternative branch
        await crud_message.create_branch_message(
            async_test_db,
            obj_in=MessageCreate(
                conversation_id=test_conversation.id,
                role="assistant",
                content="Alternative response",
                model="gpt-4o-mini",
                provider="openai"
            ), # type: ignore
            parent_message_id=msg1.id,
            branch_name="alternative"
        )

        # Get branches
        branches = await crud_message.get_conversation_branches(
            async_test_db, test_conversation.id
        )
        assert "main" in branches
        assert "alternative" in branches

        # Get branch messages
        main_messages = await crud_message.get_branch_messages(
            async_test_db, test_conversation.id, "main"
        )
        assert len(main_messages) == 2

        alt_messages = await crud_message.get_branch_messages(
            async_test_db, test_conversation.id, "alternative"
        )
        assert len(alt_messages) == 1

    async def test_set_active_branch(self, async_test_db: AsyncSession, test_conversation):
        """Test setting active branch."""
        # Create messages on two branches
        msg1 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="User message",
            branch_name="main",
            is_active_branch=True
        )
        async_test_db.add(msg1)

        msg2 = Message(
            conversation_id=test_conversation.id,
            role="assistant",
            content="Response on main",
            branch_name="main",
            is_active_branch=True
        )
        async_test_db.add(msg2)

        msg3 = Message(
            conversation_id=test_conversation.id,
            role="assistant",
            content="Response on alt",
            branch_name="alt",
            is_active_branch=False
        )
        async_test_db.add(msg3)

        await async_test_db.commit()

        # Set alt branch as active
        await crud_message.set_active_branch(
            async_test_db, test_conversation.id, "alt"
        )

        # Verify changes
        await async_test_db.refresh(msg1)
        await async_test_db.refresh(msg2)
        await async_test_db.refresh(msg3)

        assert msg1.is_active_branch is False
        assert msg2.is_active_branch is False
        assert msg3.is_active_branch is True

    async def test_get_branch_point_messages(self, async_test_db: AsyncSession, test_conversation):
        """Test getting branch point messages."""
        # Create a linear conversation
        msg1 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="First message"
        )
        async_test_db.add(msg1)
        await async_test_db.commit()
        await async_test_db.refresh(msg1)

        # Create two responses to the same message (branch point)
        msg2a = Message(
            conversation_id=test_conversation.id,
            role="assistant",
            content="Response A",
            parent_message_id=msg1.id,
            branch_name="branch_a"
        )
        async_test_db.add(msg2a)

        msg2b = Message(
            conversation_id=test_conversation.id,
            role="assistant",
            content="Response B",
            parent_message_id=msg1.id,
            branch_name="branch_b"
        )
        async_test_db.add(msg2b)
        await async_test_db.commit()

        # Get branch points
        branch_points = await crud_message.get_branch_point_messages(
            async_test_db, test_conversation.id
        )

        # Should find msg1 as a branch point
        assert len(branch_points) == 1
        assert branch_points[0].id == msg1.id

    async def test_get_message_history_to_root(self, async_test_db: AsyncSession, test_conversation):
        """Test getting message history from a leaf to root."""
        # Create a chain of messages
        msg1 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="Message 1"
        )
        async_test_db.add(msg1)
        await async_test_db.commit()
        await async_test_db.refresh(msg1)

        msg2 = Message(
            conversation_id=test_conversation.id,
            role="assistant",
            content="Message 2",
            parent_message_id=msg1.id
        )
        async_test_db.add(msg2)
        await async_test_db.commit()
        await async_test_db.refresh(msg2)

        msg3 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="Message 3",
            parent_message_id=msg2.id
        )
        async_test_db.add(msg3)
        await async_test_db.commit()
        await async_test_db.refresh(msg3)

        # Get history from msg3 to root
        history = await crud_message.get_message_history_to_root(
            async_test_db, msg3.id
        )

        # Should return messages in order from root to leaf
        assert len(history) == 3
        assert history[0].id == msg1.id
        assert history[1].id == msg2.id
        assert history[2].id == msg3.id

    async def test_count_branch_messages(self, async_test_db: AsyncSession, test_conversation):
        """Test counting messages in a branch."""
        # Create messages on different branches
        for i in range(5):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content=f"Main branch message {i}",
                branch_name="main"
            )
            async_test_db.add(msg)

        for i in range(3):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content=f"Alt branch message {i}",
                branch_name="alt"
            )
            async_test_db.add(msg)

        await async_test_db.commit()

        # Count messages in each branch
        main_count = await crud_message.count_branch_messages(
            async_test_db, test_conversation.id, "main"
        )
        assert main_count == 5

        alt_count = await crud_message.count_branch_messages(
            async_test_db, test_conversation.id, "alt"
        )
        assert alt_count == 3

    async def test_update_message(self, async_test_db: AsyncSession, test_conversation):
        """Test updating a message."""
        # Create a message
        message = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="Original content"
        )
        async_test_db.add(message)
        await async_test_db.commit()
        await async_test_db.refresh(message)

        # Update message - using dict to bypass schema alias issue
        update_dict = {
            "content": "Updated content",
            "meta_data": {"edited": True}
        }
        updated = await crud_message.update(
            async_test_db, db_obj=message, obj_in=update_dict
        )

        # Assertions
        assert updated.content == "Updated content"
        assert updated.meta_data == {"edited": True}

    async def test_delete_message(self, async_test_db: AsyncSession, test_conversation):
        """Test deleting a message."""
        # Create a message
        message = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="To be deleted"
        )
        async_test_db.add(message)
        await async_test_db.commit()
        await async_test_db.refresh(message)

        message_id = message.id

        # Delete message
        deleted = await crud_message.remove(async_test_db, id=message_id)
        assert deleted is not None

        # Verify deletion
        retrieved = await crud_message.get(async_test_db, message_id)
        assert retrieved is None
