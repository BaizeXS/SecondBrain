"""自定义模型相关的 Pydantic 模型."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class ModelProvider(str, Enum):
    """模型提供商类型."""
    CUSTOM = "custom"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ModelCapability(str, Enum):
    """模型能力."""
    CHAT = "chat"
    VISION = "vision"
    EMBEDDING = "embedding"
    SEARCH = "search"


class UserCustomModelBase(BaseModel):
    """用户自定义模型基础模型."""
    name: str = Field(..., description="模型名称", min_length=1, max_length=100)
    provider: ModelProvider = Field(..., description="提供商类型")
    endpoint: HttpUrl | str = Field(..., description="API端点URL")
    model_id: str = Field(..., description="模型ID")
    capabilities: list[ModelCapability] = Field(default=[ModelCapability.CHAT], description="模型能力列表")
    is_active: bool = Field(default=True, description="是否启用")
    meta_data: dict = Field(default_factory=dict, description="额外配置信息")


class UserCustomModelCreate(UserCustomModelBase):
    """创建用户自定义模型."""
    api_key: str | None = Field(None, description="API密钥（可选）")


class UserCustomModelUpdate(BaseModel):
    """更新用户自定义模型."""
    name: str | None = Field(None, min_length=1, max_length=100)
    endpoint: HttpUrl | str | None = None
    api_key: str | None = None
    model_id: str | None = None
    capabilities: list[ModelCapability] | None = None
    is_active: bool | None = None
    meta_data: dict | None = None


class UserCustomModelResponse(UserCustomModelBase):
    """用户自定义模型响应."""
    id: int
    user_id: int
    has_api_key: bool = Field(..., description="是否设置了API密钥")
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

    @classmethod
    def from_orm_with_masked_key(cls, db_obj):
        """从ORM对象创建响应，屏蔽API密钥."""
        data = {
            "id": db_obj.id,
            "user_id": db_obj.user_id,
            "name": db_obj.name,
            "provider": db_obj.provider,
            "endpoint": db_obj.endpoint,
            "model_id": db_obj.model_id,
            "capabilities": db_obj.capabilities or [],
            "is_active": db_obj.is_active,
            "meta_data": db_obj.meta_data or {},
            "has_api_key": bool(db_obj.api_key),
            "created_at": db_obj.created_at,
            "updated_at": db_obj.updated_at,
        }
        return cls(**data)


class TestCustomModelRequest(BaseModel):
    """测试自定义模型请求."""
    custom_model_id: int = Field(..., description="自定义模型ID")
    test_message: str = Field(default="Hello, can you hear me?", description="测试消息")


class TestCustomModelResponse(BaseModel):
    """测试自定义模型响应."""
    success: bool
    response: str | None = None
    error: str | None = None
    model_info: dict | None = None
