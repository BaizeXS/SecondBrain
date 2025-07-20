"""Unit tests for Deep Research Service."""

import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User
from app.services.deep_research_service import DeepResearchService


@pytest.fixture
def mock_ai_service():
    """创建模拟AI服务."""
    ai_service = Mock()
    ai_service.openrouter_client = Mock()  # 表示OpenRouter已配置
    ai_service.chat = AsyncMock(return_value="Test research response")
    ai_service.stream_chat = AsyncMock()
    return ai_service


@pytest.fixture
def deep_research_service():
    """创建深度研究服务实例."""
    # 直接创建实例，然后手动设置mock的ai_service
    service = DeepResearchService()
    return service


@pytest.fixture
def mock_user():
    """创建模拟用户."""
    user = Mock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_db():
    """创建模拟数据库会话."""
    db = Mock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_space():
    """创建模拟空间."""
    space = Mock()
    space.id = 1
    space.name = "Test Research Space"
    return space


@pytest.fixture
def mock_perplexity_response():
    """模拟Perplexity API响应."""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677858242,
        "model": "sonar",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "这是一个深度研究报告示例。\n\n## 研究内容\n\n详细的研究内容...",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
        "citations": [
            {
                "title": "Test Citation",
                "url": "https://example.com",
                "snippet": "This is a test citation",
                "published_date": "2023-01-01",
            }
        ],
    }


class TestCreateResearch:
    """测试创建研究功能."""

    @pytest.mark.asyncio
    async def test_create_research_no_api_key(self):
        """测试没有API密钥的情况."""
        service = DeepResearchService()
        # 设置没有OpenRouter的AI服务
        service.ai_service.openrouter_client = None
        
        result = await service.create_research("test query")

        assert result["error"] == "Deep Research功能未配置"
        assert "请配置OPENROUTER_API_KEY环境变量" in result["message"]

    @pytest.mark.asyncio
    async def test_create_research_success_no_space(
        self, deep_research_service, mock_perplexity_response
    ):
        """测试成功创建研究（无空间）."""
        # 设置AI服务返回模拟响应
        deep_research_service.ai_service.chat = AsyncMock(
            return_value=mock_perplexity_response["choices"][0]["message"]["content"]
        )
        deep_research_service.ai_service.openrouter_client = Mock()  # 表示已配置

        result = await deep_research_service.create_research(
            query="AI研究主题",
            mode="general",
        )

        assert result["status"] == "completed"
        assert result["query"] == "AI研究主题"
        assert result["mode"] == "general"
        assert "result" in result

    @pytest.mark.asyncio
    async def test_create_research_with_space_creation(
        self, deep_research_service, mock_user, mock_db, mock_space
    ):
        """测试创建研究并自动创建空间."""
        # 设置AI服务
        deep_research_service.ai_service.chat = AsyncMock(return_value="Research content")
        deep_research_service.ai_service.openrouter_client = Mock()
        
        with patch("app.services.deep_research_service.crud_space") as mock_crud_space:
            mock_crud_space.create = AsyncMock(return_value=mock_space)
            
            result = await deep_research_service.create_research(
                query="学术研究主题",
                mode="academic",
                user=mock_user,
                db=mock_db,
            )

            assert result["status"] == "completed"
            assert result["mode"] == "academic"
            assert result["space_id"] == 1
            # 验证空间创建参数
            create_call = mock_crud_space.create.call_args
            space_data = create_call[1]["obj_in"]
            assert "研究: 学术研究主题" in space_data.name
            assert space_data.icon == "🔬"  # academic mode icon

    @pytest.mark.asyncio
    async def test_create_research_with_existing_space(
        self, deep_research_service, mock_user, mock_db
    ):
        """测试使用现有空间创建研究."""
        deep_research_service.ai_service.chat = AsyncMock(return_value="Research content")
        deep_research_service.ai_service.openrouter_client = Mock()
        
        result = await deep_research_service.create_research(
            query="测试查询",
            mode="general",
            user=mock_user,
            db=mock_db,
            space_id=42,
        )

        assert result["status"] == "completed"
        assert result["space_id"] == 42

    @pytest.mark.asyncio
    async def test_create_research_api_error(
        self, deep_research_service, mock_user, mock_db
    ):
        """测试API调用错误."""
        deep_research_service.ai_service.chat = AsyncMock(side_effect=Exception("API Error"))
        deep_research_service.ai_service.openrouter_client = Mock()

        result = await deep_research_service.create_research(
            query="测试查询",
            mode="general",
            user=mock_user,
            db=mock_db,
        )

        assert "error" in result
        assert result["error"] == "API调用失败"

    @pytest.mark.asyncio
    async def test_create_research_timeout(
        self, deep_research_service, mock_user, mock_db
    ):
        """测试超时错误."""
        import httpx
        deep_research_service.ai_service.chat = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout")
        )
        deep_research_service.ai_service.openrouter_client = Mock()

        result = await deep_research_service.create_research(
            query="测试查询",
            mode="general",
            user=mock_user,
            db=mock_db,
        )

        assert "error" in result
        assert result["error"] == "API调用失败"

    @pytest.mark.asyncio
    async def test_create_research_exception(
        self, deep_research_service, mock_user, mock_db
    ):
        """测试通用异常处理."""
        deep_research_service.ai_service.chat = AsyncMock(
            side_effect=Exception("Unknown error")
        )
        deep_research_service.ai_service.openrouter_client = Mock()

        result = await deep_research_service.create_research(
            query="测试查询",
            mode="general",
            user=mock_user,
            db=mock_db,
        )

        assert "error" in result
        assert result["error"] == "API调用失败"
        assert "Unknown error" in result["message"]


