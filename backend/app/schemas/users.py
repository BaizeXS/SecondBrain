"""User schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """用户基础模式."""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")


class UserCreate(UserBase):
    """创建用户模式."""

    password: str = Field(..., min_length=6, description="密码")


class UserUpdate(BaseModel):
    """更新用户模式."""

    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    preferences: Optional[Dict[str, Any]] = Field(None, description="用户偏好设置")


class UserResponse(BaseModel):
    """用户响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_premium: bool
    is_verified: bool
    daily_usage: int
    preferences: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserProfile(BaseModel):
    """用户详细资料模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_premium: bool
    is_verified: bool
    daily_usage: int
    last_reset_date: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # 统计信息
    total_spaces: Optional[int] = 0
    total_documents: Optional[int] = 0
    total_conversations: Optional[int] = 0


class APIKeyCreate(BaseModel):
    """创建API密钥模式."""

    provider: str = Field(..., description="提供商名称")
    key_name: str = Field(..., description="密钥名称")
    api_key: str = Field(..., description="API密钥")


class APIKeyResponse(BaseModel):
    """API密钥响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    key_name: str
    is_active: bool
    usage_count: int
    last_used: Optional[datetime] = None
    created_at: datetime


class APIKeyUpdate(BaseModel):
    """更新API密钥模式."""

    key_name: Optional[str] = Field(None, description="密钥名称")
    is_active: Optional[bool] = Field(None, description="是否启用")


class UserStats(BaseModel):
    """用户统计信息模式."""

    total_conversations: int = 0
    total_messages: int = 0
    total_tokens: int = 0
    total_spaces: int = 0
    total_documents: int = 0
    total_notes: int = 0
    daily_usage: int = 0
    usage_limit: int = 0
    storage_used: int = 0  # 字节
    storage_limit: int = 0  # 字节


class UserPreferences(BaseModel):
    """用户偏好设置模式."""

    theme: str = Field(default="light", description="主题")
    language: str = Field(default="zh-cn", description="语言")
    default_model: Optional[str] = Field(None, description="默认AI模型")
    auto_save: bool = Field(default=True, description="自动保存")
    notification_email: bool = Field(default=True, description="邮件通知")
    notification_browser: bool = Field(default=True, description="浏览器通知")

    # AI设置
    default_temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="默认温度"
    )
    default_max_tokens: Optional[int] = Field(
        None, ge=1, le=4096, description="默认最大令牌数"
    )
    stream_response: bool = Field(default=True, description="流式响应")

    # 隐私设置
    public_profile: bool = Field(default=False, description="公开个人资料")
    share_usage_data: bool = Field(default=False, description="共享使用数据")


class UsageLogResponse(BaseModel):
    """使用日志响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    token_count: Optional[int] = None
    cost: Optional[float] = None
    created_at: datetime


class UserUsageStats(BaseModel):
    """用户使用统计模式."""

    today: UserStats
    this_week: UserStats
    this_month: UserStats
    all_time: UserStats
    recent_logs: List[UsageLogResponse] = []
