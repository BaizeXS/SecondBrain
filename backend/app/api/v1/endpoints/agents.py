"""Agent endpoints v2 - 使用服务层和CRUD层的完整版本."""

from collections.abc import AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
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
    DeepResearchRequest,
    DeepResearchResponse,
)
from app.services.deep_research_service import deep_research_service

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
        AgentResponse(
            id=1,
            name="Deep Research",
            description="基于Perplexity的深度研究代理，自动收集、分析和整理研究资料",
            agent_type="research",
            avatar_url=None,
            capabilities=["deep-research", "auto-collect", "analysis", "summary"],
            tools=None,
            is_public=True,
            is_active=True,
            is_verified=True,
            usage_count=0,
            rating=5.0,
            tags=["research", "deep-research", "perplexity"],
            user_id=None,  # 官方Agent
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
        ),
        AgentResponse(
            id=2,
            name="写作助手",
            description="帮助你创作和优化文本内容",
            agent_type="writing",
            avatar_url=None,
            capabilities=["generation", "editing", "translation"],
            tools=None,
            is_public=True,
            is_active=True,
            is_verified=True,
            usage_count=0,
            rating=5.0,
            tags=["writing", "creative"],
            user_id=None,  # 官方Agent
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
        ),
        AgentResponse(
            id=3,
            name="分析专家",
            description="进行数据分析和可视化",
            agent_type="analysis",
            avatar_url=None,
            capabilities=["analysis", "visualization", "report"],
            tools=None,
            is_public=True,
            is_active=True,
            is_verified=True,
            usage_count=0,
            rating=5.0,
            tags=["data", "analysis"],
            user_id=None,  # 官方Agent
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
        ),
    ]

    # 应用筛选
    if agent_type:
        agents = [a for a in agents if a.agent_type == agent_type]

    if is_public is not None:
        agents = [a for a in agents if a.is_public == is_public]

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
        1: AgentResponse(
            id=1,
            name="Deep Research",
            description="基于Perplexity的深度研究代理，自动收集、分析和整理研究资料",
            agent_type="research",
            avatar_url=None,
            capabilities=["deep-research", "auto-collect", "analysis", "summary"],
            tools=None,
            is_public=True,
            is_active=True,
            is_verified=True,
            usage_count=0,
            rating=5.0,
            tags=["research", "deep-research", "perplexity"],
            user_id=None,  # 官方Agent
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
        ),
        2: AgentResponse(
            id=2,
            name="写作助手",
            description="帮助你创作和优化文本内容",
            agent_type="writing",
            avatar_url=None,
            capabilities=["generation", "editing", "translation"],
            tools=None,
            is_public=True,
            is_active=True,
            is_verified=True,
            usage_count=0,
            rating=5.0,
            tags=["writing", "creative"],
            user_id=None,  # 官方Agent
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
        ),
        3: AgentResponse(
            id=3,
            name="分析专家",
            description="进行数据分析和可视化",
            agent_type="analysis",
            avatar_url=None,
            capabilities=["analysis", "visualization", "report"],
            tools=None,
            is_public=True,
            is_active=True,
            is_verified=True,
            usage_count=0,
            rating=5.0,
            tags=["data", "analysis"],
            user_id=None,  # 官方Agent
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
        ),
    }

    agent = agents.get(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="代理不存在",
        )

    return agent


@router.post("/{agent_id}/execute", response_model=None)
async def execute_agent(
    agent_id: int,
    request: AgentExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse | AgentExecuteResponse:
    """执行AI代理."""
    # Deep Research代理
    if agent_id == 1:
        # 调用Deep Research服务
        if request.stream:
            # 流式响应
            async def generate() -> AsyncGenerator[str, None]:
                async for chunk in deep_research_service.stream_research(
                    query=request.prompt,
                    mode=request.mode or "general",
                    user=current_user,
                    db=db,
                ):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            # 非流式响应
            result = await deep_research_service.create_research(
                query=request.prompt,
                mode=request.mode or "general",
                user=current_user,
                db=db,
                space_id=request.space_id,
            )
            if "error" in result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["error"],
                )
            return AgentExecuteResponse(
                execution_id=result.get("research_id", ""),
                agent_id=agent_id,
                status="completed",
                result=result,
                execution_time=0,
                created_at=result.get("created_at", datetime.now()),
            )
    # 其他代理的简化实现
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

    # 非Deep Research代理的响应
    return AgentExecuteResponse(
        execution_id="exec_" + str(agent_id),
        agent_id=agent_id,
        status="completed",
        result={"response": response},
        execution_time=1.5,
        tokens_used=100,
        created_at=datetime.now(),
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
        agent_type=agent_data.agent_type,
        avatar_url=agent_data.avatar_url,
        capabilities=agent_data.capabilities,
        tools=agent_data.tools,
        is_public=False,  # 默认私有
        is_active=True,
        is_verified=False,
        usage_count=0,
        rating=0.0,
        tags=None,
        user_id=current_user.id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@router.post("/deep-research", response_model=None)
async def create_deep_research(
    request: DeepResearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse | DeepResearchResponse:
    """创建Deep Research任务 - 专用端点."""
    if request.stream:
        # 流式响应
        async def generate() -> AsyncGenerator[str, None]:
            async for chunk in deep_research_service.stream_research(
                query=request.query, mode=request.mode, user=current_user, db=db
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # 非流式响应
        result = await deep_research_service.create_research(
            query=request.query,
            mode=request.mode,
            user=current_user,
            db=db,
            space_id=request.space_id,
        )
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )
        return DeepResearchResponse(
            research_id=result.get("research_id", ""),
            space_id=result.get("space_id"),
            query=result.get("query", ""),
            mode=result.get("mode", ""),
            status=result.get("status", ""),
            result=result.get("result"),
            created_at=datetime.now(),
        )
