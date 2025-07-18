"""Authentication endpoints."""

import logging
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthService, get_current_active_user
from app.core.config import settings
from app.core.database import get_db

# Rate limiting will be handled by middleware or service layer
from app.models.models import User
from app.schemas.auth import (
    ChangePasswordRequest,
    RefreshTokenRequest,
    ResetPasswordConfirm,
    ResetPasswordRequest,
    Token,
    UserLogin,
    UserRegister,
)
from app.schemas.users import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def validate_password_strength(password: str) -> None:
    """Validate password meets security requirements."""
    if len(password) < 8:
        raise ValueError("密码长度至少8位")
    if not any(c.isupper() for c in password):
        raise ValueError("密码必须包含至少一个大写字母")
    if not any(c.islower() for c in password):
        raise ValueError("密码必须包含至少一个小写字母")
    if not any(c.isdigit() for c in password):
        raise ValueError("密码必须包含至少一个数字")


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)) -> Any:
    """用户注册."""

    try:
        # Validate password strength
        validate_password_strength(user_data.password)

        # Normalize input
        user_data.username = user_data.username.lower().strip()
        user_data.email = user_data.email.lower().strip()

        user = await AuthService.create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
        )
        logger.info(f"New user registered: {user_data.username}")
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试",
        ) from e


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """用户登录."""
    # Log login attempt
    client_ip = request.client.host if request.client else "unknown"

    user = await AuthService.authenticate_user(
        db=db, username=form_data.username, password=form_data.password
    )

    if not user:
        logger.warning(
            f"Failed login attempt for {form_data.username} from {client_ip}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户账户已禁用"
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    # 创建刷新令牌
    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})

    logger.info(f"User {user.username} logged in from {client_ip}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/login/json", response_model=Token)
async def login_json(
    request: Request, user_data: UserLogin, db: AsyncSession = Depends(get_db)
) -> Any:
    """JSON格式用户登录."""
    # Log login attempt
    client_ip = request.client.host if request.client else "unknown"

    user = await AuthService.authenticate_user(
        db=db, username=user_data.username, password=user_data.password
    )

    if not user:
        logger.warning(
            f"Failed login attempt for {user_data.username} from {client_ip}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户账户已禁用"
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    # 创建刷新令牌
    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})

    logger.info(f"User {user.username} logged in from {client_ip}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
) -> Any:
    """刷新访问令牌."""
    try:
        # 验证刷新令牌
        payload = AuthService.verify_token(refresh_data.refresh_token)
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌"
            )

        # 获取用户信息
        user = await AuthService.get_user_by_id(db, int(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用"
            )

        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )

        # 创建新的刷新令牌
        new_refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌"
        ) from None


@router.post("/logout")
async def logout() -> Any:
    """用户登出."""
    # 注意：由于JWT是无状态的，实际的登出需要前端删除令牌
    # 在生产环境中，可以维护一个黑名单来撤销令牌
    return {"message": "登出成功"}


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """修改密码."""
    # 验证旧密码
    if not AuthService.verify_password(
        password_data.old_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码错误"
        )

    # 验证新密码强度
    try:
        validate_password_strength(password_data.new_password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    # 更新密码
    current_user.hashed_password = AuthService.get_password_hash(
        password_data.new_password
    )
    await db.commit()

    logger.info(f"User {current_user.username} changed password")
    return {"message": "密码修改成功"}


@router.post("/reset-password")
async def reset_password(
    reset_data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> Any:
    """重置密码请求."""
    user = await AuthService.get_user_by_email(db, reset_data.email)

    if not user:
        # 即使用户不存在，也返回成功消息（安全考虑）
        return {"message": "如果邮箱存在，重置链接已发送"}

    # TODO: 实现邮件发送功能
    # 生成重置令牌并发送邮件
    reset_token = AuthService.create_access_token(
        data={"sub": str(user.id), "type": "password_reset"},
        expires_delta=timedelta(hours=1),  # 1小时有效期
    )

    # 这里应该发送邮件，暂时返回令牌（仅用于开发）
    if settings.DEBUG:
        return {
            "message": "重置链接已发送",
            "reset_token": reset_token,  # 生产环境中不应返回
        }

    return {"message": "如果邮箱存在，重置链接已发送"}


@router.post("/reset-password/confirm")
async def confirm_reset_password(
    confirm_data: ResetPasswordConfirm, db: AsyncSession = Depends(get_db)
) -> Any:
    """确认重置密码."""
    try:
        # 验证重置令牌
        payload = AuthService.verify_token(confirm_data.token)
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if user_id is None or token_type != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="无效的重置令牌"
            )

        # 获取用户并更新密码
        user = await AuthService.get_user_by_id(db, int(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="用户不存在"
            )

        # 验证新密码强度
        try:
            validate_password_strength(confirm_data.new_password)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e

        # 更新密码
        user.hashed_password = AuthService.get_password_hash(confirm_data.new_password)
        await db.commit()

        logger.info(f"User {user.username} reset password")
        return {"message": "密码重置成功"}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="无效的重置令牌"
        ) from None
