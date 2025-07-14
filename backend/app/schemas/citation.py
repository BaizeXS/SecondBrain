"""Citation management schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CitationCreate(BaseModel):
    """创建引用请求."""

    # 必需字段
    citation_type: str = Field(..., description="引用类型: article/book/inproceedings/misc等")
    bibtex_key: str = Field(..., description="BibTeX键值")
    title: str = Field(..., description="标题")

    # 可选字段，使用 Field(default=None) 而不是显式类型注解
    document_id: int | None = Field(default=None, description="关联的文档ID")
    authors: list[str] = Field(default_factory=list, description="作者列表")
    year: int | None = Field(default=None, description="年份")
    journal: str | None = Field(default=None, description="期刊名称")
    volume: str | None = Field(default=None, description="卷号")
    number: str | None = Field(default=None, description="期号")
    pages: str | None = Field(default=None, description="页码")
    publisher: str | None = Field(default=None, description="出版社")
    doi: str | None = Field(default=None, description="DOI")
    url: str | None = Field(default=None, description="URL")
    abstract: str | None = Field(default=None, description="摘要")
    keywords: list[str] | None = Field(default=None, description="关键词")
    bibtex_raw: str | None = Field(default=None, description="原始BibTeX内容")
    meta_data: dict[str, Any] | None = Field(default=None, description="其他元数据")

    model_config = ConfigDict(
        # 允许额外字段被忽略
        extra='ignore',
        # 使用 enum 值
        use_enum_values=True,
    )


class CitationUpdate(BaseModel):
    """更新引用请求."""

    title: str | None = None
    authors: list[str] | None = None
    year: int | None = None
    journal: str | None = None
    volume: str | None = None
    number: str | None = None
    pages: str | None = None
    publisher: str | None = None
    doi: str | None = None
    url: str | None = None
    abstract: str | None = None
    keywords: list[str] | None = None
    bibtex_raw: str | None = None
    meta_data: dict[str, Any] | None = Field(None, description="元数据")


class CitationResponse(BaseModel):
    """引用响应."""

    id: int
    document_id: int | None
    citation_type: str
    bibtex_key: str
    title: str
    authors: list[str]
    year: int | None
    journal: str | None
    volume: str | None
    number: str | None
    pages: str | None
    publisher: str | None
    doi: str | None
    url: str | None
    abstract: str | None
    keywords: list[str] | None
    bibtex_raw: str | None
    meta_data: dict[str, Any] | None = Field(None, description="元数据")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CitationListResponse(BaseModel):
    """引用列表响应."""

    citations: list[CitationResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class BibTeXImportRequest(BaseModel):
    """BibTeX导入请求."""

    space_id: int = Field(..., description="目标空间ID")
    bibtex_content: str = Field(..., description="BibTeX内容")
    create_documents: bool = Field(False, description="是否为每个引用创建文档")
    tags: list[str] | None = Field(None, description="要添加的标签")


class BibTeXImportResponse(BaseModel):
    """BibTeX导入响应."""

    imported_count: int
    failed_count: int
    citations: list[CitationResponse]
    errors: list[dict[str, str]] = []


class BibTeXExportRequest(BaseModel):
    """BibTeX导出请求."""

    citation_ids: list[int] | None = Field(None, description="要导出的引用ID列表")
    space_id: int | None = Field(None, description="导出整个空间的引用")
    format: str = Field("bibtex", description="导出格式: bibtex/json/csv")


class CitationSearchRequest(BaseModel):
    """引用搜索请求."""

    query: str = Field(..., description="搜索关键词")
    space_id: int | None = Field(None, description="限定空间")
    citation_type: str | None = Field(None, description="引用类型")
    year_from: int | None = Field(None, description="起始年份")
    year_to: int | None = Field(None, description="结束年份")
    authors: list[str] | None = Field(None, description="作者筛选")


class CitationStyleFormat(BaseModel):
    """引用格式化样式."""

    style: str = Field("apa", description="引用样式: apa/mla/chicago/ieee")
    citation_ids: list[int] = Field(..., description="要格式化的引用ID列表")


class FormattedCitation(BaseModel):
    """格式化的引用."""

    citation_id: int
    formatted_text: str
    style: str
