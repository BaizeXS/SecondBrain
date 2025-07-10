"""Document schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    """创建文档模式."""

    filename: str = Field(..., description="文件名")
    content_type: str = Field(..., description="内容类型")
    size: int = Field(..., description="文件大小")
    space_id: int = Field(..., description="知识空间ID")
    description: Optional[str] = Field(None, description="文档描述")
    tags: Optional[List[str]] = Field(None, description="标签")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="元数据")


class DocumentUpdate(BaseModel):
    """更新文档模式."""

    filename: Optional[str] = Field(None, description="文件名")
    description: Optional[str] = Field(None, description="文档描述")
    tags: Optional[List[str]] = Field(None, description="标签")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="元数据")


class DocumentResponse(BaseModel):
    """文档响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str
    file_size: int
    space_id: int
    user_id: int
    file_url: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    meta_data: Optional[Dict[str, Any]] = None
    processing_status: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class DocumentDetail(DocumentResponse):
    """文档详细信息模式."""

    content: Optional[str] = None
    preview_url: Optional[str] = None
    annotations: Optional[List[Dict[str, Any]]] = None
    translations: Optional[List[Dict[str, Any]]] = None


class DocumentListResponse(BaseModel):
    """文档列表响应模式."""

    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class DocumentUploadRequest(BaseModel):
    """文档上传请求模式."""

    space_id: int = Field(..., description="知识空间ID")
    description: Optional[str] = Field(None, description="文档描述")
    tags: Optional[List[str]] = Field(None, description="标签")
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
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None


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
    color: Optional[str] = Field(None, description="颜色")


class AnnotationUpdate(BaseModel):
    """更新批注模式."""

    content: Optional[str] = Field(None, description="批注内容")
    color: Optional[str] = Field(None, description="颜色")


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
    color: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class DocumentTranslationRequest(BaseModel):
    """文档翻译请求模式."""

    target_language: str = Field(..., description="目标语言")
    source_language: Optional[str] = Field(None, description="源语言")
    translate_images: bool = Field(default=False, description="翻译图片")
    preserve_formatting: bool = Field(default=True, description="保持格式")
    translation_provider: Optional[str] = Field(None, description="翻译提供商")


class DocumentTranslationResponse(BaseModel):
    """文档翻译响应模式."""

    id: int
    original_document_id: int
    target_language: str
    source_language: str
    status: str
    progress: int
    translated_document_id: Optional[int] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    created_at: datetime


class DocumentSearch(BaseModel):
    """文档搜索请求模式."""

    query: str = Field(..., description="搜索查询")
    space_id: Optional[int] = Field(None, description="知识空间ID")
    document_types: Optional[List[str]] = Field(None, description="文档类型")
    tags: Optional[List[str]] = Field(None, description="标签")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")
    search_type: str = Field(default="semantic", description="搜索类型")
    limit: int = Field(default=20, ge=1, le=100, description="结果限制")


class DocumentSearchResult(BaseModel):
    """文档搜索结果模式."""

    document: DocumentResponse
    score: float
    highlights: List[str] = []
    matched_content: Optional[str] = None
    page_number: Optional[int] = None


class DocumentSearchResponse(BaseModel):
    """文档搜索响应模式."""

    query: str
    results: List[DocumentSearchResult]
    total_results: int
    search_time: float
    facets: Dict[str, Any] = {}


class DocumentStats(BaseModel):
    """文档统计模式."""

    total_documents: int = 0
    total_size: int = 0
    file_type_distribution: Dict[str, int] = {}
    processing_status_distribution: Dict[str, int] = {}
    recent_uploads: List[DocumentResponse] = []
    storage_usage: Dict[str, Any] = {}


class DocumentExport(BaseModel):
    """文档导出模式."""

    format: str = Field(default="pdf", description="导出格式")
    include_annotations: bool = Field(default=True, description="包含批注")
    include_metadata: bool = Field(default=True, description="包含元数据")
    page_range: Optional[str] = Field(None, description="页面范围")


class DocumentShare(BaseModel):
    """文档分享模式."""

    permission: str = Field(default="view", description="权限")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    password: Optional[str] = Field(None, description="访问密码")
    allow_download: bool = Field(default=False, description="允许下载")


class DocumentShareResponse(BaseModel):
    """文档分享响应模式."""

    document_id: int
    share_link: str
    permission: str
    expires_at: Optional[datetime] = None
    password_protected: bool = False
    allow_download: bool = False
    created_at: datetime


class DocumentPreviewRequest(BaseModel):
    """文档预览请求模式."""

    page: int = Field(default=1, ge=1, description="页码")
    width: Optional[int] = Field(None, ge=100, le=2000, description="宽度")
    height: Optional[int] = Field(None, ge=100, le=2000, description="高度")
    quality: str = Field(default="medium", description="质量")


class DocumentContent(BaseModel):
    """文档内容模式."""

    text: Optional[str] = None
    images: Optional[List[Dict[str, Any]]] = None
    tables: Optional[List[Dict[str, Any]]] = None
    meta_data: Optional[Dict[str, Any]] = None
    structure: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    """搜索请求模式."""
    
    query: str = Field(..., description="搜索查询")
    space_id: Optional[int] = Field(None, description="限定空间ID")
    limit: int = Field(default=10, ge=1, le=50, description="结果数量")
    search_type: str = Field(default="keyword", description="搜索类型")


class SearchResult(BaseModel):
    """搜索结果模式."""
    
    document_id: int
    title: str
    snippet: str
    score: float
    highlight: Dict[str, List[str]] = {}


class SearchResponse(BaseModel):
    """搜索响应模式."""
    
    results: List[SearchResult]
    total: int
    query: str
    search_time: Optional[float] = None
