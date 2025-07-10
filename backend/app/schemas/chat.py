"""Chat schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

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
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ChatCompletionRequest(BaseModel):
    """聊天完成请求."""
    
    model: str = Field(..., description="模型名称")
    messages: List[Message] = Field(..., description="消息列表")
    conversation_id: Optional[int] = Field(None, description="对话ID")
    space_id: Optional[int] = Field(None, description="空间ID")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(None, ge=1, description="最大令牌数")
    stream: bool = Field(False, description="是否流式响应")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top-p采样")
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="存在惩罚")
    stop: Optional[Union[str, List[str]]] = Field(None, description="停止序列")
    n: Optional[int] = Field(1, ge=1, le=10, description="生成数量")
    user: Optional[str] = Field(None, description="用户标识")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="可用工具")
    tool_choice: Optional[Union[str, Dict[str, Any]]] = Field(None, description="工具选择")


class Choice(BaseModel):
    """聊天选择."""
    
    index: int
    message: Message
    finish_reason: Optional[str] = None
    logprobs: Optional[Dict[str, Any]] = None


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
    choices: List[Choice]
    usage: Optional[Usage] = None
    system_fingerprint: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    """流式聊天响应块."""
    
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    system_fingerprint: Optional[str] = None


class ModelInfo(BaseModel):
    """模型信息."""
    
    id: str
    object: str = "model"
    created: int
    owned_by: str
    permission: Optional[List[Dict[str, Any]]] = None
    root: Optional[str] = None
    parent: Optional[str] = None


class ModelListResponse(BaseModel):
    """模型列表响应."""
    
    object: str = "list"
    data: List[ModelInfo]


class ChatStats(BaseModel):
    """聊天统计."""
    
    total_conversations: int = 0
    total_messages: int = 0
    total_tokens: int = 0
    avg_messages_per_conversation: float = 0.0
    avg_tokens_per_message: float = 0.0
    daily_usage: List[Dict[str, Any]] = []
    model_usage: Dict[str, int] = {}


class ChatHistoryExport(BaseModel):
    """聊天历史导出."""
    
    format: str = Field("json", description="导出格式")
    conversation_ids: Optional[List[int]] = Field(None, description="对话ID列表")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")
    include_system_messages: bool = Field(True, description="包含系统消息")
    include_metadata: bool = Field(True, description="包含元数据")