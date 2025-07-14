"""Message CRUD operations."""

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.models import Message
from app.schemas.conversations import MessageCreate, MessageUpdate


class CRUDMessage(CRUDBase[Message, MessageCreate, MessageUpdate]):
    """Message CRUD class."""

    async def create(
        self, db: AsyncSession, *, obj_in: MessageCreate, **kwargs
    ) -> Message:
        """Create a new message with proper defaults."""
        # Extract data from schema
        create_data = obj_in.model_dump(exclude_unset=True)

        # Create message
        db_obj = Message(**create_data, **kwargs)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_conversation(
        self,
        db: AsyncSession,
        *,
        conversation_id: int,
        branch_name: str | None = None,
        limit: int = 50,
        skip: int = 0,
    ) -> list[Message]:
        """获取对话的消息列表."""
        query = select(self.model).where(
            self.model.conversation_id == conversation_id
        )

        # 如果指定了分支，只获取该分支的消息
        if branch_name:
            query = query.where(self.model.branch_name == branch_name)
        else:
            # 默认只获取活跃分支的消息
            query = query.where(self.model.is_active_branch.is_(True))

        query = query.order_by(self.model.created_at.desc())

        if limit:
            query = query.limit(limit)
        if skip:
            query = query.offset(skip)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_conversation_branches(
        self,
        db: AsyncSession,
        conversation_id: int
    ) -> list[str]:
        """获取对话的所有分支名称."""
        query = select(self.model.branch_name).where(
            and_(
                self.model.conversation_id == conversation_id,
                self.model.branch_name.isnot(None)
            )
        ).distinct()

        result = await db.execute(query)
        return [name for (name,) in result.fetchall()]

    async def get_branch_messages(
        self,
        db: AsyncSession,
        conversation_id: int,
        branch_name: str
    ) -> list[Message]:
        """获取特定分支的所有消息."""
        query = select(self.model).where(
            and_(
                self.model.conversation_id == conversation_id,
                self.model.branch_name == branch_name
            )
        ).order_by(self.model.created_at)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_branch_point_messages(
        self,
        db: AsyncSession,
        conversation_id: int
    ) -> list[Message]:
        """获取所有分支点消息（有子消息的消息）."""
        # 查找所有作为父消息的消息
        parent_ids_query = select(self.model.parent_message_id).where(
            and_(
                self.model.conversation_id == conversation_id,
                self.model.parent_message_id.isnot(None)
            )
        ).distinct()

        parent_ids_result = await db.execute(parent_ids_query)
        parent_ids = [pid for (pid,) in parent_ids_result.fetchall()]

        if not parent_ids:
            return []

        # 获取这些父消息的详细信息
        query = select(self.model).where(
            self.model.id.in_(parent_ids)
        ).options(selectinload(self.model.child_messages))

        result = await db.execute(query)
        return list(result.scalars().all())

    async def set_active_branch(
        self,
        db: AsyncSession,
        conversation_id: int,
        branch_name: str
    ) -> None:
        """设置活跃分支."""
        # 先将所有消息设为非活跃
        await db.execute(
            update(self.model).where(
                self.model.conversation_id == conversation_id
            ).values(is_active_branch=False)
        )

        # 设置指定分支为活跃
        await db.execute(
            update(self.model).where(
                and_(
                    self.model.conversation_id == conversation_id,
                    self.model.branch_name == branch_name
                )
            ).values(is_active_branch=True)
        )

        await db.commit()

    async def create_branch_message(
        self,
        db: AsyncSession,
        *,
        obj_in: MessageCreate,
        parent_message_id: int,
        branch_name: str
    ) -> Message:
        """创建分支消息."""
        # Extract data from schema
        create_data = obj_in.model_dump(exclude_unset=True)

        # Add branch-specific fields
        create_data.update({
            "parent_message_id": parent_message_id,
            "branch_name": branch_name,
            "is_active_branch": False  # 新分支默认不活跃
        })

        db_obj = Message(**create_data)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_message_history_to_root(
        self,
        db: AsyncSession,
        message_id: int
    ) -> list[Message]:
        """获取从指定消息到根消息的历史路径."""
        messages = []
        current_id = message_id

        while current_id:
            query = select(self.model).where(self.model.id == current_id)
            result = await db.execute(query)
            message = result.scalar_one_or_none()

            if not message:
                break

            messages.append(message)
            current_id = message.parent_message_id

        return list(reversed(messages))  # 返回从根到当前消息的顺序

    async def count_branch_messages(
        self,
        db: AsyncSession,
        conversation_id: int,
        branch_name: str
    ) -> int:
        """统计分支中的消息数量."""
        from sqlalchemy import func

        query = select(func.count(self.model.id)).where(
            and_(
                self.model.conversation_id == conversation_id,
                self.model.branch_name == branch_name
            )
        )

        result = await db.execute(query)
        return result.scalar() or 0


crud_message = CRUDMessage(Message)
