"""agents.py 的完整单元测试"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.agents import (
    create_agent,
    create_deep_research,
    execute_agent,
    get_agent,
    get_agents,
)
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


class TestAgentsList:
    """测试代理列表功能"""

    @pytest.mark.asyncio
    async def test_get_agents_all(self):
        """测试获取所有代理"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        result = await get_agents(
            agent_type=None,
            is_public=None,
            skip=0,
            limit=20,
            db=mock_db,
            current_user=mock_user,
        )

        assert isinstance(result, AgentListResponse)
        assert result.total == 3  # 预定义了3个代理
        assert len(result.agents) == 3
        assert result.page == 1
        assert result.has_next is False

    @pytest.mark.asyncio
    async def test_get_agents_filtered_by_type(self):
        """测试按类型过滤代理"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        result = await get_agents(
            agent_type="research",
            is_public=None,
            skip=0,
            limit=20,
            db=mock_db,
            current_user=mock_user,
        )

        assert isinstance(result, AgentListResponse)
        assert result.total == 1
        assert len(result.agents) == 1
        assert result.agents[0].agent_type == "research"
        assert result.agents[0].user_id is None  # 官方Agent

    @pytest.mark.asyncio
    async def test_get_agents_pagination(self):
        """测试代理列表分页"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        result = await get_agents(
            agent_type=None,
            is_public=None,
            skip=2,
            limit=1,
            db=mock_db,
            current_user=mock_user,
        )

        assert isinstance(result, AgentListResponse)
        assert result.total == 3
        assert len(result.agents) == 1
        assert result.page == 3  # skip=2, limit=1, 所以是第3页
        assert result.has_next is False


class TestAgentDetail:
    """测试代理详情功能"""

    @pytest.mark.asyncio
    async def test_get_agent_success(self):
        """测试成功获取代理详情"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        result = await get_agent(agent_id=1, db=mock_db, current_user=mock_user)

        assert isinstance(result, AgentResponse)
        assert result.id == 1
        assert result.name == "Deep Research"
        assert result.agent_type == "research"
        assert result.user_id is None  # 官方Agent

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self):
        """测试获取不存在的代理"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        with pytest.raises(HTTPException) as exc_info:
            await get_agent(agent_id=999, db=mock_db, current_user=mock_user)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "代理不存在" in str(exc_info.value.detail)


