"""Space schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SpaceCreate(BaseModel):
    """创建知识空间模式."""

    name: str = Field(..., min_length=1, max_length=200, description="空间名称")
    description: str | None = Field(None, description="空间描述")
    color: str | None = Field(
        None, pattern=r"^#[0-9A-Fa-f]{6}$", description="主题颜色"
    )
    icon: str | None = Field(None, max_length=50, description="图标")
    is_public: bool = Field(default=False, description="是否公开")
    allow_collaboration: bool = Field(default=False, description="允许协作")
    tags: list[str] | None = Field(None, description="标签")
    meta_data: dict[str, Any] | None = Field(None, description="元数据")


class SpaceUpdate(BaseModel):
    """更新知识空间模式."""

    name: str | None = Field(
        None, min_length=1, max_length=200, description="空间名称"
    )
    description: str | None = Field(None, description="空间描述")
    color: str | None = Field(
        None, pattern=r"^#[0-9A-Fa-f]{6}$", description="主题颜色"
    )
    icon: str | None = Field(None, max_length=50, description="图标")
    is_public: bool | None = Field(None, description="是否公开")
    allow_collaboration: bool | None = Field(None, description="允许协作")
    tags: list[str] | None = Field(None, description="标签")
    meta_data: dict[str, Any] | None = Field(None, description="元数据")


class SpaceResponse(BaseModel):
    """知识空间响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    color: str | None = None
    icon: str | None = None
    is_public: bool
    allow_collaboration: bool
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = None
    document_count: int
    note_count: int
    total_size: int
    created_at: datetime
    updated_at: datetime | None = None


class SpaceDetail(SpaceResponse):
    """知识空间详细信息模式."""

    user_id: int
    # 可以添加更多详细信息，如最近的文档、统计信息等


class SpaceListResponse(BaseModel):
    """知识空间列表响应模式."""

    spaces: list[SpaceResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class SpaceCollaborationCreate(BaseModel):
    """创建空间协作模式."""

    user_id: int = Field(..., description="用户ID")
    role: str = Field(default="viewer", description="角色")
    can_edit: bool = Field(default=False, description="可编辑")
    can_delete: bool = Field(default=False, description="可删除")
    can_invite: bool = Field(default=False, description="可邀请")


class SpaceCollaborationUpdate(BaseModel):
    """更新空间协作模式."""

    role: str | None = Field(None, description="角色")
    can_edit: bool | None = Field(None, description="可编辑")
    can_delete: bool | None = Field(None, description="可删除")
    can_invite: bool | None = Field(None, description="可邀请")
    status: str | None = Field(None, description="状态")


class SpaceCollaborationResponse(BaseModel):
    """空间协作响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    space_id: int
    user_id: int
    role: str
    status: str
    can_edit: bool
    can_delete: bool
    can_invite: bool
    created_at: datetime


class SpaceInviteRequest(BaseModel):
    """空间邀请请求模式."""

    email: str = Field(..., description="邀请邮箱")
    role: str = Field(default="viewer", description="角色")
    message: str | None = Field(None, description="邀请消息")


class SpaceShareRequest(BaseModel):
    """空间分享请求模式."""

    is_public: bool = Field(..., description="是否公开")
    allow_collaboration: bool = Field(default=False, description="允许协作")
    share_link: str | None = Field(None, description="分享链接")


class SpaceShareResponse(BaseModel):
    """空间分享响应模式."""

    space_id: int
    share_link: str
    is_public: bool
    allow_collaboration: bool
    created_at: datetime
    expires_at: datetime | None = None


class SpaceStats(BaseModel):
    """空间统计模式."""

    total_documents: int = 0
    total_notes: int = 0
    total_conversations: int = 0
    total_size: int = 0
    file_type_distribution: dict[str, int] = {}
    recent_activity: list[dict[str, Any]] = []
    knowledge_graph_nodes: int = 0
    knowledge_graph_edges: int = 0


class SpaceSearch(BaseModel):
    """空间搜索请求模式."""

    query: str = Field(..., description="搜索查询")
    search_type: str = Field(default="semantic", description="搜索类型")
    limit: int = Field(default=20, ge=1, le=100, description="结果限制")
    include_documents: bool = Field(default=True, description="包含文档")
    include_notes: bool = Field(default=True, description="包含笔记")
    include_conversations: bool = Field(default=False, description="包含对话")


class SpaceSearchResult(BaseModel):
    """空间搜索结果模式."""

    id: int
    type: str  # document, note, conversation
    title: str
    content: str
    score: float
    highlights: list[str] = []
    meta_data: dict[str, Any] | None = Field(None, alias="metadata")
    created_at: datetime


class SpaceSearchResponse(BaseModel):
    """空间搜索响应模式."""

    query: str
    results: list[SpaceSearchResult]
    total_results: int
    search_time: float
    facets: dict[str, Any] = {}


class KnowledgeGraphNode(BaseModel):
    """知识图谱节点模式."""

    id: str
    label: str
    type: str
    properties: dict[str, Any] = {}
    size: float | None = None
    color: str | None = None


class KnowledgeGraphEdge(BaseModel):
    """知识图谱边模式."""

    source: str
    target: str
    label: str
    weight: float | None = None
    properties: dict[str, Any] = {}


class KnowledgeGraphResponse(BaseModel):
    """知识图谱响应模式."""

    nodes: list[KnowledgeGraphNode]
    edges: list[KnowledgeGraphEdge]
    metadata: dict[str, Any] = {}


class SpaceExport(BaseModel):
    """空间导出模式."""

    format: str = Field(default="zip", description="导出格式")
    include_documents: bool = Field(default=True, description="包含文档")
    include_notes: bool = Field(default=True, description="包含笔记")
    include_conversations: bool = Field(default=False, description="包含对话")
    include_metadata: bool = Field(default=True, description="包含元数据")


class SpaceImport(BaseModel):
    """空间导入模式."""

    source_type: str = Field(..., description="源类型")
    data: dict[str, Any] = Field(..., description="导入数据")
    merge_mode: str = Field(default="append", description="合并模式")
    preserve_structure: bool = Field(default=True, description="保持结构")


class SpaceTemplate(BaseModel):
    """空间模板模式."""

    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    category: str = Field(..., description="模板分类")
    structure: dict[str, Any] = Field(..., description="空间结构")
    default_settings: dict[str, Any] = Field(
        default_factory=dict, description="默认设置"
    )


class SpaceActivity(BaseModel):
    """空间活动模式."""

    id: int
    space_id: int
    user_id: int
    action: str
    resource_type: str
    resource_id: int | None = None
    details: dict[str, Any] | None = None
    created_at: datetime
