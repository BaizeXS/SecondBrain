"""Conversation CRUD operations."""

from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.models import Conversation, Message
from app.schemas.conversations import ConversationCreate, ConversationUpdate


class CRUDConversation(CRUDBase[Conversation, ConversationCreate, ConversationUpdate]):
    """CRUD operations for Conversation model."""

    async def get_user_conversations(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        space_id: Optional[int] = None,
        mode: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Conversation]:
        """Get conversations for a specific user."""
        query = select(Conversation).where(Conversation.user_id == user_id)
        
        if space_id is not None:
            query = query.where(Conversation.space_id == space_id)
        
        if mode:
            query = query.where(Conversation.mode == mode)
        
        query = query.order_by(Conversation.updated_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_with_messages(
        self,
        db: AsyncSession,
        *,
        conversation_id: int,
        message_limit: int = 50,
    ) -> Optional[Conversation]:
        """Get conversation with its messages."""
        # Get conversation
        conversation = await self.get(db, conversation_id)
        if not conversation:
            return None
        
        # Get messages
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(message_limit)
        )
        messages = result.scalars().all()
        conversation.messages = list(reversed(messages))  # Reverse to get chronological order
        
        return conversation

    async def update_stats(
        self,
        db: AsyncSession,
        *,
        conversation_id: int,
        message_delta: int = 0,
        token_delta: int = 0,
    ) -> Optional[Conversation]:
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
    ) -> List[Conversation]:
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
        return result.scalars().all()


class CRUDMessage(CRUDBase[Message, dict, dict]):
    """CRUD operations for Message model."""

    async def get_conversation_messages(
        self,
        db: AsyncSession,
        *,
        conversation_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Message]:
        """Get messages for a specific conversation."""
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create_message(
        self,
        db: AsyncSession,
        *,
        conversation_id: int,
        role: str,
        content: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        token_count: Optional[int] = None,
        meta_data: Optional[dict] = None,
        attachments: Optional[list] = None,
    ) -> Message:
        """Create a new message."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            provider=provider,
            token_count=token_count,
            meta_data=meta_data,
            attachments=attachments,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message


# Create single instances
conversation = CRUDConversation(Conversation)
message = CRUDMessage(Message)