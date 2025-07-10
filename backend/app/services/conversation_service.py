"""Conversation management service using CRUD layer."""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.models.models import Conversation, Message, User
from app.schemas.conversations import ConversationCreate, ConversationUpdate


class ConversationService:
    """对话管理服务."""

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        conversation_data: ConversationCreate,
        user: User,
    ) -> Conversation:
        """创建新对话."""
        return await crud.conversation.create(
            db, obj_in=conversation_data, user_id=user.id
        )

    @staticmethod
    async def get_user_conversations(
        db: AsyncSession,
        user: User,
        space_id: Optional[int] = None,
        mode: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Conversation]:
        """获取用户的对话列表."""
        return await crud.conversation.get_user_conversations(
            db,
            user_id=user.id,
            space_id=space_id,
            mode=mode,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def get_conversation_by_id(
        db: AsyncSession, conversation_id: int, user: User
    ) -> Optional[Conversation]:
        """根据ID获取对话."""
        conversation = await crud.conversation.get(db, id=conversation_id)
        
        # 检查权限
        if conversation and conversation.user_id == user.id:
            return conversation
        
        # 如果对话关联到空间，检查空间权限
        if conversation and conversation.space_id:
            space = await crud.space.get(db, id=conversation.space_id)
            if space and space.is_public:
                return conversation
            
            # 检查协作权限
            access = await crud.space.get_user_access(
                db, space_id=conversation.space_id, user_id=user.id
            )
            if access:
                return conversation
        
        return None

    @staticmethod
    async def get_conversation_with_messages(
        db: AsyncSession,
        conversation_id: int,
        user: User,
        message_limit: int = 50,
    ) -> Optional[Conversation]:
        """获取对话及其消息."""
        conversation = await ConversationService.get_conversation_by_id(
            db, conversation_id, user
        )
        if not conversation:
            return None
        
        return await crud.conversation.get_with_messages(
            db, conversation_id=conversation_id, message_limit=message_limit
        )

    @staticmethod
    async def update_conversation(
        db: AsyncSession,
        conversation: Conversation,
        conversation_data: ConversationUpdate,
    ) -> Conversation:
        """更新对话信息."""
        return await crud.conversation.update(
            db, db_obj=conversation, obj_in=conversation_data
        )

    @staticmethod
    async def delete_conversation(
        db: AsyncSession, conversation: Conversation
    ) -> bool:
        """删除对话."""
        await crud.conversation.remove(db, id=conversation.id)
        return True

    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: int,
        role: str,
        content: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        token_count: Optional[int] = None,
        meta_data: Optional[dict] = None,
        attachments: Optional[list] = None,
    ) -> Message:
        """添加消息到对话."""
        # 创建消息
        message = await crud.message.create_message(
            db,
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            provider=provider,
            token_count=token_count,
            meta_data=meta_data,
            attachments=attachments,
        )
        
        # 更新对话统计
        await crud.conversation.update_stats(
            db,
            conversation_id=conversation_id,
            message_delta=1,
            token_delta=token_count or 0,
        )
        
        return message

    @staticmethod
    async def get_conversation_messages(
        db: AsyncSession,
        conversation_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Message]:
        """获取对话的消息列表."""
        return await crud.message.get_conversation_messages(
            db, conversation_id=conversation_id, skip=skip, limit=limit
        )

    @staticmethod
    async def search_conversations(
        db: AsyncSession,
        user: User,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Conversation]:
        """搜索用户的对话."""
        return await crud.conversation.search_by_title(
            db, user_id=user.id, query=query, skip=skip, limit=limit
        )