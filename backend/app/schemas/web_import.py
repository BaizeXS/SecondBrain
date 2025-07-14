"""Web import schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class URLImportRequest(BaseModel):
    """URL导入请求."""

    url: HttpUrl = Field(..., description="要导入的网页URL")
    space_id: int = Field(..., description="目标空间ID")
    title: str | None = Field(None, description="自定义标题")
    tags: list[str] | None = Field(None, description="标签列表")
    save_snapshot: bool = Field(True, description="是否保存网页快照")
    extract_links: bool = Field(False, description="是否提取页面中的链接")


class BatchURLImportRequest(BaseModel):
    """批量URL导入请求."""

    urls: list[HttpUrl] = Field(..., description="要导入的网页URL列表", max_length=30)
    space_id: int = Field(..., description="目标空间ID")
    tags: list[str] | None = Field(None, description="标签列表")
    save_snapshot: bool = Field(True, description="是否保存网页快照")


class WebPageMetadata(BaseModel):
    """网页元数据."""

    url: str
    domain: str
    title: str | None = None
    description: str | None = None
    keywords: str | None = None
    author: str | None = None
    published_time: str | None = None
    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None
    fetched_at: datetime


class URLImportResponse(BaseModel):
    """URL导入响应."""

    document_id: int
    url: str
    title: str
    status: str = Field(..., description="导入状态: success/error")
    error: str | None = None
    metadata: WebPageMetadata | None = None
    extracted_links: list[str] | None = None
    created_at: datetime


class WebSnapshotResponse(BaseModel):
    """网页快照响应."""

    document_id: int
    url: str
    title: str
    snapshot_html: str | None = None
    snapshot_markdown: str | None = None
    metadata: dict[str, Any]
    created_at: datetime


class URLAnalysisRequest(BaseModel):
    """URL分析请求."""

    url: HttpUrl = Field(..., description="要分析的URL")


class URLAnalysisResponse(BaseModel):
    """URL分析响应."""

    url: str
    title: str
    description: str | None = None
    content_preview: str = Field(..., description="内容预览（前500字符）")
    metadata: WebPageMetadata
    word_count: int
    links_count: int
    images_count: int
    can_import: bool
    suggested_tags: list[str] = []
