"""User endpoints v2 - 使用服务层和CRUD层的完整版本."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core.auth import AuthService, get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User
from app.schemas.users import UserResponse, UserUpdate

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
    # 检查用户名是否已被使用
    if user_update.username and user_update.username != current_user.username:
        existing = await crud.crud_user.get_by_username(db, username=user_update.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用",
            )

    # 检查邮箱是否已被使用
    if user_update.email and user_update.email != current_user.email:
        existing = await crud.crud_user.get_by_email(db, email=user_update.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用",
            )

    # 更新用户信息
    updated_user = await crud.crud_user.update(db, db_obj=current_user, obj_in=user_update)
    return UserResponse.model_validate(updated_user)


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    current_password: str,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """修改密码."""
    # 验证当前密码
    if not AuthService.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误",
        )

    # 验证新密码
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度至少为6位",
        )

    # 更新密码
    hashed_password = AuthService.get_password_hash(new_password)
    await crud.crud_user.update(
        db, db_obj=current_user, obj_in={"hashed_password": hashed_password}
    )


@router.get("/me/stats", response_model=dict)
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """获取用户统计信息."""
    # 获取空间数量
    space_count = await crud.crud_space.get_count(
        db, query=crud.crud_space.model.user_id == current_user.id
    )

    # 获取文档数量
    document_count = await crud.crud_document.get_count(
        db, query=crud.crud_document.model.user_id == current_user.id
    )

    # 获取对话数量
    conversation_count = await crud.crud_conversation.get_count(
        db, query=crud.crud_conversation.model.user_id == current_user.id
    )

    # 计算存储使用量
    documents = await crud.crud_document.get_user_documents(db, user_id=current_user.id)
    total_storage = sum(doc.file_size for doc in documents)

    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "is_premium": current_user.is_premium,
        "stats": {
            "spaces": space_count,
            "documents": document_count,
            "conversations": conversation_count,
            "storage_bytes": total_storage,
            "storage_mb": round(total_storage / 1024 / 1024, 2),
        },
        "limits": {
            "max_spaces": 10 if current_user.is_premium else 5,
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "daily_api_calls": settings.RATE_LIMIT_PREMIUM_USER if current_user.is_premium else settings.RATE_LIMIT_FREE_USER,
        },
        "usage": {
            "daily_api_calls": current_user.daily_usage,
            "space_usage_percent": round(space_count / (10 if current_user.is_premium else 5) * 100, 1),
        },
    }


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
