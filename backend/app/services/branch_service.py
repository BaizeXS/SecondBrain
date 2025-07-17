"""Conversation branching service."""

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.conversation import crud_conversation
from app.crud.message import crud_message
from app.models.models import Message, User
from app.schemas.conversation_branch import (
    BranchCreate,
    BranchHistory,
    BranchInfo,
    BranchListResponse,
)
from app.schemas.conversations import MessageCreate, MessageResponse

logger = logging.getLogger(__name__)


class BranchService:
    """对话分支管理服务."""

    async def create_branch(
        self,
        db: AsyncSession,
        conversation_id: int,
        branch_data: BranchCreate,
        user: User
    ) -> Message:
        """创建新的对话分支."""
        # 验证对话权限
        conversation = await crud_conversation.get(db, id=conversation_id)
        if not conversation or conversation.user_id != user.id:
            raise ValueError("对话不存在或无权访问")

        # 验证父消息
        parent_message = await crud_message.get(db, id=branch_data.from_message_id)
        if not parent_message or parent_message.conversation_id != conversation_id:
            raise ValueError("父消息不存在或不属于此对话")

        # 检查分支名称是否已存在
        existing_branches = await crud_message.get_conversation_branches(db, conversation_id)
        if branch_data.branch_name in existing_branches:
            raise ValueError(f"分支名称 '{branch_data.branch_name}' 已存在")

        # 创建分支的第一条消息（用户消息）
        branch_message = await crud_message.create_branch_message(
            db,
            obj_in=MessageCreate(
                conversation_id=conversation_id,
                role="user",
                content=branch_data.initial_content,
                model=None,
                provider=None,
                meta_data=None,
                attachments=None
            ),
            parent_message_id=branch_data.from_message_id,
            branch_name=branch_data.branch_name
        )

        logger.info(f"Created branch '{branch_data.branch_name}' from message {branch_data.from_message_id}")

        return branch_message

    async def list_branches(
        self,
        db: AsyncSession,
        conversation_id: int,
        user: User
    ) -> BranchListResponse:
        """列出对话的所有分支."""
        # 验证权限
        conversation = await crud_conversation.get(db, id=conversation_id)
        if not conversation or conversation.user_id != user.id:
            raise ValueError("对话不存在或无权访问")

        # 获取所有分支名称
        branch_names = await crud_message.get_conversation_branches(db, conversation_id)

        # 获取每个分支的信息
        branch_infos = []
        active_branch = None

        for branch_name in branch_names:
            messages = await crud_message.get_branch_messages(db, conversation_id, branch_name)

            if messages:
                # 找到活跃分支
                if any(msg.is_active_branch for msg in messages):
                    active_branch = branch_name

                # 获取分支的第一条和最后一条消息
                first_message = messages[0]
                last_message = messages[-1]

                branch_infos.append(BranchInfo(
                    branch_name=branch_name,
                    message_id=first_message.id,
                    created_at=first_message.created_at,
                    message_count=len(messages),
                    last_message=MessageResponse(
                        id=last_message.id,
                        role=last_message.role,
                        content=last_message.content[:100] + "..." if len(last_message.content) > 100 else last_message.content,
                        model=last_message.model,
                        provider=last_message.provider,
                        token_count=last_message.token_count,
                        processing_time=last_message.processing_time,
                        meta_data=last_message.meta_data,
                        attachments=last_message.attachments,
                        created_at=last_message.created_at
                    )
                ))

        # 如果没有明确的分支，检查主线消息
        main_messages = await crud_message.get_by_conversation(
            db, conversation_id=conversation_id, branch_name=None
        )

        if main_messages and not any(branch.branch_name == "main" for branch in branch_infos):
            last_main_message = main_messages[0] if main_messages else None
            branch_infos.insert(0, BranchInfo(
                branch_name="main",
                message_id=main_messages[-1].id if main_messages else 0,
                created_at=main_messages[-1].created_at if main_messages else datetime.now(),
                message_count=len(main_messages),
                last_message=MessageResponse(
                    id=last_main_message.id,
                    role=last_main_message.role,
                    content=last_main_message.content[:100] + "..." if len(last_main_message.content) > 100 else last_main_message.content,
                    model=last_main_message.model,
                    provider=last_main_message.provider,
                    token_count=last_main_message.token_count,
                    processing_time=last_main_message.processing_time,
                    meta_data=last_main_message.meta_data,
                    attachments=last_main_message.attachments,
                    created_at=last_main_message.created_at
                ) if last_main_message else None
            ))

            if active_branch is None:
                active_branch = "main"

        return BranchListResponse(
            branches=branch_infos,
            active_branch=active_branch,
            total=len(branch_infos)
        )

    async def switch_branch(
        self,
        db: AsyncSession,
        conversation_id: int,
        branch_name: str,
        user: User
    ) -> None:
        """切换到指定分支."""
        # 验证权限
        conversation = await crud_conversation.get(db, id=conversation_id)
        if not conversation or conversation.user_id != user.id:
            raise ValueError("对话不存在或无权访问")

        # 验证分支存在
        branches = await crud_message.get_conversation_branches(db, conversation_id)
        if branch_name not in branches and branch_name != "main":
            raise ValueError(f"分支 '{branch_name}' 不存在")

        # 设置活跃分支
        await crud_message.set_active_branch(db, conversation_id, branch_name)

        logger.info(f"Switched to branch '{branch_name}' in conversation {conversation_id}")

    async def get_branch_history(
        self,
        db: AsyncSession,
        conversation_id: int,
        message_id: int | None = None,
        user: User | None = None
    ) -> list[BranchHistory]:
        """获取分支历史树."""
        # 验证权限
        if user:
            conversation = await crud_conversation.get(db, id=conversation_id)
            if not conversation or conversation.user_id != user.id:
                raise ValueError("对话不存在或无权访问")

        # 如果指定了消息ID，获取到根的路径
        if message_id:
            messages = await crud_message.get_message_history_to_root(db, message_id)
        else:
            # 获取所有消息构建完整树
            messages = await crud_message.get_by_conversation(
                db, conversation_id=conversation_id, limit=1000
            )

        # 获取所有分支点
        branch_points = await crud_message.get_branch_point_messages(db, conversation_id)
        branch_point_ids = {msg.id for msg in branch_points}

        # 构建历史记录
        history = []
        for msg in messages:
            # 获取从此消息分出的子分支
            child_branches = []
            if msg.id in branch_point_ids:
                for bp in branch_points:
                    if bp.id == msg.id:
                        # 获取所有子消息的分支名称
                        for child in bp.child_messages:
                            if child.branch_name and child.branch_name not in child_branches:
                                child_branches.append(child.branch_name)

            history.append(BranchHistory(
                message_id=msg.id,
                parent_message_id=msg.parent_message_id,
                branch_name=msg.branch_name,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                is_branch_point=msg.id in branch_point_ids,
                child_branches=child_branches
            ))

        return history

    async def merge_branch(
        self,
        db: AsyncSession,
        conversation_id: int,
        source_branch: str,
        target_message_id: int | None,
        user: User
    ) -> list[Message]:
        """合并分支（将一个分支的消息追加到另一个分支）."""
        # 验证权限
        conversation = await crud_conversation.get(db, id=conversation_id)
        if not conversation or conversation.user_id != user.id:
            raise ValueError("对话不存在或无权访问")

        # 获取源分支的所有消息
        source_messages = await crud_message.get_branch_messages(
            db, conversation_id, source_branch
        )

        if not source_messages:
            raise ValueError(f"源分支 '{source_branch}' 为空")

        # 如果指定了目标消息，验证它
        if target_message_id:
            target_message = await crud_message.get(db, id=target_message_id)
            if not target_message or target_message.conversation_id != conversation_id:
                raise ValueError("目标消息不存在或不属于此对话")
        else:
            # 默认合并到主线的最后一条消息
            main_messages = await crud_message.get_by_conversation(
                db, conversation_id=conversation_id, branch_name=None
            )
            if main_messages:
                target_message = main_messages[0]  # 最新的消息
                target_message_id = target_message.id
            else:
                raise ValueError("无法找到合并目标")

        # 复制源分支的消息到目标位置
        merged_messages = []
        parent_id = target_message_id

        for source_msg in source_messages:
            # 创建消息副本
            new_message = await crud_message.create(
                db,
                obj_in=MessageCreate(
                    conversation_id=conversation_id,
                    role=source_msg.role,
                    content=source_msg.content,
                    model=source_msg.model,
                    provider=source_msg.provider,
                    meta_data={
                        **(source_msg.meta_data or {}),
                        "merged_from": source_branch,
                        "original_message_id": source_msg.id
                    },
                    attachments=source_msg.attachments
                )
            )

            # 更新父消息关系
            new_message.parent_message_id = parent_id
            new_message.branch_name = target_message.branch_name if target_message else None
            new_message.is_active_branch = True

            await db.commit()
            await db.refresh(new_message)

            merged_messages.append(new_message)
            parent_id = new_message.id

        logger.info(f"Merged {len(merged_messages)} messages from branch '{source_branch}'")

        return merged_messages

    async def delete_branch(
        self,
        db: AsyncSession,
        conversation_id: int,
        branch_name: str,
        user: User
    ) -> None:
        """删除分支."""
        # 验证权限
        conversation = await crud_conversation.get(db, id=conversation_id)
        if not conversation or conversation.user_id != user.id:
            raise ValueError("对话不存在或无权访问")

        if branch_name == "main":
            raise ValueError("不能删除主分支")

        # 获取分支的所有消息
        messages = await crud_message.get_branch_messages(db, conversation_id, branch_name)

        # 删除这些消息
        for msg in messages:
            await crud_message.remove(db, id=msg.id)

        logger.info(f"Deleted branch '{branch_name}' with {len(messages)} messages")


# 创建全局实例
branch_service = BranchService()
