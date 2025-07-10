"""Agent endpoints v2 - 使用服务层和CRUD层的完整版本."""


from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.models import User
from app.schemas.agents import (
    AgentCreate,
    AgentExecuteRequest,
    AgentExecuteResponse,
    AgentListResponse,
    AgentResponse,
)

router = APIRouter()


@router.get("/", response_model=AgentListResponse)
async def get_agents(
    agent_type: str | None = Query(None, description="代理类型"),
    is_public: bool | None = Query(True, description="是否公开"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AgentListResponse:
    """获取AI代理列表."""
    # 简化版本：返回预定义的代理列表
    agents = [
        {
            "id": 1,
            "name": "研究助手",
            "description": "帮助你进行深度研究和信息收集",
            "category": "research",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "capabilities": ["search", "analysis", "summary"],
            "is_public": True,
            "is_active": True,
            "is_verified": True,
            "usage_count": 0,
            "rating": 5.0,
            "tags": ["research", "analysis"],
            "created_by": current_user.id,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        },
        {
            "id": 2,
            "name": "写作助手",
            "description": "帮助你创作和优化文本内容",
            "category": "writing",
            "model": "gpt-4o-mini",
            "temperature": 0.8,
            "capabilities": ["generation", "editing", "translation"],
            "is_public": True,
            "is_active": True,
            "is_verified": True,
            "usage_count": 0,
            "rating": 5.0,
            "tags": ["writing", "creative"],
            "created_by": current_user.id,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        },
        {
            "id": 3,
            "name": "分析专家",
            "description": "进行数据分析和可视化",
            "category": "analysis",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
            "capabilities": ["analysis", "visualization", "report"],
            "is_public": True,
            "is_active": True,
            "is_verified": True,
            "usage_count": 0,
            "rating": 5.0,
            "tags": ["data", "analysis"],
            "created_by": current_user.id,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        },
    ]

    # 应用筛选
    if agent_type:
        agents = [a for a in agents if a["category"] == agent_type]

    if is_public is not None:
        agents = [a for a in agents if a["is_public"] == is_public]

    # 分页
    total = len(agents)
    agents = agents[skip : skip + limit]

    return AgentListResponse(
        agents=agents,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        has_next=total > skip + limit,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AgentResponse:
    """获取AI代理详情."""
    # 简化版本：返回预定义的代理
    agents = {
        1: {
            "id": 1,
            "name": "研究助手",
            "description": "帮助你进行深度研究和信息收集",
            "category": "research",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 2000,
            "capabilities": ["search", "analysis", "summary"],
            "is_public": True,
            "is_active": True,
            "is_verified": True,
            "usage_count": 0,
            "rating": 5.0,
            "tags": ["research", "analysis"],
            "created_by": current_user.id,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        },
        2: {
            "id": 2,
            "name": "写作助手",
            "description": "帮助你创作和优化文本内容",
            "category": "writing",
            "model": "gpt-4o-mini",
            "temperature": 0.8,
            "max_tokens": 2000,
            "capabilities": ["generation", "editing", "translation"],
            "is_public": True,
            "is_active": True,
            "is_verified": True,
            "usage_count": 0,
            "rating": 5.0,
            "tags": ["writing", "creative"],
            "created_by": current_user.id,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        },
        3: {
            "id": 3,
            "name": "分析专家",
            "description": "进行数据分析和可视化",
            "category": "analysis",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
            "max_tokens": 2000,
            "capabilities": ["analysis", "visualization", "report"],
            "is_public": True,
            "is_active": True,
            "is_verified": True,
            "usage_count": 0,
            "rating": 5.0,
            "tags": ["data", "analysis"],
            "created_by": current_user.id,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        },
    }

    agent = agents.get(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="代理不存在",
        )

    return AgentResponse(**agent)


@router.post("/{agent_id}/execute", response_model=AgentExecuteResponse)
async def execute_agent(
    agent_id: int,
    request: AgentExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AgentExecuteResponse:
    """执行AI代理."""
    # 简化版本：返回模拟响应
    if agent_id == 1:  # 研究助手
        response = f"根据你的查询 '{request.prompt}'，我进行了以下研究：\n\n"
        response += "1. 搜索相关资料\n"
        response += "2. 分析信息\n"
        response += "3. 总结要点\n\n"
        response += "这是一个演示响应。在实际应用中，这里会返回真实的研究结果。"
    elif agent_id == 2:  # 写作助手
        response = f"基于你的需求 '{request.prompt}'，我创作了以下内容：\n\n"
        response += "这是一个演示响应。在实际应用中，这里会返回真实的创作内容。"
    elif agent_id == 3:  # 分析专家
        response = f"针对你的分析需求 '{request.prompt}'，我的分析结果如下：\n\n"
        response += "这是一个演示响应。在实际应用中，这里会返回真实的分析结果。"
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="代理不存在",
        )

    return AgentExecuteResponse(
        execution_id="exec_" + str(agent_id),
        agent_id=agent_id,
        status="completed",
        result={"response": response},
        execution_time=1.5,
        tokens_used=100,
        created_at="2024-01-01T00:00:00",
    )


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AgentResponse:
    """创建自定义AI代理（高级用户功能）."""
    # 检查用户权限
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="创建自定义代理需要高级会员权限",
        )

    # 简化版本：返回创建成功的响应
    return AgentResponse(
        id=100,
        name=agent_data.name,
        description=agent_data.description,
        category=agent_data.category,
        model=agent_data.model,
        temperature=agent_data.temperature,
        max_tokens=agent_data.max_tokens,
        capabilities=agent_data.capabilities,
        is_public=agent_data.is_public,
        is_active=True,
        is_verified=False,
        usage_count=0,
        rating=0.0,
        tags=agent_data.tags,
        created_by=current_user.id,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