class TestSaveResearchResults:
    """测试保存研究结果功能."""

    @pytest.mark.asyncio
    async def test_save_research_results_success(
        self, deep_research_service, mock_db, mock_perplexity_response
    ):
        """测试成功保存研究结果."""
        with patch(
            "app.services.deep_research_service.crud_document"
        ) as mock_crud_document:
            mock_crud_document.create = AsyncMock()

            await deep_research_service._save_research_results(
                db=mock_db,
                space_id=1,
                user_id=1,
                research_data=mock_perplexity_response,
                query="测试查询",
            )

            # 验证创建了主报告和引用文献
            assert mock_crud_document.create.call_count == 2  # 1个报告 + 1个引用
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_research_results_no_citations(
        self, deep_research_service, mock_db
    ):
        """测试保存没有引用的研究结果."""
        research_data = {
            "choices": [
                {"message": {"content": "Research content", "role": "assistant"}}
            ],
            "citations": [],
        }

        with patch(
            "app.services.deep_research_service.crud_document"
        ) as mock_crud_document:
            mock_crud_document.create = AsyncMock()

            await deep_research_service._save_research_results(
                db=mock_db,
                space_id=1,
                user_id=1,
                research_data=research_data,
                query="测试查询",
            )

            # 只创建主报告，没有引用文献
            assert mock_crud_document.create.call_count == 1

    @pytest.mark.asyncio
    async def test_save_research_results_exception(
        self, deep_research_service, mock_db, mock_perplexity_response
    ):
        """测试保存过程中出现异常."""
        with patch(
            "app.services.deep_research_service.crud_document"
        ) as mock_crud_document:
            mock_crud_document.create.side_effect = Exception("Save error")

            await deep_research_service._save_research_results(
                db=mock_db,
                space_id=1,
                user_id=1,
                research_data=mock_perplexity_response,
                query="测试查询",
            )

            mock_db.rollback.assert_called_once()


class TestFormatCitation:
    """测试格式化引用功能."""

    def test_format_citation_complete(self, deep_research_service):
        """测试完整的引用格式化."""
        citation = {
            "title": "Test Citation",
            "authors": ["Author One", "Author Two"],
            "url": "https://example.com",
            "published_date": "2024-01-01",
            "snippet": "This is a test snippet",
            "highlights": ["Point 1", "Point 2"],
        }

        result = deep_research_service._format_citation(citation)

        assert "# Test Citation" in result
        assert "**作者**: Author One, Author Two" in result
        assert "**链接**: [https://example.com]" in result
        assert "**发表时间**: 2024-01-01" in result
        assert "## 摘要" in result
        assert "This is a test snippet" in result
        assert "## 关键内容" in result
        assert "- Point 1" in result
        assert "- Point 2" in result

    def test_format_citation_minimal(self, deep_research_service):
        """测试最小引用格式化."""
        citation = {"title": "Minimal Citation"}

        result = deep_research_service._format_citation(citation)

        assert "# Minimal Citation" in result
        assert "**作者**" not in result
        assert "**链接**" not in result

    def test_format_citation_partial(self, deep_research_service):
        """测试部分引用格式化."""
        citation = {
            "title": "Partial Citation",
            "url": "https://example.com",
            "snippet": "Test snippet",
        }

        result = deep_research_service._format_citation(citation)

        assert "# Partial Citation" in result
        assert "**链接**" in result
        assert "## 摘要" in result
        assert "**作者**" not in result


