"""Note version history schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NoteVersionCreate(BaseModel):
    """创建笔记版本（内部使用）."""

    note_id: int
    version_number: int
    title: str
    content: str
    content_html: str | None = None
    change_summary: str | None = None
    change_type: str = "edit"  # edit, ai_generate, restore
    ai_model: str | None = None
    ai_prompt: str | None = None
    tags: list[str] | None = None
    word_count: int = 0
    meta_data: dict[str, Any] | None = Field(None, description="元数据")


class NoteVersionResponse(BaseModel):
    """笔记版本响应."""

    id: int
    note_id: int
    user_id: int
    version_number: int
    title: str
    content: str
    content_html: str | None
    change_summary: str | None
    change_type: str
    ai_model: str | None
    ai_prompt: str | None
    tags: list[str] | None
    word_count: int
    meta_data: dict[str, Any] | None = Field(None, description="元数据")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NoteVersionListResponse(BaseModel):
    """笔记版本列表响应."""

    versions: list[NoteVersionResponse]
    total: int
    current_version: int


class NoteVersionDiff(BaseModel):
    """版本差异对比."""

    version1: NoteVersionResponse
    version2: NoteVersionResponse
    title_changed: bool
    content_diff: list[dict[str, Any]]  # 差异详情
    tags_added: list[str]
    tags_removed: list[str]
    word_count_change: int


class NoteRestoreRequest(BaseModel):
    """恢复版本请求."""

    version_id: int = Field(..., description="要恢复的版本ID")
    create_backup: bool = Field(True, description="是否创建当前版本的备份")


class NoteVersionCompareRequest(BaseModel):
    """版本对比请求."""

    version1_id: int = Field(..., description="版本1的ID")
    version2_id: int = Field(..., description="版本2的ID")
