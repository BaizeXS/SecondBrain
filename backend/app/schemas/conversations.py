"""Conversation and message schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatMode(str, Enum):
    """对话模式枚举."""
    CHAT = "chat"
    SEARCH = "search"
    THINK = "think"
    AUTO = "auto"


class MessageCreate(BaseModel):
    """创建消息模式."""

    conversation_id: int = Field(..., description="对话ID")
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")
    model: str | None = Field(None, description="AI模型名称")
    provider: str | None = Field(None, description="AI提供商")
    meta_data: dict[str, Any] | None = Field(None, description="元数据")
    attachments: list[dict[str, Any]] | None = Field(None, description="附件")


class MessageCreateSimple(BaseModel):
    """简化的创建消息模式 - 用于API端点."""

    content: str = Field(..., description="消息内容")
    attachments: list[dict[str, Any]] | None = Field(None, description="附件")


class MessageUpdate(BaseModel):
    """更新消息模式."""

    content: str | None = Field(None, description="消息内容")
    attachments: list[dict[str, Any]] | None = Field(None, description="附件")
    meta_data: dict[str, Any] | None = Field(None, description="元数据")


class MessageResponse(BaseModel):
    """消息响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    model: str | None = None
    provider: str | None = None
    token_count: int | None = None
    processing_time: float | None = None
    meta_data: dict[str, Any] | None = Field(None, description="元数据")
    attachments: list[dict[str, Any]] | None = None
    created_at: datetime


class ConversationCreate(BaseModel):
    """创建对话模式."""

    title: str = Field(..., max_length=500, description="对话标题")
    mode: ChatMode = Field(default=ChatMode.CHAT, description="对话模式")
    space_id: int | None = Field(None, description="关联的知识空间ID")
    system_prompt: str | None = Field(None, description="系统提示词")
    model: str | None = Field(None, description="指定AI模型")
    temperature: float | None = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int | None = Field(None, ge=1, description="最大令牌数")
    meta_data: dict[str, Any] | None = Field(None, description="元数据")


class ConversationUpdate(BaseModel):
    """更新对话模式."""

    title: str | None = Field(None, max_length=500, description="对话标题")
    system_prompt: str | None = Field(None, description="系统提示词")
    temperature: float | None = Field(None, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int | None = Field(None, ge=1, description="最大令牌数")
    meta_data: dict[str, Any] | None = Field(None, description="元数据")


class ConversationResponse(BaseModel):
    """对话响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    mode: str
    model: str | None = None
    space_id: int | None = None
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    meta_data: dict[str, Any] | None = Field(None, description="元数据")
    message_count: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime | None = None


class ConversationDetail(ConversationResponse):
    """对话详细信息模式."""

    messages: list[MessageResponse] = []


class ChatRequest(BaseModel):
    """聊天请求模式."""

    message: str = Field(..., description="用户消息")
    stream: bool = Field(default=True, description="是否流式响应")
    model: str | None = Field(None, description="指定AI模型")
    provider: str | None = Field(None, description="指定AI提供商")
    temperature: float | None = Field(None, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int | None = Field(None, ge=1, description="最大令牌数")
    context_files: list[int] | None = Field(None, description="上下文文档ID列表")
    search_scope: str | None = Field("web", description="搜索范围")
    attachments: list[dict[str, Any]] | None = Field(None, description="附件")


class ChatResponse(BaseModel):
    """聊天响应模式."""

    message_id: int
    content: str
    model: str
    provider: str
    token_count: int | None = None
    processing_time: float
    sources: list[dict[str, Any]] | None = None
    meta_data: dict[str, Any] | None = Field(None, description="元数据")


class StreamChatChunk(BaseModel):
    """流式聊天块模式."""

    content: str
    finished: bool = False
    message_id: int | None = None
    meta_data: dict[str, Any] | None = Field(None, description="元数据")


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
    content: str | None = None
    score: float | None = None
    source: str
    published_date: datetime | None = None


class SearchResponse(BaseModel):
    """搜索响应模式."""

    query: str
    results: list[SearchResult]
    summary: str | None = None
    total_results: int
    search_time: float
    sources: list[str]


class ThinkRequest(BaseModel):
    """推理请求模式."""

    question: str = Field(..., description="需要深度思考的问题")
    context: str | None = Field(None, description="上下文信息")
    model: str | None = Field(None, description="指定推理模型")
    max_tokens: int | None = Field(None, ge=1, description="最大令牌数")
    show_reasoning: bool = Field(default=True, description="显示推理过程")


class ThinkResponse(BaseModel):
    """推理响应模式."""

    question: str
    answer: str
    reasoning: str | None = None
    model: str
    provider: str
    token_count: int | None = None
    processing_time: float
    confidence: float | None = None


class ConversationListResponse(BaseModel):
    """对话列表响应模式."""

    conversations: list[ConversationResponse]
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
    model: str | None = None
    space_id: int | None = None
    prompt_template: str | None = None
    is_pinned: bool = False
    is_archived: bool = False
    message_count: int = 0
    token_count: int = 0
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = Field(None, description="元数据")
    created_at: datetime
    updated_at: datetime | None = None
    messages: list[MessageResponse] = []


class ConversationStats(BaseModel):
    """对话统计模式."""

    total_conversations: int
    total_messages: int
    total_tokens: int
    avg_messages_per_conversation: float
    most_used_model: str | None = None
    mode_distribution: dict[str, int] = {}
    daily_usage: list[dict[str, Any]] = []


class ConversationExport(BaseModel):
    """对话导出模式."""

    format: str = Field(default="json", description="导出格式")
    include_metadata: bool = Field(default=True, description="包含元数据")
    include_attachments: bool = Field(default=False, description="包含附件")


class ConversationImport(BaseModel):
    """对话导入模式."""

    data: dict[str, Any] = Field(..., description="导入数据")
    merge_mode: str = Field(default="append", description="合并模式")
    validate_format: bool = Field(default=True, description="验证格式")
