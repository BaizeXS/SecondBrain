"""Document schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    """创建文档模式."""

    filename: str = Field(..., description="文件名")
    content_type: str = Field(..., description="内容类型")
    size: int = Field(..., description="文件大小")
    space_id: int = Field(..., description="知识空间ID")
    description: str | None = Field(default=None, description="文档描述")
    tags: list[str] | None = Field(default=None, description="标签")
    meta_data: dict[str, Any] | None = Field(default=None, description="元数据")


class DocumentUpdate(BaseModel):
    """更新文档模式."""

    filename: str | None = Field(default=None, description="文件名")
    description: str | None = Field(default=None, description="文档描述")
    tags: list[str] | None = Field(default=None, description="标签")
    meta_data: dict[str, Any] | None = Field(default=None, description="元数据")


class DocumentResponse(BaseModel):
    """文档响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    original_filename: str | None = None
    content_type: str
    file_size: int
    space_id: int
    user_id: int
    file_url: str | None = None
    title: str | None = None
    summary: str | None = None
    language: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = Field(None, description="元数据")
    processing_status: str | None = None
    extraction_status: str = "pending"
    embedding_status: str = "pending"
    parent_id: int | None = None
    created_at: datetime
    updated_at: datetime | None = None


class DocumentDetail(DocumentResponse):
    """文档详细信息模式."""

    content: str | None = None
    preview_url: str | None = None
    annotations: list[dict[str, Any]] | None = None
    translations: list[dict[str, Any]] | None = None


class DocumentListResponse(BaseModel):
    """文档列表响应模式."""

    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class DocumentUploadRequest(BaseModel):
    """文档上传请求模式."""

    space_id: int = Field(..., description="知识空间ID")
    description: str | None = Field(None, description="文档描述")
    tags: list[str] | None = Field(None, description="标签")
    auto_process: bool = Field(default=True, description="自动处理")
    extract_images: bool = Field(default=False, description="提取图片")
    ocr_enabled: bool = Field(default=False, description="启用OCR")


class DocumentProcessRequest(BaseModel):
    """文档处理请求模式."""

    extract_text: bool = Field(default=True, description="提取文本")
    extract_images: bool = Field(default=False, description="提取图片")
    extract_tables: bool = Field(default=False, description="提取表格")
    ocr_enabled: bool = Field(default=False, description="启用OCR")
    generate_summary: bool = Field(default=False, description="生成摘要")
    create_embeddings: bool = Field(default=True, description="创建嵌入")


class DocumentProcessResponse(BaseModel):
    """文档处理响应模式."""

    document_id: int
    status: str
    progress: int
    results: dict[str, Any] | None = None
    error_message: str | None = None
    processing_time: float | None = None


class AnnotationCreate(BaseModel):
    """创建批注模式."""

    document_id: int = Field(..., description="文档ID")
    page_number: int = Field(..., description="页码")
    x: float = Field(..., description="X坐标")
    y: float = Field(..., description="Y坐标")
    width: float = Field(..., description="宽度")
    height: float = Field(..., description="高度")
    content: str = Field(..., description="批注内容")
    annotation_type: str = Field(default="highlight", description="批注类型")
    color: str | None = Field(None, description="颜色")


class AnnotationUpdate(BaseModel):
    """更新批注模式."""

    content: str | None = Field(None, description="批注内容")
    color: str | None = Field(None, description="颜色")


class AnnotationResponse(BaseModel):
    """批注响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    user_id: int
    page_number: int
    x: float
    y: float
    width: float
    height: float
    content: str
    annotation_type: str
    color: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class DocumentTranslationRequest(BaseModel):
    """文档翻译请求模式."""

    target_language: str = Field(..., description="目标语言")
    source_language: str | None = Field(None, description="源语言")
    translate_images: bool = Field(default=False, description="翻译图片")
    preserve_formatting: bool = Field(default=True, description="保持格式")
    translation_provider: str | None = Field(None, description="翻译提供商")


class DocumentTranslationResponse(BaseModel):
    """文档翻译响应模式."""

    id: int
    original_document_id: int
    target_language: str
    source_language: str
    status: str
    progress: int
    translated_document_id: int | None = None
    error_message: str | None = None
    processing_time: float | None = None
    created_at: datetime


class DocumentSearch(BaseModel):
    """文档搜索请求模式."""

    query: str = Field(..., description="搜索查询")
    space_id: int | None = Field(None, description="知识空间ID")
    document_types: list[str] | None = Field(None, description="文档类型")
    tags: list[str] | None = Field(None, description="标签")
    date_from: datetime | None = Field(None, description="开始日期")
    date_to: datetime | None = Field(None, description="结束日期")
    search_type: str = Field(default="semantic", description="搜索类型")
    limit: int = Field(default=20, ge=1, le=100, description="结果限制")


class DocumentSearchResult(BaseModel):
    """文档搜索结果模式."""

    document: DocumentResponse
    score: float
    highlights: list[str] = []
    matched_content: str | None = None
    page_number: int | None = None


class DocumentSearchResponse(BaseModel):
    """文档搜索响应模式."""

    query: str
    results: list[DocumentSearchResult]
    total_results: int
    search_time: float
    facets: dict[str, Any] = {}


class DocumentStats(BaseModel):
    """文档统计模式."""

    total_documents: int = 0
    total_size: int = 0
    file_type_distribution: dict[str, int] = {}
    processing_status_distribution: dict[str, int] = {}
    recent_uploads: list[DocumentResponse] = []
    storage_usage: dict[str, Any] = {}


class DocumentExport(BaseModel):
    """文档导出模式."""

    format: str = Field(default="pdf", description="导出格式")
    include_annotations: bool = Field(default=True, description="包含批注")
    include_metadata: bool = Field(default=True, description="包含元数据")
    page_range: str | None = Field(None, description="页面范围")


class DocumentShare(BaseModel):
    """文档分享模式."""

    permission: str = Field(default="view", description="权限")
    expires_at: datetime | None = Field(None, description="过期时间")
    password: str | None = Field(None, description="访问密码")
    allow_download: bool = Field(default=False, description="允许下载")


class DocumentShareResponse(BaseModel):
    """文档分享响应模式."""

    document_id: int
    share_link: str
    permission: str
    expires_at: datetime | None = None
    password_protected: bool = False
    allow_download: bool = False
    created_at: datetime


class DocumentPreviewRequest(BaseModel):
    """文档预览请求模式."""

    page: int = Field(default=1, ge=1, description="页码")
    width: int | None = Field(None, ge=100, le=2000, description="宽度")
    height: int | None = Field(None, ge=100, le=2000, description="高度")
    quality: str = Field(default="medium", description="质量")


class DocumentContent(BaseModel):
    """文档内容模式."""

    text: str | None = None
    images: list[dict[str, Any]] | None = None
    tables: list[dict[str, Any]] | None = None
    meta_data: dict[str, Any] | None = Field(None, description="元数据")
    structure: dict[str, Any] | None = None


class SearchRequest(BaseModel):
    """搜索请求模式."""

    query: str = Field(..., description="搜索查询")
    space_id: int | None = Field(None, description="限定空间ID")
    limit: int = Field(default=10, ge=1, le=50, description="结果数量")
    search_type: str = Field(default="keyword", description="搜索类型")


class SearchResult(BaseModel):
    """搜索结果模式."""

    document_id: int
    title: str
    snippet: str
    score: float
    highlight: dict[str, list[str]] = {}


class SearchResponse(BaseModel):
    """搜索响应模式."""

    results: list[SearchResult]
    total: int
    query: str
    search_time: float | None = None
