"""User endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.api.v1.endpoints.auth import validate_password_strength
from app.core.auth import AuthService, get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.models.models import Conversation, Document, Note, Space, User
from app.schemas.auth import ChangePasswordRequest
from app.schemas.users import UserResponse, UserStats, UserUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """获取当前用户信息."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """更新当前用户信息."""
    # 更新用户信息
    try:
        updated_user = await crud.crud_user.update(
            db, db_obj=current_user, obj_in=user_update
        )
        logger.info(f"User {current_user.username} updated profile")
        return UserResponse.model_validate(updated_user)
    except Exception as e:
        logger.error(f"Failed to update user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新用户信息失败"
        ) from e


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """修改密码."""
    # 验证当前密码
    if not AuthService.verify_password(
        password_data.old_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误",
        )

    # 验证新密码强度
    try:
        validate_password_strength(password_data.new_password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    # 更新密码
    hashed_password = AuthService.get_password_hash(password_data.new_password)
    await crud.crud_user.update(
        db, db_obj=current_user, obj_in={"hashed_password": hashed_password}
    )
    logger.info(f"User {current_user.username} changed password")


@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserStats:
    """获取用户统计信息."""
    # 使用单个查询获取所有统计信息
    stats_query = (
        select(
            func.count(func.distinct(Space.id)).label("space_count"),
            func.count(func.distinct(Document.id)).label("document_count"),
            func.count(func.distinct(Conversation.id)).label("conversation_count"),
            func.count(func.distinct(Note.id)).label("note_count"),
            func.coalesce(func.sum(Document.file_size), 0).label("total_storage"),
        )
        .select_from(User)
        .outerjoin(Space, Space.user_id == User.id)
        .outerjoin(Document, Document.user_id == User.id)
        .outerjoin(Conversation, Conversation.user_id == User.id)
        .outerjoin(Note, Note.user_id == User.id)
        .where(User.id == current_user.id)
        .group_by(User.id)
    )

    result = await db.execute(stats_query)
    stats = result.first()

    if not stats:
        return UserStats(
            total_spaces=0,
            total_documents=0,
            total_conversations=0,
            total_messages=0,
            total_tokens=0,
            total_notes=0,
            daily_usage=current_user.daily_usage,
            usage_limit=settings.RATE_LIMIT_PREMIUM_USER
            if current_user.is_premium
            else settings.RATE_LIMIT_FREE_USER,
            storage_used=0,
            storage_limit=0,  # Storage limit not implemented
        )

    return UserStats(
        total_spaces=stats.space_count or 0,
        total_documents=stats.document_count or 0,
        total_conversations=stats.conversation_count or 0,
        total_messages=0,  # Messages are not directly linked to users
        total_tokens=0,  # Token tracking not implemented yet
        total_notes=stats.note_count or 0,
        daily_usage=current_user.daily_usage,
        usage_limit=settings.RATE_LIMIT_PREMIUM_USER
        if current_user.is_premium
        else settings.RATE_LIMIT_FREE_USER,
        storage_used=int(stats.total_storage or 0),
        storage_limit=0,  # Storage limit not implemented
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    password: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """删除账户（需要密码确认）."""
    # 验证密码
    if not AuthService.verify_password(password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码错误",
        )

    # 删除用户（会级联删除相关数据）
    await crud.crud_user.remove(db, id=current_user.id)
    logger.info(f"User {current_user.username} deleted account")
