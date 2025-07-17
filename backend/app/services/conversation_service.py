"""Conversation management service using CRUD layer."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.crud.message import crud_message
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
        return await crud.crud_conversation.create(
            db, obj_in=conversation_data, user_id=user.id
        )

    @staticmethod
    async def get_user_conversations(
        db: AsyncSession,
        user: User,
        space_id: int | None = None,
        mode: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Conversation]:
        """获取用户的对话列表."""
        return await crud.crud_conversation.get_user_conversations(
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
    ) -> Conversation | None:
        """根据ID获取对话."""
        conversation = await crud.crud_conversation.get(db, id=conversation_id)

        # 检查权限
        if conversation and conversation.user_id == user.id:
            return conversation

        # 如果对话关联到空间，检查空间权限
        if conversation and conversation.space_id:
            space = await crud.crud_space.get(db, id=conversation.space_id)
            if space and space.is_public:
                return conversation

            # 检查协作权限
            access = await crud.crud_space.get_user_access(
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
    ) -> tuple[Conversation, list[Message]] | None:
        """获取对话及其消息."""
        conversation = await ConversationService.get_conversation_by_id(
            db, conversation_id, user
        )
        if not conversation:
            return None

        result = await crud.crud_conversation.get_with_messages(
            db, conversation_id=conversation_id, message_limit=message_limit
        )
        if result[0] is None:
            return None
        return result

    @staticmethod
    async def update_conversation(
        db: AsyncSession,
        conversation: Conversation,
        conversation_data: ConversationUpdate,
    ) -> Conversation:
        """更新对话信息."""
        return await crud.crud_conversation.update(
            db, db_obj=conversation, obj_in=conversation_data
        )

    @staticmethod
    async def delete_conversation(
        db: AsyncSession, conversation: Conversation
    ) -> bool:
        """删除对话."""
        await crud.crud_conversation.remove(db, id=conversation.id)
        return True

    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: int,
        role: str,
        content: str,
        model: str | None = None,
        provider: str | None = None,
        token_count: int | None = None,
        meta_data: dict[str, Any] | None = None,
        attachments: list[dict[str, Any]] | None = None,
        parent_message_id: int | None = None,
        branch_name: str | None = None,
    ) -> Message:
        """添加消息到对话."""
        # 如果指定了父消息，获取其分支信息
        if parent_message_id:
            parent_msg = await crud_message.get(db, id=parent_message_id)
            if parent_msg and parent_msg.conversation_id == conversation_id:
                # 继承父消息的分支
                branch_name = branch_name or parent_msg.branch_name

        # 创建消息
        from app.schemas.conversations import MessageCreate
        message = await crud_message.create(
            db,
            obj_in=MessageCreate(
                conversation_id=conversation_id,
                role=role,
                content=content,
                model=model,
                provider=provider,
                meta_data=meta_data,
                attachments=attachments,
            )
        )

        # 设置分支信息和 token_count
        if hasattr(message, 'parent_message_id'):
            message.parent_message_id = parent_message_id
            message.branch_name = branch_name
            message.is_active_branch = True

        # 设置 token_count
        if token_count is not None and hasattr(message, 'token_count'):
            message.token_count = token_count

        await db.commit()
        await db.refresh(message)

        # 更新对话统计
        await crud.crud_conversation.update_stats(
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
    ) -> list[Message]:
        """获取对话的消息列表."""
        return await crud_message.get_by_conversation(
            db, conversation_id=conversation_id, skip=skip, limit=limit
        )

    @staticmethod
    async def search_conversations(
        db: AsyncSession,
        user: User,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Conversation]:
        """搜索用户的对话."""
        return await crud.crud_conversation.search_by_title(
            db, user_id=user.id, query=query, skip=skip, limit=limit
        )