class TestAgentExecution:
    """测试代理执行功能"""

    @pytest.mark.asyncio
    async def test_execute_deep_research_stream(self):
        """测试执行Deep Research代理流式响应"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        request = AgentExecuteRequest(
            prompt="test query",
            mode="general",
            context=None,
            stream=True,
            space_id=None,
            parameters=None,
        )

        async def mock_stream():
            yield '{"content": "Research result"}'

        with patch("app.api.v1.endpoints.agents.deep_research_service") as mock_service:
            mock_service.stream_research = AsyncMock(return_value=mock_stream())

            result = await execute_agent(
                agent_id=1, request=request, db=mock_db, current_user=mock_user
            )

            assert isinstance(result, StreamingResponse)
            assert result.media_type == "text/event-stream"

    @pytest.mark.asyncio
    async def test_execute_deep_research_non_stream(self):
        """测试执行Deep Research代理非流式响应"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        request = AgentExecuteRequest(
            prompt="test query",
            mode="general",
            context=None,
            stream=False,
            space_id=1,
            parameters=None,
        )

        mock_result = {
            "research_id": "res_123",
            "space_id": 1,
            "query": "test query",
            "mode": "general",
            "status": "completed",
            "result": {"summary": "Test summary"},
            "created_at": datetime.now(),
        }

        with patch("app.api.v1.endpoints.agents.deep_research_service") as mock_service:
            mock_service.create_research = AsyncMock(return_value=mock_result)

            result = await execute_agent(
                agent_id=1, request=request, db=mock_db, current_user=mock_user
            )

            assert isinstance(result, AgentExecuteResponse)
            assert result.execution_id == "res_123"
            assert result.status == "completed"
            assert result.result == mock_result

    @pytest.mark.asyncio
    async def test_execute_deep_research_error(self):
        """测试执行Deep Research代理失败"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        request = AgentExecuteRequest(
            prompt="test query",
            mode="general",
            context=None,
            stream=False,
            space_id=None,
            parameters=None,
        )

        with patch("app.api.v1.endpoints.agents.deep_research_service") as mock_service:
            mock_service.create_research = AsyncMock(
                return_value={"error": "API error"}
            )

            with pytest.raises(HTTPException) as exc_info:
                await execute_agent(
                    agent_id=1, request=request, db=mock_db, current_user=mock_user
                )

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "API error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_execute_writing_agent(self):
        """测试执行写作助手代理"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        request = AgentExecuteRequest(
            prompt="帮我写一篇文章",
            mode=None,
            context=None,
            stream=False,
            space_id=None,
            parameters=None,
        )

        result = await execute_agent(
            agent_id=2, request=request, db=mock_db, current_user=mock_user
        )

        assert isinstance(result, AgentExecuteResponse)
        assert result.agent_id == 2
        assert result.status == "completed"
        assert result.result is not None
        assert isinstance(result.result, dict)
        assert "response" in result.result
        assert "创作了以下内容" in result.result["response"]

    @pytest.mark.asyncio
    async def test_execute_analysis_agent(self):
        """测试执行分析专家代理"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        request = AgentExecuteRequest(
            prompt="分析数据趋势",
            mode=None,
            context=None,
            stream=False,
            space_id=None,
            parameters=None,
        )

        result = await execute_agent(
            agent_id=3, request=request, db=mock_db, current_user=mock_user
        )

        assert isinstance(result, AgentExecuteResponse)
        assert result.agent_id == 3
        assert result.status == "completed"
        assert result.result is not None
        assert isinstance(result.result, dict)
        assert "response" in result.result
        assert "分析结果如下" in result.result["response"]

    @pytest.mark.asyncio
    async def test_execute_agent_not_found(self):
        """测试执行不存在的代理"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        request = AgentExecuteRequest(
            prompt="test",
            mode=None,
            context=None,
            stream=False,
            space_id=None,
            parameters=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            await execute_agent(
                agent_id=999, request=request, db=mock_db, current_user=mock_user
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "代理不存在" in str(exc_info.value.detail)


class TestAgentCreation:
    """测试代理创建功能"""

    @pytest.mark.asyncio
    async def test_create_agent_premium_user(self):
        """测试高级用户创建代理"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.is_premium = True

        agent_data = AgentCreate(
            name="Custom Agent",
            description="My custom agent",
            agent_type="custom",
            prompt_template="You are a custom agent...",
            config={"temperature": 0.7},
            capabilities=["custom"],
            tools=None,
            avatar_url=None,
        )

        result = await create_agent(
            agent_data=agent_data, db=mock_db, current_user=mock_user
        )

        assert isinstance(result, AgentResponse)
        assert result.id == 100
        assert result.name == "Custom Agent"
        assert result.agent_type == "custom"
        assert result.is_active is True
        assert result.is_verified is False

    @pytest.mark.asyncio
    async def test_create_agent_non_premium_user(self):
        """测试非高级用户创建代理"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.is_premium = False

        agent_data = AgentCreate(
            name="Custom Agent",
            description="My custom agent",
            agent_type="custom",
            prompt_template="You are a custom agent...",
            config={},
            capabilities=["custom"],
            tools=None,
            avatar_url=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_agent(
                agent_data=agent_data, db=mock_db, current_user=mock_user
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "高级会员权限" in str(exc_info.value.detail)


class TestDeepResearch:
    """测试Deep Research专用端点"""

    @pytest.mark.asyncio
    async def test_create_deep_research_stream(self):
        """测试创建Deep Research任务流式响应"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        request = DeepResearchRequest(
            query="test research",
            mode="general",
            stream=True,
            space_id=None,
        )

        async def mock_stream():
            yield '{"content": "Research in progress..."}'

        with patch("app.api.v1.endpoints.agents.deep_research_service") as mock_service:
            mock_service.stream_research = AsyncMock(return_value=mock_stream())

            result = await create_deep_research(
                request=request, db=mock_db, current_user=mock_user
            )

            assert isinstance(result, StreamingResponse)
            assert result.media_type == "text/event-stream"

    @pytest.mark.asyncio
    async def test_create_deep_research_non_stream(self):
        """测试创建Deep Research任务非流式响应"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        request = DeepResearchRequest(
            query="test research",
            mode="academic",
            stream=False,
            space_id=1,
        )

        mock_result = {
            "research_id": "res_456",
            "space_id": 1,
            "query": "test research",
            "mode": "academic",
            "status": "completed",
            "result": {"summary": "Academic research summary"},
        }

        with patch("app.api.v1.endpoints.agents.deep_research_service") as mock_service:
            mock_service.create_research = AsyncMock(return_value=mock_result)

            result = await create_deep_research(
                request=request, db=mock_db, current_user=mock_user
            )

            assert isinstance(result, DeepResearchResponse)
            assert result.research_id == "res_456"
            assert result.query == "test research"
            assert result.mode == "academic"
            assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_create_deep_research_error(self):
        """测试创建Deep Research任务失败"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        request = DeepResearchRequest(
            query="test research",
            mode="general",
            stream=False,
            space_id=None,
        )

        with patch("app.api.v1.endpoints.agents.deep_research_service") as mock_service:
            mock_service.create_research = AsyncMock(
                return_value={"error": "Service unavailable"}
            )

            with pytest.raises(HTTPException) as exc_info:
                await create_deep_research(
                    request=request, db=mock_db, current_user=mock_user
                )

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Service unavailable" in str(exc_info.value.detail)

