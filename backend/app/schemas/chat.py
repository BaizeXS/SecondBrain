"""Chat schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Role(str, Enum):
    """消息角色."""

    system = "system"
    user = "user"
    assistant = "assistant"
    function = "function"
    tool = "tool"


class Message(BaseModel):
    """聊天消息."""

    role: Role
    content: str
    name: str | None = None
    function_call: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] | None = None


class ChatCompletionRequest(BaseModel):
    """聊天完成请求."""

    model: str = Field(..., description="模型名称")
    messages: list[Message] = Field(..., description="消息列表")
    mode: str | None = Field("chat", description="对话模式: chat, search, think")
    conversation_id: int | None = Field(None, description="对话ID")
    space_id: int | None = Field(None, description="空间ID")
    document_ids: list[int] | None = Field(None, description="关联的文档ID列表")
    temperature: float | None = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int | None = Field(None, ge=1, description="最大令牌数")
    stream: bool = Field(False, description="是否流式响应")
    top_p: float | None = Field(None, ge=0.0, le=1.0, description="Top-p采样")
    frequency_penalty: float | None = Field(0.0, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: float | None = Field(0.0, ge=-2.0, le=2.0, description="存在惩罚")
    stop: str | list[str] | None = Field(None, description="停止序列")
    n: int | None = Field(1, ge=1, le=10, description="生成数量")
    user: str | None = Field(None, description="用户标识")
    tools: list[dict[str, Any]] | None = Field(None, description="可用工具")
    tool_choice: str | dict[str, Any] | None = Field(None, description="工具选择")


class Choice(BaseModel):
    """聊天选择."""

    index: int
    message: Message
    finish_reason: str | None = None
    logprobs: dict[str, Any] | None = None


class Usage(BaseModel):
    """令牌使用情况."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """聊天完成响应."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[Choice]
    usage: Usage | None = None
    system_fingerprint: str | None = None


class ChatCompletionChunk(BaseModel):
    """流式聊天响应块."""

    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[dict[str, Any]]
    system_fingerprint: str | None = None


class ModelInfo(BaseModel):
    """模型信息."""

    id: str
    object: str = "model"
    created: int
    owned_by: str
    permission: list[dict[str, Any]] | None = None
    root: str | None = None
    parent: str | None = None


class ModelListResponse(BaseModel):
    """模型列表响应."""

    object: str = "list"
    data: list[ModelInfo]


class ChatStats(BaseModel):
    """聊天统计."""

    total_conversations: int = 0
    total_messages: int = 0
    total_tokens: int = 0
    avg_messages_per_conversation: float = 0.0
    avg_tokens_per_message: float = 0.0
    daily_usage: list[dict[str, Any]] = []
    model_usage: dict[str, int] = {}


class ChatHistoryExport(BaseModel):
    """聊天历史导出."""

    format: str = Field("json", description="导出格式")
    conversation_ids: list[int] | None = Field(None, description="对话ID列表")
    date_from: datetime | None = Field(None, description="开始日期")
    date_to: datetime | None = Field(None, description="结束日期")
    include_system_messages: bool = Field(True, description="包含系统消息")
    include_metadata: bool = Field(True, description="包含元数据")
