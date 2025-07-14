"""Note schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NoteBase(BaseModel):
    """笔记基础模型."""

    title: str = Field(..., min_length=1, max_length=500, description="笔记标题")
    content: str = Field(..., description="笔记内容")
    content_type: str = Field(default="markdown", description="内容类型: markdown/html/plain")
    tags: list[str] | None = Field(None, description="标签列表")
    linked_documents: list[int] | None = Field(None, description="关联的文档ID列表")
    linked_notes: list[int] | None = Field(None, description="关联的笔记ID列表")
    meta_data: dict[str, Any] | None = Field(None, description="元数据")


class NoteCreate(NoteBase):
    """创建笔记模型."""

    space_id: int = Field(..., description="所属Space ID")
    note_type: str = Field(default="manual", description="笔记类型: manual/ai/linked")
    source_type: str | None = Field(default=None, description="来源类型: user/ai/research/summary")
    source_id: str | None = Field(default=None, description="来源ID（如研究ID、对话ID等）")


class NoteUpdate(BaseModel):
    """更新笔记模型."""

    title: str | None = Field(default=None, min_length=1, max_length=500, description="笔记标题")
    content: str | None = Field(default=None, description="笔记内容")
    content_type: str | None = Field(default=None, description="内容类型")
    tags: list[str] | None = Field(default=None, description="标签列表")
    linked_documents: list[int] | None = Field(default=None, description="关联的文档ID列表")
    linked_notes: list[int] | None = Field(default=None, description="关联的笔记ID列表")
    meta_data: dict[str, Any] | None = Field(default=None, description="元数据")


class NoteResponse(NoteBase):
    """笔记响应模型."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    space_id: int
    user_id: int
    note_type: str = "manual"
    source_type: str | None = None
    source_id: str | None = None
    ai_model: str | None = None
    version: int = 1
    is_draft: bool = False
    created_at: datetime
    updated_at: datetime | None = None


class NoteDetail(NoteResponse):
    """笔记详情模型."""

    space_name: str | None = None
    username: str | None = None
    linked_document_titles: list[str] | None = None
    linked_note_titles: list[str] | None = None
    version_count: int = 0
    last_edited_by: str | None = None


class NoteListResponse(BaseModel):
    """笔记列表响应模型."""

    notes: list[NoteResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class NoteAIGenerateRequest(BaseModel):
    """AI生成笔记请求模型."""

    space_id: int = Field(..., description="所属Space ID")
    prompt: str = Field(..., description="生成提示")
    document_ids: list[int] | None = Field(None, description="参考文档ID列表")
    note_ids: list[int] | None = Field(None, description="参考笔记ID列表")
    generation_type: str = Field(
        default="summary",
        description="生成类型: summary/outline/keypoints/mindmap/question"
    )
    model: str | None = Field(None, description="指定使用的AI模型")
    temperature: float = Field(default=0.7, ge=0, le=2, description="生成温度")


class NoteAISummaryRequest(BaseModel):
    """AI总结请求模型."""

    document_ids: list[int] = Field(..., min_length=1, description="要总结的文档ID列表")
    space_id: int = Field(..., description="所属Space ID")
    summary_type: str = Field(
        default="comprehensive",
        description="总结类型: comprehensive/brief/technical/beginner"
    )
    max_length: int = Field(default=1000, ge=100, le=5000, description="最大总结长度")
    language: str = Field(default="auto", description="输出语言: auto/zh/en")


class NoteExportRequest(BaseModel):
    """笔记导出请求模型."""

    note_ids: list[int] = Field(..., min_length=1, description="要导出的笔记ID列表")
    format: str = Field(default="markdown", description="导出格式: markdown/pdf/html/docx")
    include_metadata: bool = Field(default=False, description="是否包含元数据")
    include_linked_content: bool = Field(default=False, description="是否包含关联内容")


class NoteSearchRequest(BaseModel):
    """笔记搜索请求模型."""

    query: str = Field(..., min_length=1, description="搜索查询")
    space_ids: list[int] | None = Field(None, description="限定Space ID列表")
    tags: list[str] | None = Field(None, description="标签过滤")
    content_types: list[str] | None = Field(None, description="内容类型过滤")
    date_from: datetime | None = Field(None, description="开始日期")
    date_to: datetime | None = Field(None, description="结束日期")
    sort_by: str = Field(default="relevance", description="排序方式: relevance/created_at/updated_at")
    limit: int = Field(default=20, ge=1, le=100, description="结果数量限制")


class NoteVersion(BaseModel):
    """笔记版本模型."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    note_id: int
    version_number: int
    content: str
    changed_by: int
    changed_by_username: str | None = None
    change_summary: str | None = None
    created_at: datetime


class NoteTemplate(BaseModel):
    """笔记模板模型."""

    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    content: str = Field(..., description="模板内容")
    category: str = Field(..., description="模板分类")
    variables: list[str] | None = Field(None, description="模板变量")
    tags: list[str] | None = Field(None, description="标签")


class NoteBatchOperation(BaseModel):
    """批量操作模型."""

    note_ids: list[int] = Field(..., min_length=1, description="笔记ID列表")
    operation: str = Field(..., description="操作类型: delete/move/tag/export")
    target_space_id: int | None = Field(None, description="目标Space ID（移动操作）")
    tags_to_add: list[str] | None = Field(None, description="要添加的标签")
    tags_to_remove: list[str] | None = Field(None, description="要移除的标签")
