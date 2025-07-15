"""Unit tests for conversation CRUD operations.

To run these tests:
    uv run pytest tests/unit/crud/test_conversation.py -v
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.conversation import crud_conversation
from app.crud.message import crud_message
from app.crud.space import crud_space
from app.crud.user import crud_user
from app.models.models import Message
from app.schemas.conversations import (
    ConversationCreate,
    ConversationUpdate,
)
from app.schemas.spaces import SpaceCreate
from app.schemas.users import UserCreate


@pytest.fixture
async def test_user(async_test_db: AsyncSession):
    """Create a test user."""
    user_in = UserCreate(
        username="conversationuser",
        email="conversationuser@example.com",
        password="password123",
        full_name="Conversation User"
    )
    user = await crud_user.create(async_test_db, obj_in=user_in)
    return user


@pytest.fixture
async def test_space(async_test_db: AsyncSession, test_user):
    """Create a test space."""
    space_in = SpaceCreate(
        name="Test Space for Conversations",
        description="A space for testing conversations"
    ) # type: ignore
    space = await crud_space.create(async_test_db, obj_in=space_in, user_id=test_user.id)
    return space


class TestCRUDConversation:
    """Test suite for Conversation CRUD operations."""

    async def test_create_conversation(self, async_test_db: AsyncSession, test_user, test_space):
        """Test creating a conversation."""
        conv_in = ConversationCreate(
            title="Test Conversation",
            mode="chat",
            space_id=test_space.id,
            system_prompt="You are a helpful assistant",
            temperature=0.7,
            max_tokens=1000
        ) # type: ignore
        conversation = await crud_conversation.create(
            async_test_db, obj_in=conv_in, user_id=test_user.id
        )

        # Assertions
        assert conversation.id is not None
        assert conversation.title == "Test Conversation"
        assert conversation.mode == "chat"
        assert conversation.user_id == test_user.id
        assert conversation.space_id == test_space.id
        assert conversation.system_prompt == "You are a helpful assistant"
        assert conversation.temperature == 0.7
        assert conversation.max_tokens == 1000
        assert conversation.message_count == 0
        assert conversation.total_tokens == 0

    async def test_create_conversation_minimal(self, async_test_db: AsyncSession, test_user):
        """Test creating a conversation with minimal data."""
        conv_in = ConversationCreate(
            title="Minimal Conversation",
            mode="chat"
        ) # type: ignore
        conversation = await crud_conversation.create(
            async_test_db, obj_in=conv_in, user_id=test_user.id
        )

        # Assertions
        assert conversation.id is not None
        assert conversation.title == "Minimal Conversation"
        assert conversation.mode == "chat"
        assert conversation.user_id == test_user.id
        assert conversation.space_id is None
        assert conversation.temperature == 0.7  # Default value

    async def test_get_user_conversations(self, async_test_db: AsyncSession, test_user, test_space):
        """Test getting user conversations."""
        # Create multiple conversations
        for i in range(5):
            conv_in = ConversationCreate(
                title=f"Conversation {i}",
                mode="chat" if i % 2 == 0 else "search",
                space_id=test_space.id if i < 3 else None
            ) # type: ignore
            await crud_conversation.create(
                async_test_db, obj_in=conv_in, user_id=test_user.id
            )

        # Get all conversations
        conversations = await crud_conversation.get_user_conversations(
            async_test_db, user_id=test_user.id
        )
        assert len(conversations) == 5

        # Filter by space
        space_conversations = await crud_conversation.get_user_conversations(
            async_test_db, user_id=test_user.id, space_id=test_space.id
        )
        assert len(space_conversations) == 3

        # Filter by mode
        chat_conversations = await crud_conversation.get_user_conversations(
            async_test_db, user_id=test_user.id, mode="chat"
        )
        assert len(chat_conversations) == 3

        search_conversations = await crud_conversation.get_user_conversations(
            async_test_db, user_id=test_user.id, mode="search"
        )
        assert len(search_conversations) == 2

    async def test_get_user_conversations_pagination(self, async_test_db: AsyncSession, test_user):
        """Test pagination for user conversations."""
        # Create 10 conversations
        for i in range(10):
            conv_in = ConversationCreate(
                title=f"Conversation {i}",
                mode="chat"
            ) # type: ignore
            await crud_conversation.create(
                async_test_db, obj_in=conv_in, user_id=test_user.id
            )

        # Test pagination
        first_page = await crud_conversation.get_user_conversations(
            async_test_db, user_id=test_user.id, skip=0, limit=5
        )
        assert len(first_page) == 5

        second_page = await crud_conversation.get_user_conversations(
            async_test_db, user_id=test_user.id, skip=5, limit=5
        )
        assert len(second_page) == 5

        # Ensure different conversations
        first_ids = {c.id for c in first_page}
        second_ids = {c.id for c in second_page}
        assert len(first_ids.intersection(second_ids)) == 0

    async def test_get_with_messages(self, async_test_db: AsyncSession, test_user):
        """Test getting conversation with messages."""
        # Create conversation
        conv_in = ConversationCreate(title="Conversation with Messages", mode="chat") # type: ignore
        conversation = await crud_conversation.create(
            async_test_db, obj_in=conv_in, user_id=test_user.id
        )

        # Add messages
        for i in range(5):
            msg = Message(
                conversation_id=conversation.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}"
            )
            async_test_db.add(msg)
        await async_test_db.commit()

        # Get conversation with messages
        conv, messages = await crud_conversation.get_with_messages(
            async_test_db, conversation_id=conversation.id
        )

        assert conv is not None
        assert messages is not None
        assert len(messages) == 5

        # Check all messages are present (order may vary due to same timestamp)
        message_contents = {msg.content for msg in messages}
        expected_contents = {f"Message {i}" for i in range(5)}
        assert message_contents == expected_contents

        # Check roles are correct
        user_messages = [msg for msg in messages if msg.role == "user"]
        assistant_messages = [msg for msg in messages if msg.role == "assistant"]
        assert len(user_messages) == 3  # 0, 2, 4
        assert len(assistant_messages) == 2  # 1, 3

    async def test_get_with_messages_branch_filter(self, async_test_db: AsyncSession, test_user):
        """Test getting conversation with branch-filtered messages."""
        # Create conversation
        conv_in = ConversationCreate(title="Branched Conversation", mode="chat") # type: ignore
        conversation = await crud_conversation.create(
            async_test_db, obj_in=conv_in, user_id=test_user.id
        )

        # Add messages on different branches
        for i in range(3):
            msg = Message(
                conversation_id=conversation.id,
                role="user",
                content=f"Main branch message {i}",
                branch_name="main",
                is_active_branch=True
            )
            async_test_db.add(msg)

        for i in range(2):
            msg = Message(
                conversation_id=conversation.id,
                role="user",
                content=f"Alt branch message {i}",
                branch_name="alt",
                is_active_branch=False
            )
            async_test_db.add(msg)

        await async_test_db.commit()

        # Get default (active branch)
        conv_active, active_messages = await crud_conversation.get_with_messages(
            async_test_db, conversation_id=conversation.id
        )
        assert conv_active is not None
        assert active_messages is not None
        assert len(active_messages) == 3
        assert all("Main branch" in msg.content for msg in active_messages)

        # Get specific branch
        conv_alt, alt_messages = await crud_conversation.get_with_messages(
            async_test_db, conversation_id=conversation.id, branch_name="alt"
        )
        assert conv_alt is not None
        assert alt_messages is not None
        assert len(alt_messages) == 2
        assert all("Alt branch" in msg.content for msg in alt_messages)

    async def test_update_stats(self, async_test_db: AsyncSession, test_user):
        """Test updating conversation statistics."""
        # Create conversation
        conv_in = ConversationCreate(title="Stats Test", mode="chat") # type: ignore
        conversation = await crud_conversation.create(
            async_test_db, obj_in=conv_in, user_id=test_user.id
        )

        # Initial stats
        assert conversation.message_count == 0
        assert conversation.total_tokens == 0

        # Update stats
        updated = await crud_conversation.update_stats(
            async_test_db,
            conversation_id=conversation.id,
            message_delta=2,
            token_delta=100
        )

        assert updated is not None
        assert updated.message_count == 2
        assert updated.total_tokens == 100

        # Update again
        updated2 = await crud_conversation.update_stats(
            async_test_db,
            conversation_id=conversation.id,
            message_delta=1,
            token_delta=50
        )

        assert updated2 is not None
        assert updated2.message_count == 3
        assert updated2.total_tokens == 150

    async def test_search_by_title(self, async_test_db: AsyncSession, test_user):
        """Test searching conversations by title."""
        # Create conversations with different titles
        titles = [
            "Python Programming Tutorial",
            "JavaScript Basics",
            "Python Advanced Topics",
            "Machine Learning with Python",
            "Web Development"
        ]

        for title in titles:
            conv_in = ConversationCreate(title=title, mode="chat") # type: ignore
            await crud_conversation.create(
                async_test_db, obj_in=conv_in, user_id=test_user.id
            )

        # Search for Python
        python_results = await crud_conversation.search_by_title(
            async_test_db, user_id=test_user.id, query="Python"
        )
        assert len(python_results) == 3
        assert all("Python" in conv.title for conv in python_results)

        # Search for JavaScript
        js_results = await crud_conversation.search_by_title(
            async_test_db, user_id=test_user.id, query="JavaScript"
        )
        assert len(js_results) == 1
        assert js_results[0].title == "JavaScript Basics"

        # Case insensitive search
        lower_results = await crud_conversation.search_by_title(
            async_test_db, user_id=test_user.id, query="python"
        )
        assert len(lower_results) == 3

    async def test_update_conversation(self, async_test_db: AsyncSession, test_user):
        """Test updating a conversation."""
        # Create conversation
        conv_in = ConversationCreate(
            title="Original Title",
            mode="chat",
            temperature=0.7
        ) # type: ignore
        conversation = await crud_conversation.create(
            async_test_db, obj_in=conv_in, user_id=test_user.id
        )

        # Update conversation
        update_data = ConversationUpdate(
            title="Updated Title",
            system_prompt="New system prompt",
            temperature=0.9,
            max_tokens=2000
        ) # type: ignore
        updated = await crud_conversation.update(
            async_test_db, db_obj=conversation, obj_in=update_data
        )

        # Assertions
        assert updated.title == "Updated Title"
        assert updated.system_prompt == "New system prompt"
        assert updated.temperature == 0.9
        assert updated.max_tokens == 2000
        # Mode should not change
        assert updated.mode == "chat"

    async def test_delete_conversation(self, async_test_db: AsyncSession, test_user):
        """Test deleting a conversation and its cascade delete of messages."""
        # Create conversation
        conv_in = ConversationCreate(title="To Be Deleted", mode="chat") # type: ignore
        conversation = await crud_conversation.create(
            async_test_db, obj_in=conv_in, user_id=test_user.id
        )
        conv_id = conversation.id

        # Add messages
        for i in range(3):
            msg = Message(
                conversation_id=conv_id,
                role="user",
                content=f"Message {i}"
            )
            async_test_db.add(msg)
        await async_test_db.commit()

        # Verify messages exist
        messages = await crud_message.get_by_conversation(
            async_test_db, conversation_id=conv_id
        )
        assert len(messages) == 3

        # Delete conversation
        deleted = await crud_conversation.remove(async_test_db, id=conv_id)
        assert deleted is not None

        # Verify conversation is deleted
        retrieved = await crud_conversation.get(async_test_db, conv_id)
        assert retrieved is None

        # Verify messages are cascade deleted
        messages_after = await crud_message.get_by_conversation(
            async_test_db, conversation_id=conv_id
        )
        assert len(messages_after) == 0

    async def test_nonexistent_conversation(self, async_test_db: AsyncSession):
        """Test operations on non-existent conversation."""
        # Try to get non-existent conversation
        conversation = await crud_conversation.get(async_test_db, 99999)
        assert conversation is None

        # Try to get with messages
        conv, messages = await crud_conversation.get_with_messages(
            async_test_db, conversation_id=99999
        )
        assert conv is None
        assert messages is None

        # Try to update stats
        updated = await crud_conversation.update_stats(
            async_test_db, conversation_id=99999, message_delta=1
        )
        assert updated is None
