"""Conversation and message schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from enum import Enum

class ChatMode(str, Enum):
    """对话模式枚举."""
    CHAT = "chat"
    SEARCH = "search"
    THINK = "think"
    AUTO = "auto"


class MessageCreate(BaseModel):
    """创建消息模式."""

    content: str = Field(..., description="消息内容")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="附件")


class MessageResponse(BaseModel):
    """消息响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    model: Optional[str] = None
    provider: Optional[str] = None
    token_count: Optional[int] = None
    processing_time: Optional[float] = None
    meta_data: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    created_at: datetime


class ConversationCreate(BaseModel):
    """创建对话模式."""

    title: str = Field(..., max_length=500, description="对话标题")
    mode: ChatMode = Field(default=ChatMode.CHAT, description="对话模式")
    space_id: Optional[int] = Field(None, description="关联的知识空间ID")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    model: Optional[str] = Field(None, description="指定AI模型")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(None, ge=1, description="最大令牌数")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ConversationUpdate(BaseModel):
    """更新对话模式."""

    title: Optional[str] = Field(None, max_length=500, description="对话标题")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(None, ge=1, description="最大令牌数")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ConversationResponse(BaseModel):
    """对话响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    mode: str
    model: Optional[str] = None
    space_id: Optional[int] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    meta_data: Optional[Dict[str, Any]] = None
    message_count: int
    total_tokens: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class ConversationDetail(ConversationResponse):
    """对话详细信息模式."""

    messages: List[MessageResponse] = []


class ChatRequest(BaseModel):
    """聊天请求模式."""

    message: str = Field(..., description="用户消息")
    stream: bool = Field(default=True, description="是否流式响应")
    model: Optional[str] = Field(None, description="指定AI模型")
    provider: Optional[str] = Field(None, description="指定AI提供商")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(None, ge=1, description="最大令牌数")
    context_files: Optional[List[int]] = Field(None, description="上下文文档ID列表")
    search_scope: Optional[str] = Field("web", description="搜索范围")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="附件")


class ChatResponse(BaseModel):
    """聊天响应模式."""

    message_id: int
    content: str
    model: str
    provider: str
    token_count: Optional[int] = None
    processing_time: float
    sources: Optional[List[Dict[str, Any]]] = None
    meta_data: Optional[Dict[str, Any]] = None


class StreamChatChunk(BaseModel):
    """流式聊天块模式."""

    content: str
    finished: bool = False
    message_id: Optional[int] = None
    meta_data: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    """搜索请求模式."""

    query: str = Field(..., description="搜索查询")
    search_scope: str = Field(default="web", description="搜索范围")
    max_results: int = Field(default=10, ge=1, le=50, description="最大结果数")
    include_summary: bool = Field(default=True, description="包含AI总结")


class SearchResult(BaseModel):
    """搜索结果模式."""

    title: str
    url: str
    snippet: str
    content: Optional[str] = None
    score: Optional[float] = None
    source: str
    published_date: Optional[datetime] = None


class SearchResponse(BaseModel):
    """搜索响应模式."""

    query: str
    results: List[SearchResult]
    summary: Optional[str] = None
    total_results: int
    search_time: float
    sources: List[str]


class ThinkRequest(BaseModel):
    """推理请求模式."""

    question: str = Field(..., description="需要深度思考的问题")
    context: Optional[str] = Field(None, description="上下文信息")
    model: Optional[str] = Field(None, description="指定推理模型")
    max_tokens: Optional[int] = Field(None, ge=1, description="最大令牌数")
    show_reasoning: bool = Field(default=True, description="显示推理过程")


class ThinkResponse(BaseModel):
    """推理响应模式."""

    question: str
    answer: str
    reasoning: Optional[str] = None
    model: str
    provider: str
    token_count: Optional[int] = None
    processing_time: float
    confidence: Optional[float] = None


class ConversationListResponse(BaseModel):
    """对话列表响应模式."""

    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class ConversationWithMessages(BaseModel):
    """包含消息的对话响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    mode: ChatMode
    model: Optional[str] = None
    space_id: Optional[int] = None
    prompt_template: Optional[str] = None
    is_pinned: bool = False
    is_archived: bool = False
    message_count: int = 0
    token_count: int = 0
    tags: Optional[List[str]] = None
    meta_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[MessageResponse] = []


class ConversationStats(BaseModel):
    """对话统计模式."""

    total_conversations: int
    total_messages: int
    total_tokens: int
    avg_messages_per_conversation: float
    most_used_model: Optional[str] = None
    mode_distribution: Dict[str, int] = {}
    daily_usage: List[Dict[str, Any]] = []


class ConversationExport(BaseModel):
    """对话导出模式."""

    format: str = Field(default="json", description="导出格式")
    include_metadata: bool = Field(default=True, description="包含元数据")
    include_attachments: bool = Field(default=False, description="包含附件")


class ConversationImport(BaseModel):
    """对话导入模式."""

    data: Dict[str, Any] = Field(..., description="导入数据")
    merge_mode: str = Field(default="append", description="合并模式")
    validate_format: bool = Field(default=True, description="验证格式")
