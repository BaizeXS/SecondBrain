"""Conversation CRUD operations."""

from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.models import Conversation, Message
from app.schemas.conversations import ConversationCreate, ConversationUpdate


class CRUDConversation(CRUDBase[Conversation, ConversationCreate, ConversationUpdate]):
    """CRUD operations for Conversation model."""

    async def create(
        self, db: AsyncSession, *, obj_in: ConversationCreate, user_id: int, **kwargs: Any
    ) -> Conversation:
        """Create a new conversation with user_id."""
        create_data = obj_in.model_dump()
        db_obj = Conversation(**create_data, user_id=user_id, **kwargs)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_user_conversations(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        space_id: int | None = None,
        mode: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Conversation]:
        """Get conversations for a specific user."""
        query = select(Conversation).where(Conversation.user_id == user_id)

        if space_id is not None:
            query = query.where(Conversation.space_id == space_id)

        if mode:
            query = query.where(Conversation.mode == mode)

        query = query.order_by(Conversation.updated_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_with_messages(
        self,
        db: AsyncSession,
        *,
        conversation_id: int,
        message_limit: int = 50,
        branch_name: str | None = None,
    ) -> tuple[Conversation, list[Message]] | tuple[None, None]:
        """Get conversation with its messages.

        Returns a tuple of (conversation, messages) or (None, None) if not found.
        """
        # Get conversation
        conversation = await self.get(db, conversation_id)
        if not conversation:
            return None, None

        # Get messages query
        query = select(Message).where(Message.conversation_id == conversation_id)

        # Filter by branch if specified
        if branch_name:
            query = query.where(Message.branch_name == branch_name)
        else:
            # Get only active branch messages by default
            query = query.where(Message.is_active_branch.is_(True))

        query = query.order_by(Message.created_at.desc()).limit(message_limit)

        result = await db.execute(query)
        messages = list(reversed(result.scalars().all()))  # Reverse to get chronological order

        return conversation, messages

    async def update_stats(
        self,
        db: AsyncSession,
        *,
        conversation_id: int,
        message_delta: int = 0,
        token_delta: int = 0,
    ) -> Conversation | None:
        """Update conversation statistics."""
        conversation = await self.get(db, conversation_id)
        if conversation:
            conversation.message_count += message_delta
            conversation.total_tokens += token_delta
            await db.commit()
            await db.refresh(conversation)
        return conversation

    async def search_by_title(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Conversation]:
        """Search conversations by title."""
        result = await db.execute(
            select(Conversation)
            .where(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.title.ilike(f"%{query}%")
                )
            )
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


# Create single instance
crud_conversation = CRUDConversation(Conversation)
