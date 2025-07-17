"""Unit tests for Deep Research Service."""

import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User
from app.services.deep_research_service import DeepResearchService


@pytest.fixture
def deep_research_service():
    """创建深度研究服务实例."""
    with patch('app.services.deep_research_service.settings') as mock_settings:
        mock_settings.PERPLEXITY_API_KEY = "test_api_key"
        mock_settings.PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
        return DeepResearchService()


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
                    "content": "这是一个深度研究报告示例。\n\n## 研究内容\n\n详细的研究内容..."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 200,
            "total_tokens": 300
        },
        "citations": [
            {
                "title": "Test Citation",
                "url": "https://example.com",
                "snippet": "This is a test citation",
                "published_date": "2023-01-01"
            }
        ]
    }


class TestCreateResearch:
    """测试创建研究功能."""

    @pytest.mark.asyncio
    async def test_create_research_no_api_key(self):
        """测试没有API密钥的情况."""
        with patch('app.services.deep_research_service.settings') as mock_settings:
            mock_settings.PERPLEXITY_API_KEY = None
            service = DeepResearchService()

            result = await service.create_research("test query")

            assert result["error"] == "Deep Research功能未配置"
            assert "请配置PERPLEXITY_API_KEY环境变量" in result["message"]

    @pytest.mark.asyncio
    async def test_create_research_success_no_space(
        self, deep_research_service, mock_perplexity_response
    ):
        """测试成功创建研究（无空间）."""
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_perplexity_response
            mock_client.post.return_value = mock_response

            result = await deep_research_service.create_research("test query")

            assert result["query"] == "test query"
            assert result["mode"] == "general"
            assert result["status"] == "completed"
            assert "research_id" in result
            assert result["result"] == mock_perplexity_response

    @pytest.mark.asyncio
    async def test_create_research_with_space_creation(
        self, deep_research_service, mock_user, mock_db, mock_space, mock_perplexity_response
    ):
        """测试创建研究并自动创建空间."""
        with patch('httpx.AsyncClient') as MockClient, \
             patch('app.services.deep_research_service.crud_space') as mock_crud_space:

            # Mock HTTP client
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_perplexity_response
            mock_client.post.return_value = mock_response

            # Mock space creation
            mock_crud_space.create = AsyncMock(return_value=mock_space)

            # Mock save results
            with patch.object(deep_research_service, '_save_research_results') as mock_save:
                mock_save.return_value = None

                result = await deep_research_service.create_research(
                    "test query",
                    mode="academic",
                    user=mock_user,
                    db=mock_db
                )

                assert result["space_id"] == 1
                assert result["query"] == "test query"
                assert result["mode"] == "academic"
                assert result["status"] == "completed"

                # Verify space creation
                mock_crud_space.create.assert_called_once()
                space_data = mock_crud_space.create.call_args[1]["obj_in"]
                assert "研究: test query" in space_data.name
                assert space_data.icon == "🔬"  # academic mode icon

                # Verify save results called
                mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_research_with_existing_space(
        self, deep_research_service, mock_user, mock_db, mock_perplexity_response
    ):
        """测试使用现有空间创建研究."""
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_perplexity_response
            mock_client.post.return_value = mock_response

            with patch.object(deep_research_service, '_save_research_results') as mock_save:
                mock_save.return_value = None

                result = await deep_research_service.create_research(
                    "test query",
                    user=mock_user,
                    db=mock_db,
                    space_id=5
                )

                assert result["space_id"] == 5
                mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_research_api_error(self, deep_research_service):
        """测试API错误情况."""
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_client.post.return_value = mock_response

            result = await deep_research_service.create_research("test query")

            assert result["error"] == "API调用失败"
            assert result["message"] == "状态码: 400"
            assert result["details"] == "Bad Request"

    @pytest.mark.asyncio
    async def test_create_research_timeout(self, deep_research_service):
        """测试超时情况."""
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = httpx.TimeoutException("Timeout")

            result = await deep_research_service.create_research("test query")

            assert result["error"] == "请求超时"
            assert "研究任务执行时间过长" in result["message"]

    @pytest.mark.asyncio
    async def test_create_research_exception(self, deep_research_service):
        """测试异常情况."""
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = Exception("Network error")

            result = await deep_research_service.create_research("test query")

            assert result["error"] == "研究失败"
            assert result["message"] == "Network error"


