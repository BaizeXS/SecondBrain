"""Authentication schemas."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserLogin(BaseModel):
    """用户登录请求模式."""

    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., min_length=6, description="密码")


class UserRegister(BaseModel):
    """用户注册请求模式."""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")


class Token(BaseModel):
    """令牌响应模式."""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class TokenData(BaseModel):
    """令牌数据模式."""

    user_id: Optional[int] = None


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模式."""

    refresh_token: str = Field(..., description="刷新令牌")


class ChangePasswordRequest(BaseModel):
    """修改密码请求模式."""

    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")


class ResetPasswordRequest(BaseModel):
    """重置密码请求模式."""

    email: EmailStr = Field(..., description="邮箱地址")


class ResetPasswordConfirm(BaseModel):
    """确认重置密码模式."""

    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=6, description="新密码")