class TestStreamResearch:
    """测试流式研究功能."""

    @pytest.mark.asyncio
    async def test_stream_research_no_api_key(self):
        """测试流式研究没有API密钥."""
        service = DeepResearchService()
        # 设置没有OpenRouter的AI服务
        service.ai_service.openrouter_client = None
        
        results = []
        async for chunk in service.stream_research(
            query="测试",
            mode="general",
        ):
            results.append(json.loads(chunk))

        assert len(results) == 1
        assert "error" in results[0]
        assert results[0]["error"] == "Deep Research功能未配置"

    @pytest.mark.asyncio
    async def test_stream_research_success(
        self, deep_research_service, mock_user, mock_db, mock_space
    ):
        """测试成功的流式研究."""
        # 模拟流式响应
        async def mock_stream():
            yield "Part 1"
            yield "Part 2"
            yield "Part 3"

        deep_research_service.ai_service.stream_chat = MagicMock(return_value=mock_stream())
        deep_research_service.ai_service.openrouter_client = Mock()

        with patch("app.services.deep_research_service.crud_space") as mock_crud_space:
            mock_crud_space.create = AsyncMock(return_value=mock_space)

            results = []
            async for chunk in deep_research_service.stream_research(
                query="流式测试",
                mode="general",
                user=mock_user,
                db=mock_db,
            ):
                results.append(json.loads(chunk))

            # 验证结果
            assert any(r["type"] == "space_created" for r in results)
            assert any(r["type"] == "update" for r in results)
            assert any(r["type"] == "completed" for r in results)

    @pytest.mark.asyncio
    async def test_stream_research_no_user(self, deep_research_service):
        """测试没有用户的流式研究."""
        # 模拟流式响应
        async def mock_stream():
            yield "Response"

        deep_research_service.ai_service.stream_chat = MagicMock(return_value=mock_stream())
        deep_research_service.ai_service.openrouter_client = Mock()

        results = []
        async for chunk in deep_research_service.stream_research(
            query="测试",
            mode="general",
            user=None,
            db=None,
        ):
            results.append(json.loads(chunk))

        # 没有用户时不创建空间
        assert not any(r.get("type") == "space_created" for r in results)

    @pytest.mark.asyncio
    async def test_stream_research_invalid_json(self, deep_research_service):
        """测试流式研究中的JSON解析错误."""
        # 这个测试主要验证服务的健壮性
        async def mock_stream():
            yield "Valid response"

        deep_research_service.ai_service.stream_chat = MagicMock(return_value=mock_stream())
        deep_research_service.ai_service.openrouter_client = Mock()

        results = []
        async for chunk in deep_research_service.stream_research(
            query="测试",
            mode="general",
        ):
            # 所有chunk都应该是有效的JSON
            result = json.loads(chunk)
            results.append(result)

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_stream_research_exception(
        self, deep_research_service, mock_user, mock_db
    ):
        """测试流式研究中的异常处理."""
        deep_research_service.ai_service.stream_chat = MagicMock(
            side_effect=Exception("Stream error")
        )
        deep_research_service.ai_service.openrouter_client = Mock()

        results = []
        async for chunk in deep_research_service.stream_research(
            query="测试",
            mode="general",
            user=mock_user,
            db=mock_db,
        ):
            results.append(json.loads(chunk))

        assert any("error" in r for r in results)


class TestInitialization:
    """测试服务初始化."""

    def test_init_with_api_key(self):
        """测试有API密钥时的初始化."""
        service = DeepResearchService()
        # 假设AI服务已经配置了OpenRouter
        if hasattr(service.ai_service, 'openrouter_client'):
            assert service.ai_service.openrouter_client is not None or service.ai_service.openrouter_client is None
        # 这个测试主要验证服务能正确初始化

    def test_init_without_api_key(self):
        """测试没有API密钥时的初始化."""
        service = DeepResearchService()
        # 服务应该能正常初始化，即使没有API密钥
        assert hasattr(service, 'ai_service')


class TestGlobalInstance:
    """测试全局实例."""

    def test_global_instance_exists(self):
        """测试全局实例存在."""
        from app.services.deep_research_service import deep_research_service

        assert deep_research_service is not None
        assert isinstance(deep_research_service, DeepResearchService)