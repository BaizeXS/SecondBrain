"""Annotation schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AnnotationBase(BaseModel):
    """标注基础模型."""

    type: str = Field(..., description="标注类型: highlight/underline/note/bookmark")
    content: str | None = Field(default=None, description="标注内容/批注")
    selected_text: str | None = Field(default=None, description="选中的文本")
    page_number: int | None = Field(default=None, ge=1, description="页码")
    position_data: dict[str, Any] | None = Field(default=None, description="位置数据")
    color: str | None = Field(default=None, description="颜色（十六进制）")


class AnnotationCreate(AnnotationBase):
    """创建标注模型."""

    document_id: int = Field(..., description="文档ID")


class AnnotationUpdate(BaseModel):
    """更新标注模型."""

    content: str | None = Field(None, description="标注内容")
    color: str | None = Field(None, description="颜色")
    position_data: dict[str, Any] | None = Field(None, description="位置数据")


class AnnotationResponse(AnnotationBase):
    """标注响应模型."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime | None = None


class AnnotationDetail(AnnotationResponse):
    """标注详情模型."""

    document_title: str | None = None
    document_filename: str | None = None
    username: str | None = None


class AnnotationListResponse(BaseModel):
    """标注列表响应模型."""

    annotations: list[AnnotationResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class AnnotationBatchCreate(BaseModel):
    """批量创建标注模型."""

    document_id: int = Field(..., description="文档ID")
    annotations: list[AnnotationBase] = Field(..., min_length=1, description="标注列表")


class AnnotationExportRequest(BaseModel):
    """标注导出请求模型."""

    document_ids: list[int] = Field(..., min_length=1, description="文档ID列表")
    format: str = Field(default="json", description="导出格式: json/csv/pdf")
    include_content: bool = Field(default=True, description="是否包含标注内容")
    group_by_page: bool = Field(default=False, description="是否按页分组")


class AnnotationStatistics(BaseModel):
    """标注统计模型."""

    total_annotations: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)
    by_document: dict[str, int] = Field(default_factory=dict)
    by_color: dict[str, int] = Field(default_factory=dict)
    recent_activity: list[dict[str, Any]] = Field(default_factory=list)


class PDFHighlight(BaseModel):
    """PDF高亮标注模型."""

    page: int = Field(..., ge=1, description="页码")
    text: str = Field(..., description="高亮文本")
    rects: list[list[float]] = Field(..., description="矩形坐标列表")
    color: str = Field(default="#FFFF00", description="高亮颜色")
    note: str | None = Field(None, description="批注内容")


class PDFAnnotationData(BaseModel):
    """PDF标注数据模型."""

    highlights: list[PDFHighlight] = Field(default_factory=list)
    underlines: list[PDFHighlight] = Field(default_factory=list)
    notes: list[dict[str, Any]] = Field(default_factory=list)
    bookmarks: list[dict[str, Any]] = Field(default_factory=list)
