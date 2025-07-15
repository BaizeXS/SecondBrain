"""Ollama schemas."""

from typing import Any

from pydantic import BaseModel, Field


class OllamaModelResponse(BaseModel):
    """Ollama模型响应."""

    name: str = Field(..., description="模型名称")
    size: int = Field(..., description="模型大小（字节）")
    digest: str = Field(..., description="模型摘要")
    modified_at: str = Field(..., description="修改时间")

    @property
    def size_human(self) -> str:
        """人类可读的文件大小."""
        size: float = float(self.size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size = size / 1024.0
        return f"{size:.1f} PB"


class OllamaModelListResponse(BaseModel):
    """Ollama模型列表响应."""

    models: list[OllamaModelResponse] = Field(default_factory=list, description="模型列表")
    total: int = Field(0, description="模型总数")
    is_available: bool = Field(True, description="Ollama服务是否可用")
    error: str | None = Field(None, description="错误信息")


class OllamaPullRequest(BaseModel):
    """拉取模型请求."""

    model_name: str = Field(..., description="要拉取的模型名称")
    insecure: bool = Field(False, description="是否允许不安全的连接")


class OllamaPullResponse(BaseModel):
    """拉取模型响应."""

    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="状态: pulling/completed/failed")
    model_name: str = Field(..., description="模型名称")
    progress: int | None = Field(None, description="下载进度（0-100）")
    message: str | None = Field(None, description="状态消息")


class OllamaModelInfo(BaseModel):
    """模型详细信息."""

    name: str = Field(..., description="模型名称")
    model_format: str = Field(..., description="模型格式")
    family: str = Field(..., description="模型家族")
    parameter_size: str = Field(..., description="参数大小")
    quantization_level: str = Field(..., description="量化级别")
    size: int = Field(..., description="模型大小（字节）")
    digest: str = Field(..., description="模型摘要")
    details: dict[str, Any] = Field(default_factory=dict, description="其他详细信息")

    @property
    def size_human(self) -> str:
        """人类可读的文件大小."""
        size: float = float(self.size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size = size / 1024.0
        return f"{size:.1f} PB"


class OllamaGenerateRequest(BaseModel):
    """生成请求."""

    model: str = Field(..., description="模型名称")
    prompt: str = Field(..., description="提示词")
    system: str | None = Field(None, description="系统提示词")
    template: str | None = Field(None, description="模板")
    context: list[int] | None = Field(None, description="上下文")
    stream: bool = Field(True, description="是否流式输出")
    raw: bool = Field(False, description="是否原始模式")
    format: str | None = Field(None, description="输出格式")
    options: dict[str, Any] | None = Field(None, description="生成选项")


class OllamaChatRequest(BaseModel):
    """聊天请求."""

    model: str = Field(..., description="模型名称")
    messages: list[dict[str, str]] = Field(..., description="消息列表")
    stream: bool = Field(True, description="是否流式输出")
    format: str | None = Field(None, description="输出格式")
    options: dict[str, Any] | None = Field(None, description="生成选项")


class OllamaEmbeddingRequest(BaseModel):
    """嵌入请求."""

    model: str = Field(..., description="模型名称")
    prompt: str = Field(..., description="要嵌入的文本")


class OllamaEmbeddingResponse(BaseModel):
    """嵌入响应."""

    embedding: list[float] = Field(..., description="嵌入向量")
    model: str = Field(..., description="使用的模型")


class OllamaStatusResponse(BaseModel):
    """Ollama服务状态."""

    available: bool = Field(..., description="服务是否可用")
    version: str | None = Field(None, description="Ollama版本")
    models_count: int = Field(0, description="已安装模型数量")
    total_size: int = Field(0, description="所有模型总大小")
    gpu_available: bool = Field(False, description="GPU是否可用")
    gpu_info: dict[str, Any] | None = Field(None, description="GPU信息")