class TestSaveResearchResults:
    """测试保存研究结果功能."""

    @pytest.mark.asyncio
    async def test_save_research_results_success(
        self, deep_research_service, mock_db, mock_perplexity_response
    ):
        """测试成功保存研究结果."""
        with patch('app.services.deep_research_service.crud_document') as mock_crud_document:
            mock_crud_document.create = AsyncMock(return_value=Mock())

            research_data = {
                "report": "Test research report",
                "summary": "Test summary",
                "citations": [
                    {
                        "title": "Test Citation",
                        "url": "https://example.com",
                        "snippet": "Test snippet"
                    }
                ]
            }

            await deep_research_service._save_research_results(
                db=mock_db,
                space_id=1,
                user_id=1,
                research_data=research_data,
                query="test query"
            )

            # Verify main report creation
            assert mock_crud_document.create.call_count == 2  # 主报告 + 1个引用

            # Check main report
            main_report_call = mock_crud_document.create.call_args_list[0]
            main_report_data = main_report_call[1]["obj_in"]
            assert main_report_data.filename == "研究报告.md"
            assert main_report_data.space_id == 1
            assert main_report_data.meta_data["document_type"] == "research_report"
            assert main_report_data.meta_data["content"] == "Test research report"

            # Check citation
            citation_call = mock_crud_document.create.call_args_list[1]
            citation_data = citation_call[1]["obj_in"]
            assert citation_data.filename == "引用文献_1.md"
            assert citation_data.meta_data["document_type"] == "citation"

            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_research_results_no_citations(
        self, deep_research_service, mock_db
    ):
        """测试保存无引用的研究结果."""
        with patch('app.services.deep_research_service.crud_document') as mock_crud_document:
            mock_crud_document.create = AsyncMock(return_value=Mock())

            research_data = {
                "report": "Test research report",
                "summary": "Test summary",
                "citations": []
            }

            await deep_research_service._save_research_results(
                db=mock_db,
                space_id=1,
                user_id=1,
                research_data=research_data,
                query="test query"
            )

            # Only main report should be created
            assert mock_crud_document.create.call_count == 1
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_research_results_exception(
        self, deep_research_service, mock_db
    ):
        """测试保存研究结果时的异常."""
        with patch('app.services.deep_research_service.crud_document') as mock_crud_document:
            mock_crud_document.create = AsyncMock(side_effect=Exception("Database error"))

            research_data = {"report": "Test report", "citations": []}

            await deep_research_service._save_research_results(
                db=mock_db,
                space_id=1,
                user_id=1,
                research_data=research_data,
                query="test query"
            )

            mock_db.rollback.assert_called_once()


class TestFormatCitation:
    """测试格式化引用功能."""

    def test_format_citation_complete(self, deep_research_service):
        """测试完整引用格式化."""
        citation = {
            "title": "Test Article",
            "authors": ["John Doe", "Jane Smith"],
            "url": "https://example.com",
            "published_date": "2023-01-01",
            "snippet": "This is a test article",
            "highlights": ["Key point 1", "Key point 2"]
        }

        result = deep_research_service._format_citation(citation)

        assert "# Test Article" in result
        assert "**作者**: John Doe, Jane Smith" in result
        assert "**链接**: [https://example.com](https://example.com)" in result
        assert "**发表时间**: 2023-01-01" in result
        assert "## 摘要" in result
        assert "This is a test article" in result
        assert "## 关键内容" in result
        assert "- Key point 1" in result
        assert "- Key point 2" in result

    def test_format_citation_minimal(self, deep_research_service):
        """测试最小引用格式化."""
        citation = {}

        result = deep_research_service._format_citation(citation)

        assert "# 未知标题" in result
        assert "**作者**" not in result
        assert "**链接**" not in result
        assert "**发表时间**" not in result
        assert "## 摘要" not in result
        assert "## 关键内容" not in result

    def test_format_citation_partial(self, deep_research_service):
        """测试部分字段的引用格式化."""
        citation = {
            "title": "Partial Citation",
            "url": "https://example.com",
            "snippet": "Only some fields"
        }

        result = deep_research_service._format_citation(citation)

        assert "# Partial Citation" in result
        assert "**链接**: [https://example.com](https://example.com)" in result
        assert "## 摘要" in result
        assert "Only some fields" in result
        assert "**作者**" not in result
        assert "**发表时间**" not in result
        assert "## 关键内容" not in result


