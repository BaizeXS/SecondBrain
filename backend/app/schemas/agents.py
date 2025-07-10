"""Agent schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentCreate(BaseModel):
    """创建代理模式."""

    name: str = Field(..., min_length=1, max_length=100, description="代理名称")
    description: str = Field(..., description="代理描述")
    category: str = Field(..., description="代理分类")
    system_prompt: str = Field(..., description="系统提示词")
    model: str = Field(..., description="使用的AI模型")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int | None = Field(None, ge=1, description="最大令牌数")
    tools: list[dict[str, Any]] | None = Field(None, description="可用工具")
    capabilities: list[str] | None = Field(None, description="能力列表")
    metadata: dict[str, Any] | None = Field(None, description="元数据")
    is_public: bool = Field(default=False, description="是否公开")
    tags: list[str] | None = Field(None, description="标签")


class AgentUpdate(BaseModel):
    """更新代理模式."""

    name: str | None = Field(
        None, min_length=1, max_length=100, description="代理名称"
    )
    description: str | None = Field(None, description="代理描述")
    category: str | None = Field(None, description="代理分类")
    system_prompt: str | None = Field(None, description="系统提示词")
    model: str | None = Field(None, description="使用的AI模型")
    temperature: float | None = Field(None, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int | None = Field(None, ge=1, description="最大令牌数")
    tools: list[dict[str, Any]] | None = Field(None, description="可用工具")
    capabilities: list[str] | None = Field(None, description="能力列表")
    metadata: dict[str, Any] | None = Field(None, description="元数据")
    is_public: bool | None = Field(None, description="是否公开")
    is_active: bool | None = Field(None, description="是否启用")
    tags: list[str] | None = Field(None, description="标签")


class AgentResponse(BaseModel):
    """代理响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    category: str
    model: str
    temperature: float
    max_tokens: int | None = None
    capabilities: list[str] | None = None
    is_public: bool
    is_active: bool
    is_verified: bool
    usage_count: int = 0
    rating: float | None = None
    tags: list[str] | None = None
    created_by: int
    created_at: datetime
    updated_at: datetime | None = None


class AgentDetail(AgentResponse):
    """代理详细信息模式."""

    system_prompt: str
    tools: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None
    # 统计信息
    total_executions: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    recent_executions: list[dict[str, Any]] | None = None


