"""Unit tests for Search Service."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.models.models import User
from app.schemas.conversations import SearchResponse, SearchResult
from app.services.search_service import SearchService


@pytest.fixture
def search_service():
    """创建搜索服务实例."""
    service = SearchService()
    service.perplexity_api_key = "test-api-key"  # 设置测试API密钥
    return service


@pytest.fixture
def mock_user():
    """创建模拟用户."""
    user = Mock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_perplexity_response():
    """创建模拟的 Perplexity API 响应."""
    return {
        "choices": [
            {
                "message": {
                    "content": "这是关于搜索查询的详细回答内容。"
                }
            }
        ],
        "citations": [
            {
                "title": "搜索结果标题 1",
                "url": "https://example.com/result1",
                "snippet": "这是第一个搜索结果的摘要内容。"
            },
            {
                "title": "搜索结果标题 2",
                "url": "https://example.com/result2",
                "snippet": "这是第二个搜索结果的摘要内容。"
            }
        ]
    }


class TestSearch:
    """测试搜索功能."""

    @pytest.mark.asyncio
    async def test_search_with_api_key(self, search_service, mock_user, mock_perplexity_response):
        """测试有 API 密钥时的搜索."""
        # Mock API 调用
        with patch('app.services.search_service.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json = Mock(return_value=mock_perplexity_response)

            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            # 执行搜索
            result = await search_service.search(
                query="Python 编程",
                search_scope="web",
                max_results=10,
                include_summary=True,
                user=mock_user
            )

            # 验证结果
            assert isinstance(result, SearchResponse)
            assert result.query == "Python 编程"
            assert len(result.results) == 2  # mock响应中有2个citations
            assert result.total_results == 2
            assert result.summary is not None
            assert "Python 编程" in result.summary
            assert result.search_time > 0

            # 验证 API 调用
            mock_client_instance.post.assert_called_once()
            call_args = mock_client_instance.post.call_args
            assert call_args[0][0] == "https://api.perplexity.ai/chat/completions"

    @pytest.mark.asyncio
    async def test_search_without_api_key(self, search_service, mock_user):
        """测试没有 API 密钥时返回模拟结果."""
        # 设置无 API 密钥
        search_service.perplexity_api_key = None

        # 执行搜索
        result = await search_service.search(
            query="测试查询",
            search_scope="web",
            max_results=3,
            include_summary=True,
            user=mock_user
        )

        # 验证返回模拟结果
        assert isinstance(result, SearchResponse)
        assert result.query == "测试查询"
        assert len(result.results) == 3
        assert all(r.source == "mock" for r in result.results)
        assert result.summary is not None

    @pytest.mark.asyncio
    async def test_search_api_failure(self, search_service, mock_user):
        """测试 API 调用失败时的处理."""
        # Mock API 调用失败
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500

            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            # 执行搜索
            result = await search_service.search(
                query="测试查询",
                search_scope="web",
                max_results=5,
                include_summary=True,
                user=mock_user
            )

            # 验证返回模拟结果
            assert isinstance(result, SearchResponse)
            assert len(result.results) == 5
            assert all(r.source == "mock" for r in result.results)

    @pytest.mark.asyncio
    async def test_search_exception_handling(self, search_service, mock_user):
        """测试搜索过程中出现异常的处理."""
        # Mock _perplexity_search 方法抛出异常
        with patch.object(search_service, '_perplexity_search', side_effect=Exception("网络错误")):
            # 执行搜索
            result = await search_service.search(
                query="测试查询",
                search_scope="web",
                max_results=5,
                include_summary=True,
                user=mock_user
            )

            # 验证返回空结果
            assert isinstance(result, SearchResponse)
            assert len(result.results) == 0
            assert result.total_results == 0
            assert result.summary is not None and "搜索失败" in result.summary

    @pytest.mark.asyncio
    async def test_search_without_summary(self, search_service, mock_user):
        """测试不包含摘要的搜索."""
        # 设置无 API 密钥以使用模拟结果
        search_service.perplexity_api_key = None

        # 执行搜索，不包含摘要
        result = await search_service.search(
            query="测试查询",
            search_scope="web",
            max_results=3,
            include_summary=False,
            user=mock_user
        )

        # 验证结果
        assert result.summary is None
        assert len(result.results) == 3


class TestPerplexitySearch:
    """测试 Perplexity API 搜索功能."""

    @pytest.mark.asyncio
    async def test_perplexity_search_different_scopes(self, search_service):
        """测试不同搜索范围."""
        # 设置无 API 密钥以测试模拟结果
        search_service.perplexity_api_key = None

        for scope in ["web", "academic", "news", "unknown"]:
            results = await search_service._perplexity_search(
                query="测试",
                search_scope=scope,
                max_results=3
            )

            assert len(results) == 3
            assert all(isinstance(r, SearchResult) for r in results)

    @pytest.mark.asyncio
    async def test_perplexity_search_http_exception(self, search_service):
        """测试 HTTP 请求异常时的处理."""
        # 设置 API 密钥以进入 HTTP 请求逻辑
        search_service.perplexity_api_key = "test_key"

        # Mock httpx.AsyncClient 抛出异常
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(side_effect=Exception("Connection error"))
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            # 执行搜索
            results = await search_service._perplexity_search(
                query="测试查询",
                search_scope="web",
                max_results=3
            )

            # 验证返回模拟结果
            assert len(results) == 3
            assert all(isinstance(r, SearchResult) for r in results)
            assert all(r.source == "mock" for r in results)


class TestParsePerplexityResponse:
    """测试解析 Perplexity 响应功能."""

    def test_parse_normal_response(self, search_service, mock_perplexity_response):
        """测试解析正常响应."""
        results = search_service._parse_perplexity_response(
            mock_perplexity_response,
            "测试查询"
        )

        assert len(results) == 2
        assert results[0].title == "搜索结果标题 1"
        assert results[0].url == "https://example.com/result1"
        assert results[0].snippet == "这是第一个搜索结果的摘要内容。"
        assert results[0].score == 1.0
        assert results[0].source == "perplexity"

        assert results[1].score == 0.9  # 第二个结果分数降低

    def test_parse_empty_response(self, search_service):
        """测试解析空响应."""
        results = search_service._parse_perplexity_response(
            {},
            "测试查询"
        )

        # 空响应会导致解析 citations 失败，返回空列表
        assert len(results) == 0

    def test_parse_malformed_response(self, search_service):
        """测试解析格式错误的响应."""
        malformed_response = {
            "choices": [{"wrong_key": "value"}]
        }

        results = search_service._parse_perplexity_response(
            malformed_response,
            "测试查询"
        )

        # 格式错误会导致解析 citations 失败，返回空列表
        assert len(results) == 0

    def test_parse_response_with_exception(self, search_service):
        """测试解析响应时触发异常处理分支."""
        # 创建一个会触发异常的响应
        response_with_content = {
            "choices": [
                {
                    "message": {
                        "content": "这是响应内容"
                    }
                }
            ],
            # 故意让 citations 为非列表类型来触发异常
            "citations": "invalid_type"
        }

        # Mock _parse_perplexity_response 的内部逻辑，强制触发 except 分支
        with patch('app.schemas.conversations.SearchResult') as mock_search_result:
            # 第一次调用抛出异常，触发 except 分支
            mock_search_result.side_effect = [Exception("Test exception"), Mock()]

            results = search_service._parse_perplexity_response(
                response_with_content,
                "测试查询"
            )

            # 在 except 分支中会创建一个基本结果
            assert len(results) == 1


class TestMockSearchResults:
    """测试模拟搜索结果功能."""

    def test_mock_search_results(self, search_service):
        """测试生成模拟搜索结果."""
        results = search_service._mock_search_results("测试查询", 3)

        assert len(results) == 3
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].score == 1.0
        assert results[1].score == 0.8
        assert results[2].score == 0.6
        assert all(r.source == "mock" for r in results)
        assert all("测试查询" in r.title for r in results)

    def test_mock_search_results_max_limit(self, search_service):
        """测试模拟结果的最大数量限制."""
        results = search_service._mock_search_results("测试", 10)

        assert len(results) == 5  # 最多返回5个模拟结果


class TestGenerateSummary:
    """测试生成摘要功能."""

    @pytest.mark.asyncio
    async def test_generate_summary_with_results(self, search_service):
        """测试有结果时生成摘要."""
        results = [
            SearchResult(
                title="结果1",
                url="url1",
                snippet="这是第一个结果的摘要",
                score=1.0,
                source="test"
            ),
            SearchResult(
                title="结果2",
                url="url2",
                snippet="这是第二个结果的摘要",
                score=0.9,
                source="test"
            ),
            SearchResult(
                title="结果3",
                url="url3",
                snippet="这是第三个结果的摘要",
                score=0.8,
                source="test"
            ),
            SearchResult(
                title="结果4",
                url="url4",
                snippet="这是第四个结果的摘要",
                score=0.7,
                source="test"
            )
        ]

        summary = await search_service._generate_summary("测试查询", results)

        assert "测试查询" in summary
        assert "1. 这是第一个结果的摘要" in summary
        assert "2. 这是第二个结果的摘要" in summary
        assert "3. 这是第三个结果的摘要" in summary
        assert "这是第四个结果的摘要" not in summary  # 只总结前3个
        assert "共找到 4 个相关结果" in summary

    @pytest.mark.asyncio
    async def test_generate_summary_no_results(self, search_service):
        """测试无结果时生成摘要."""
        summary = await search_service._generate_summary("测试查询", [])

        assert "没有找到关于'测试查询'的相关信息" in summary