class TestStreamResearch:
    """测试流式研究功能."""

    @pytest.mark.asyncio
    async def test_stream_research_no_api_key(self):
        """测试无API密钥的流式研究."""
        with patch('app.services.deep_research_service.settings') as mock_settings:
            mock_settings.PERPLEXITY_API_KEY = None
            service = DeepResearchService()

            results = []
            async for chunk in service.stream_research("test query"):
                results.append(chunk)

            assert len(results) == 1
            data = json.loads(results[0])
            assert data["error"] == "Deep Research功能未配置"

    @pytest.mark.asyncio
    async def test_stream_research_success(
        self, deep_research_service, mock_user, mock_db, mock_space
    ):
        """测试成功的流式研究."""
        with patch('httpx.AsyncClient') as MockClient, \
             patch('app.services.deep_research_service.crud_space') as mock_crud_space:

            # Mock space creation
            mock_crud_space.create = AsyncMock(return_value=mock_space)

            # Mock HTTP client
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # Mock stream response
            mock_response = Mock()

            async def mock_aiter_lines():
                yield "data: {\"type\": \"progress\", \"content\": \"Searching...\", \"progress\": 50}"
                yield "data: {\"type\": \"result\", \"content\": \"Found results\", \"progress\": 100}"
                yield "data: [DONE]"

            mock_response.aiter_lines = mock_aiter_lines
            mock_client.stream.return_value.__aenter__.return_value = mock_response

            results = []
            async for chunk in deep_research_service.stream_research(
                "test query",
                user=mock_user,
                db=mock_db
            ):
                results.append(json.loads(chunk))

            assert len(results) == 3

            # Check space creation message
            assert results[0]["type"] == "space_created"
            assert results[0]["space_id"] == 1

            # Check progress updates
            assert results[1]["type"] == "progress"
            assert results[1]["progress"] == 50

            # Check completion
            assert results[2]["type"] == "completed"

    @pytest.mark.asyncio
    async def test_stream_research_no_user(self, deep_research_service):
        """测试无用户的流式研究."""
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # Mock stream response
            mock_response = Mock()

            async def mock_aiter_lines():
                yield "data: [DONE]"

            mock_response.aiter_lines = mock_aiter_lines
            mock_client.stream.return_value.__aenter__.return_value = mock_response

            results = []
            async for chunk in deep_research_service.stream_research("test query"):
                results.append(json.loads(chunk))

            # Should only get completion message (no space creation)
            assert len(results) == 1
            assert results[0]["type"] == "completed"

    @pytest.mark.asyncio
    async def test_stream_research_invalid_json(self, deep_research_service):
        """测试流式研究中的无效JSON."""
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # Mock stream response
            mock_response = Mock()

            async def mock_aiter_lines():
                yield "data: invalid json"
                yield "data: {\"type\": \"progress\", \"content\": \"Valid\"}"
                yield "data: [DONE]"

            mock_response.aiter_lines = mock_aiter_lines
            mock_client.stream.return_value.__aenter__.return_value = mock_response

            results = []
            async for chunk in deep_research_service.stream_research("test query"):
                results.append(json.loads(chunk))

            # Should skip invalid JSON and only get valid ones
            assert len(results) == 2
            assert results[0]["type"] == "progress"
            assert results[1]["type"] == "completed"

    @pytest.mark.asyncio
    async def test_stream_research_exception(self, deep_research_service):
        """测试流式研究异常."""
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client
            mock_client.stream.side_effect = Exception("Network error")

            results = []
            async for chunk in deep_research_service.stream_research("test query"):
                results.append(json.loads(chunk))

            assert len(results) == 1
            assert results[0]["error"] == "研究失败"
            assert results[0]["message"] == "Network error"


class TestInitialization:
    """测试初始化功能."""

    def test_init_with_api_key(self):
        """测试带API密钥的初始化."""
        with patch('app.services.deep_research_service.settings') as mock_settings:
            mock_settings.PERPLEXITY_API_KEY = "test_key"
            mock_settings.PERPLEXITY_BASE_URL = "https://api.perplexity.ai"

            service = DeepResearchService()

            assert service.api_key == "test_key"
            assert service.base_url == "https://api.perplexity.ai"
            assert service.headers["Authorization"] == "Bearer test_key"
            assert service.headers["Content-Type"] == "application/json"

    def test_init_without_api_key(self):
        """测试无API密钥的初始化."""
        with patch('app.services.deep_research_service.settings') as mock_settings:
            mock_settings.PERPLEXITY_API_KEY = None
            mock_settings.PERPLEXITY_BASE_URL = "https://api.perplexity.ai"

            service = DeepResearchService()

            assert service.api_key is None
            assert service.headers["Authorization"] == "Bearer None"


class TestGlobalInstance:
    """测试全局实例."""

    def test_global_instance_exists(self):
        """测试全局实例存在."""
        from app.services.deep_research_service import deep_research_service

        assert isinstance(deep_research_service, DeepResearchService)
        assert hasattr(deep_research_service, 'create_research')
        assert hasattr(deep_research_service, 'stream_research')