class AgentListResponse(BaseModel):
    """代理列表响应模式."""

    agents: list[AgentResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class AgentExecuteRequest(BaseModel):
    """代理执行请求模式."""

    agent_id: int = Field(..., description="代理ID")
    input_data: str | dict[str, Any] = Field(..., description="输入数据")
    context: dict[str, Any] | None = Field(None, description="上下文")
    stream: bool = Field(default=False, description="是否流式响应")
    max_iterations: int = Field(default=10, ge=1, le=50, description="最大迭代次数")
    timeout: int = Field(default=300, ge=10, le=3600, description="超时时间(秒)")


class AgentExecuteResponse(BaseModel):
    """代理执行响应模式."""

    execution_id: str
    agent_id: int
    status: str
    result: str | dict[str, Any] | None = None
    error_message: str | None = None
    execution_time: float | None = None
    iterations: int = 0
    tokens_used: int | None = None
    cost: float | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime


class AgentExecutionLog(BaseModel):
    """代理执行日志模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    execution_id: str
    agent_id: int
    user_id: int
    status: str
    input_data: str | dict[str, Any]
    result: str | dict[str, Any] | None = None
    error_message: str | None = None
    execution_time: float
    iterations: int
    tokens_used: int | None = None
    cost: float | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime


class WorkflowCreate(BaseModel):
    """创建工作流模式."""

    name: str = Field(..., min_length=1, max_length=100, description="工作流名称")
    description: str = Field(..., description="工作流描述")
    agents: list[int] = Field(..., description="代理ID列表")
    workflow_config: dict[str, Any] = Field(..., description="工作流配置")
    is_public: bool = Field(default=False, description="是否公开")
    tags: list[str] | None = Field(None, description="标签")


class WorkflowUpdate(BaseModel):
    """更新工作流模式."""

    name: str | None = Field(
        None, min_length=1, max_length=100, description="工作流名称"
    )
    description: str | None = Field(None, description="工作流描述")
    agents: list[int] | None = Field(None, description="代理ID列表")
    workflow_config: dict[str, Any] | None = Field(None, description="工作流配置")
    is_public: bool | None = Field(None, description="是否公开")
    is_active: bool | None = Field(None, description="是否启用")
    tags: list[str] | None = Field(None, description="标签")


class WorkflowResponse(BaseModel):
    """工作流响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    agent_count: int
    is_public: bool
    is_active: bool
    usage_count: int = 0
    tags: list[str] | None = None
    created_by: int
    created_at: datetime
    updated_at: datetime | None = None


class WorkflowDetail(WorkflowResponse):
    """工作流详细信息模式."""

    agents: list[AgentResponse]
    workflow_config: dict[str, Any]
    execution_stats: dict[str, Any] | None = None


class WorkflowExecuteRequest(BaseModel):
    """工作流执行请求模式."""

    workflow_id: int = Field(..., description="工作流ID")
    input_data: dict[str, Any] = Field(..., description="输入数据")
    context: dict[str, Any] | None = Field(None, description="上下文")
    parallel_execution: bool = Field(default=False, description="并行执行")
    timeout: int = Field(default=600, ge=10, le=3600, description="超时时间(秒)")


class WorkflowExecuteResponse(BaseModel):
    """工作流执行响应模式."""

    execution_id: str
    workflow_id: int
    status: str
    results: list[dict[str, Any]] | None = None
    error_message: str | None = None
    execution_time: float | None = None
    total_tokens: int | None = None
    total_cost: float | None = None
    created_at: datetime


class AgentMarketplace(BaseModel):
    """代理市场模式."""

    featured_agents: list[AgentResponse] = []
    popular_agents: list[AgentResponse] = []
    recent_agents: list[AgentResponse] = []
    categories: list[dict[str, Any]] = []
    total_agents: int = 0


class AgentTemplate(BaseModel):
    """代理模板模式."""

    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    category: str = Field(..., description="模板分类")
    template_config: dict[str, Any] = Field(..., description="模板配置")
    required_params: list[str] = Field(default_factory=list, description="必需参数")
    optional_params: list[str] = Field(default_factory=list, description="可选参数")


class AgentRating(BaseModel):
    """代理评分模式."""

    agent_id: int = Field(..., description="代理ID")
    rating: int = Field(..., ge=1, le=5, description="评分")
    comment: str | None = Field(None, description="评论")


class AgentRatingResponse(BaseModel):
    """代理评分响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: int
    user_id: int
    rating: int
    comment: str | None = None
    created_at: datetime


class AgentStats(BaseModel):
    """代理统计模式."""

    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    total_tokens: int = 0
    total_cost: float = 0.0
    daily_usage: list[dict[str, Any]] = []
    popular_tools: list[dict[str, Any]] = []


class AgentSearch(BaseModel):
    """代理搜索请求模式."""

    query: str | None = Field(None, description="搜索查询")
    category: str | None = Field(None, description="分类")
    tags: list[str] | None = Field(None, description="标签")
    is_public: bool | None = Field(None, description="是否公开")
    is_verified: bool | None = Field(None, description="是否认证")
    min_rating: float | None = Field(None, ge=0.0, le=5.0, description="最低评分")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", description="排序顺序")
    limit: int = Field(default=20, ge=1, le=100, description="结果限制")


class AgentExport(BaseModel):
    """代理导出模式."""

    format: str = Field(default="json", description="导出格式")
    include_logs: bool = Field(default=False, description="包含日志")
    include_stats: bool = Field(default=True, description="包含统计")
    date_from: datetime | None = Field(None, description="开始日期")
    date_to: datetime | None = Field(None, description="结束日期")


class AgentImport(BaseModel):
    """代理导入模式."""

    agent_data: dict[str, Any] = Field(..., description="代理数据")
    overwrite_existing: bool = Field(default=False, description="覆盖现有")
    validate_tools: bool = Field(default=True, description="验证工具")
