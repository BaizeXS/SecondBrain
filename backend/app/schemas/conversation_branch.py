"""Conversation branch schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.conversations import MessageResponse


class BranchCreate(BaseModel):
    """创建分支请求."""

    from_message_id: int = Field(..., description="从哪条消息开始分支")
    branch_name: str = Field(..., description="分支名称", max_length=100)
    initial_content: str = Field(..., description="分支的第一条消息内容")


class BranchInfo(BaseModel):
    """分支信息."""

    branch_name: str
    message_id: int
    created_at: datetime
    message_count: int
    last_message: MessageResponse | None = None


class BranchListResponse(BaseModel):
    """分支列表响应."""

    branches: list[BranchInfo]
    active_branch: str | None = None
    total: int


class BranchSwitch(BaseModel):
    """切换分支请求."""

    branch_name: str = Field(..., description="要切换到的分支名称")


class BranchMerge(BaseModel):
    """合并分支请求."""

    source_branch: str = Field(..., description="源分支名称")
    target_message_id: int | None = Field(None, description="合并到的目标消息ID")
    merge_strategy: str = Field("append", description="合并策略: append/replace")


class BranchHistory(BaseModel):
    """分支历史记录."""

    message_id: int
    parent_message_id: int | None
    branch_name: str | None
    role: str
    content: str
    created_at: datetime
    is_branch_point: bool = False
    child_branches: list[str] = []
