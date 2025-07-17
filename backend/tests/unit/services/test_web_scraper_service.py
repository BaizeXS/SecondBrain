"""Unit tests for Web Scraper Service."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from bs4 import BeautifulSoup

from app.services.web_scraper_service import WebScraperService


@pytest.fixture
def web_scraper_service():
    """创建网页抓取服务实例."""
    return WebScraperService()


@pytest.fixture
def sample_html():
    """示例HTML内容."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <meta name="description" content="This is a test page for web scraping">
        <meta name="keywords" content="test, web, scraping">
        <meta name="author" content="Test Author">
        <meta property="og:title" content="Test OG Title">
        <meta property="og:description" content="Test OG Description">
        <meta property="og:image" content="https://example.com/image.jpg">
        <meta property="article:published_time" content="2023-01-01T10:00:00Z">
    </head>
    <body>
        <header>
            <nav>Navigation</nav>
        </header>
        <main>
            <article>
                <h1>Main Article Title</h1>
                <p>This is the main content of the article.</p>
                <p>Another paragraph with more content.</p>
                <ul>
                    <li>List item 1</li>
                    <li>List item 2</li>
                </ul>
                <blockquote>This is a quote</blockquote>
            </article>
        </main>
        <footer>
            <p>Footer content</p>
        </footer>
        <script>console.log('test');</script>
        <style>body { margin: 0; }</style>
    </body>
    </html>
    """


@pytest.fixture
def mock_response_success(sample_html):
    """模拟成功的HTTP响应."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = sample_html
    mock_response.raise_for_status = Mock()
    return mock_response


@pytest.fixture
def mock_response_error():
    """模拟错误的HTTP响应."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    return mock_response


class TestFetchWebpage:
    """测试网页抓取功能."""

    @pytest.mark.asyncio
    async def test_fetch_webpage_success(
        self, web_scraper_service, mock_response_success
    ):
        """测试成功抓取网页."""
        test_url = "https://example.com/test"

        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response_success

            result = await web_scraper_service.fetch_webpage(test_url)

            assert result["status"] == "success"
            assert result["url"] == test_url
            assert result["title"] == "Test Page"
            assert "Main Article Title" in result["content"]
            assert "fetched_at" in result
            assert result["metadata"]["domain"] == "example.com"
            assert result["metadata"]["description"] == "This is a test page for web scraping"
            assert result["metadata"]["keywords"] == "test, web, scraping"
            assert result["metadata"]["author"] == "Test Author"
            assert result["metadata"]["og_title"] == "Test OG Title"
            assert result["metadata"]["og_description"] == "Test OG Description"
            assert result["metadata"]["og_image"] == "https://example.com/image.jpg"
            assert result["metadata"]["published_time"] == "2023-01-01T10:00:00Z"

    @pytest.mark.asyncio
    async def test_fetch_webpage_http_error(
        self, web_scraper_service, mock_response_error
    ):
        """测试HTTP错误处理."""
        test_url = "https://example.com/notfound"

        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # 模拟HTTP错误
            error = httpx.HTTPStatusError("404 Not Found", request=Mock(), response=mock_response_error)
            mock_client.get.side_effect = error

            result = await web_scraper_service.fetch_webpage(test_url)

            assert result["status"] == "error"
            assert result["url"] == test_url
            assert "HTTP 404" in result["error"]
            assert "fetched_at" in result

    @pytest.mark.asyncio
    async def test_fetch_webpage_timeout(self, web_scraper_service):
        """测试超时错误处理."""
        test_url = "https://example.com/timeout"

        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")

            result = await web_scraper_service.fetch_webpage(test_url)

            assert result["status"] == "error"
            assert result["url"] == test_url
            assert "Timeout" in result["error"]
            assert "fetched_at" in result

    @pytest.mark.asyncio
    async def test_fetch_webpage_general_exception(self, web_scraper_service):
        """测试一般异常处理."""
        test_url = "https://example.com/error"

        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = Exception("Network error")

            result = await web_scraper_service.fetch_webpage(test_url)

            assert result["status"] == "error"
            assert result["url"] == test_url
            assert result["error"] == "Network error"
            assert "fetched_at" in result


class TestExtractMetadata:
    """测试元数据提取功能."""

    def test_extract_metadata_complete(self, web_scraper_service, sample_html):
        """测试完整元数据提取."""
        soup = BeautifulSoup(sample_html, "html.parser")
        test_url = "https://example.com/test"

        metadata = web_scraper_service._extract_metadata(soup, test_url)

        assert metadata["url"] == test_url
        assert metadata["domain"] == "example.com"
        assert metadata["title"] == "Test Page"
        assert metadata["description"] == "This is a test page for web scraping"
        assert metadata["keywords"] == "test, web, scraping"
        assert metadata["author"] == "Test Author"
        assert metadata["og_title"] == "Test OG Title"
        assert metadata["og_description"] == "Test OG Description"
        assert metadata["og_image"] == "https://example.com/image.jpg"
        assert metadata["published_time"] == "2023-01-01T10:00:00Z"
        assert "fetched_at" in metadata

    def test_extract_metadata_minimal(self, web_scraper_service):
        """测试最小元数据提取."""
        minimal_html = "<html><head></head><body></body></html>"
        soup = BeautifulSoup(minimal_html, "html.parser")
        test_url = "https://example.com/minimal"

        metadata = web_scraper_service._extract_metadata(soup, test_url)

        assert metadata["url"] == test_url
        assert metadata["domain"] == "example.com"
        assert metadata["title"] == "example.com"  # 应该使用域名作为标题
        assert "fetched_at" in metadata
        # 其他字段应该不存在
        assert "description" not in metadata
        assert "keywords" not in metadata
        assert "author" not in metadata

    def test_extract_metadata_with_title_only(self, web_scraper_service):
        """测试只有标题的元数据提取."""
        html = "<html><head><title>Only Title</title></head><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        test_url = "https://example.com/title"

        metadata = web_scraper_service._extract_metadata(soup, test_url)

        assert metadata["title"] == "Only Title"
        assert metadata["domain"] == "example.com"

    def test_extract_metadata_empty_content(self, web_scraper_service):
        """测试空内容的元数据提取."""
        html = """
        <html>
        <head>
            <meta name="description" content="">
            <meta name="keywords" content="">
            <meta name="author" content="">
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        test_url = "https://example.com/empty"

        metadata = web_scraper_service._extract_metadata(soup, test_url)

        # 空内容应该不被添加到元数据中
        assert "description" not in metadata
        assert "keywords" not in metadata
        assert "author" not in metadata


class TestExtractContent:
    """测试内容提取功能."""

    def test_extract_content_from_main(self, web_scraper_service, sample_html):
        """测试从main标签提取内容."""
        soup = BeautifulSoup(sample_html, "html.parser")

        content = web_scraper_service._extract_content(soup)

        assert "Main Article Title" in content
        assert "This is the main content of the article." in content
        assert "Another paragraph with more content." in content
        assert "List item 1" in content
        assert "List item 2" in content
        assert "This is a quote" in content
        # 不应该包含脚本和样式
        assert "console.log" not in content
        assert "margin: 0" not in content
        # 不应该包含导航和页脚
        assert "Navigation" not in content
        assert "Footer content" not in content

    def test_extract_content_from_article(self, web_scraper_service):
        """测试从article标签提取内容."""
        html = """
        <html>
        <body>
            <div>Other content</div>
            <article>
                <h1>Article Title</h1>
                <p>Article content</p>
            </article>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        content = web_scraper_service._extract_content(soup)

        assert "Article Title" in content
        assert "Article content" in content
        assert "Other content" not in content

    def test_extract_content_fallback_to_body(self, web_scraper_service):
        """测试回退到body标签."""
        html = """
        <html>
        <body>
            <div>
                <h1>Title</h1>
                <p>Content paragraph</p>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        content = web_scraper_service._extract_content(soup)

        assert "Title" in content
        assert "Content paragraph" in content

    def test_extract_content_with_scripts_and_styles(self, web_scraper_service):
        """测试移除脚本和样式."""
        html = """
        <html>
        <body>
            <p>Visible content</p>
            <script>alert('test');</script>
            <style>body { color: red; }</style>
            <p>More visible content</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        content = web_scraper_service._extract_content(soup)

        assert "Visible content" in content
        assert "More visible content" in content
        assert "alert('test')" not in content
        assert "color: red" not in content


class TestCleanText:
    """测试文本清理功能."""

    def test_clean_text_basic(self, web_scraper_service):
        """测试基本文本清理."""
        dirty_text = "  Line 1  \n\n  Line 2  \n\n\n  Line 3  \n  "

        cleaned = web_scraper_service._clean_text(dirty_text)

        assert cleaned == "Line 1\n\nLine 2\n\nLine 3"

    def test_clean_text_empty_lines(self, web_scraper_service):
        """测试移除空行."""
        text = "Line 1\n\n\n\nLine 2\n\n\n\nLine 3"

        cleaned = web_scraper_service._clean_text(text)

        assert cleaned == "Line 1\n\nLine 2\n\nLine 3"

    def test_clean_text_max_length(self, web_scraper_service):
        """测试最大长度限制."""
        long_text = "A" * 60000  # 超过50k限制

        cleaned = web_scraper_service._clean_text(long_text)

        assert len(cleaned) == 50003  # 50000 + "..."
        assert cleaned.endswith("...")

    def test_clean_text_empty(self, web_scraper_service):
        """测试空文本."""
        cleaned = web_scraper_service._clean_text("")
        assert cleaned == ""

    def test_clean_text_whitespace_only(self, web_scraper_service):
        """测试只有空白的文本."""
        text = "   \n\n  \n  \n   "

        cleaned = web_scraper_service._clean_text(text)

        assert cleaned == ""


class TestFetchMultipleUrls:
    """测试批量抓取功能."""

    @pytest.mark.asyncio
    async def test_fetch_multiple_urls_success(self, web_scraper_service):
        """测试成功批量抓取."""
        urls = ["https://example.com/1", "https://example.com/2"]

        with patch.object(web_scraper_service, 'fetch_webpage') as mock_fetch:
            mock_fetch.side_effect = [
                {"url": urls[0], "status": "success", "title": "Page 1"},
                {"url": urls[1], "status": "success", "title": "Page 2"},
            ]

            results = await web_scraper_service.fetch_multiple_urls(urls)

            assert len(results) == 2
            assert results[0]["url"] == urls[0]
            assert results[0]["title"] == "Page 1"
            assert results[1]["url"] == urls[1]
            assert results[1]["title"] == "Page 2"
            assert mock_fetch.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_multiple_urls_empty(self, web_scraper_service):
        """测试空URL列表."""
        results = await web_scraper_service.fetch_multiple_urls([])
        assert results == []

    @pytest.mark.asyncio
    async def test_fetch_multiple_urls_with_errors(self, web_scraper_service):
        """测试包含错误的批量抓取."""
        urls = ["https://example.com/success", "https://example.com/error"]

        with patch.object(web_scraper_service, 'fetch_webpage') as mock_fetch:
            mock_fetch.side_effect = [
                {"url": urls[0], "status": "success", "title": "Success"},
                {"url": urls[1], "status": "error", "error": "404 Not Found"},
            ]

            results = await web_scraper_service.fetch_multiple_urls(urls)

            assert len(results) == 2
            assert results[0]["status"] == "success"
            assert results[1]["status"] == "error"


class TestExtractLinks:
    """测试链接提取功能."""

    def test_extract_links_absolute(self, web_scraper_service):
        """测试提取绝对链接."""
        html = """
        <div>
            <a href="https://example.com/page1">Link 1</a>
            <a href="https://example.com/page2">Link 2</a>
            <a href="https://other.com/page">External Link</a>
        </div>
        """
        base_url = "https://example.com"

        links = web_scraper_service.extract_links(html, base_url)

        assert "https://example.com/page1" in links
        assert "https://example.com/page2" in links
        assert "https://other.com/page" in links
        assert len(links) == 3

    def test_extract_links_relative(self, web_scraper_service):
        """测试提取相对链接."""
        html = """
        <div>
            <a href="/page1">Relative Link 1</a>
            <a href="/page2">Relative Link 2</a>
            <a href="relative">Relative without slash</a>
        </div>
        """
        base_url = "https://example.com"

        links = web_scraper_service.extract_links(html, base_url)

        assert "https://example.com/page1" in links
        assert "https://example.com/page2" in links
        assert len(links) == 2  # 不以/开头的相对链接会被忽略

    def test_extract_links_mixed(self, web_scraper_service):
        """测试混合链接提取."""
        html = """
        <div>
            <a href="https://example.com/absolute">Absolute</a>
            <a href="/relative">Relative</a>
            <a href="mailto:test@example.com">Email</a>
            <a href="javascript:void(0)">JavaScript</a>
        </div>
        """
        base_url = "https://example.com"

        links = web_scraper_service.extract_links(html, base_url)

        assert "https://example.com/absolute" in links
        assert "https://example.com/relative" in links
        # 其他类型的链接应该被忽略
        assert len(links) == 2

    def test_extract_links_deduplication(self, web_scraper_service):
        """测试链接去重."""
        html = """
        <div>
            <a href="https://example.com/page">Link 1</a>
            <a href="https://example.com/page">Link 2</a>
            <a href="/page">Link 3</a>
        </div>
        """
        base_url = "https://example.com"

        links = web_scraper_service.extract_links(html, base_url)

        # 应该只有一个链接（去重后）
        assert len(links) == 1
        assert "https://example.com/page" in links

    def test_extract_links_no_links(self, web_scraper_service):
        """测试没有链接的HTML."""
        html = "<div>No links here</div>"
        base_url = "https://example.com"

        links = web_scraper_service.extract_links(html, base_url)

        assert links == []

    def test_extract_links_empty_href(self, web_scraper_service):
        """测试空href的链接."""
        html = """
        <div>
            <a href="">Empty href</a>
            <a href="https://example.com/valid">Valid link</a>
            <a>No href attribute</a>
        </div>
        """
        base_url = "https://example.com"

        links = web_scraper_service.extract_links(html, base_url)

        assert len(links) == 1
        assert "https://example.com/valid" in links


class TestConvertToMarkdown:
    """测试HTML转Markdown功能."""

    def test_convert_to_markdown_headings(self, web_scraper_service):
        """测试标题转换."""
        html = """
        <h1>Heading 1</h1>
        <h2>Heading 2</h2>
        <h3>Heading 3</h3>
        <h4>Heading 4</h4>
        <h5>Heading 5</h5>
        <h6>Heading 6</h6>
        """

        markdown = web_scraper_service.convert_to_markdown(html)

        assert "# Heading 1" in markdown
        assert "## Heading 2" in markdown
        assert "### Heading 3" in markdown
        assert "#### Heading 4" in markdown
        assert "##### Heading 5" in markdown
        assert "###### Heading 6" in markdown

    def test_convert_to_markdown_paragraphs(self, web_scraper_service):
        """测试段落转换."""
        html = """
        <p>First paragraph</p>
        <p>Second paragraph</p>
        <p></p>
        <p>   </p>
        <p>Third paragraph</p>
        """

        markdown = web_scraper_service.convert_to_markdown(html)

        assert "First paragraph" in markdown
        assert "Second paragraph" in markdown
        assert "Third paragraph" in markdown
        # 空段落应该被忽略
        lines = [line.strip() for line in markdown.split('\n') if line.strip()]
        assert len(lines) == 3

    def test_convert_to_markdown_lists(self, web_scraper_service):
        """测试列表转换."""
        html = """
        <ul>
            <li>Unordered item 1</li>
            <li>Unordered item 2</li>
        </ul>
        <ol>
            <li>Ordered item 1</li>
            <li>Ordered item 2</li>
        </ol>
        """

        markdown = web_scraper_service.convert_to_markdown(html)

        assert "- Unordered item 1" in markdown
        assert "- Unordered item 2" in markdown
        assert "1. Ordered item 1" in markdown
        assert "1. Ordered item 2" in markdown

    def test_convert_to_markdown_blockquotes(self, web_scraper_service):
        """测试引用转换."""
        html = """
        <blockquote>
            This is a quote
            with multiple lines
        </blockquote>
        """

        markdown = web_scraper_service.convert_to_markdown(html)

        assert "> This is a quote" in markdown
        assert "> with multiple lines" in markdown

    def test_convert_to_markdown_mixed(self, web_scraper_service):
        """测试混合内容转换."""
        html = """
        <h1>Title</h1>
        <p>Introduction paragraph</p>
        <ul>
            <li>List item</li>
        </ul>
        <blockquote>Quote text</blockquote>
        <p>Final paragraph</p>
        """

        markdown = web_scraper_service.convert_to_markdown(html)

        assert "# Title" in markdown
        assert "Introduction paragraph" in markdown
        assert "- List item" in markdown
        assert "> Quote text" in markdown
        assert "Final paragraph" in markdown

    def test_convert_to_markdown_empty(self, web_scraper_service):
        """测试空HTML转换."""
        html = "<div></div>"

        markdown = web_scraper_service.convert_to_markdown(html)

        assert markdown.strip() == ""

    def test_convert_to_markdown_invalid_heading(self, web_scraper_service):
        """测试无效标题处理."""
        html = """
        <h1>Valid heading</h1>
        <hx>Invalid heading</hx>
        <h>No number</h>
        """

        markdown = web_scraper_service.convert_to_markdown(html)

        assert "# Valid heading" in markdown
        # 无效标题应该被忽略
        assert "Invalid heading" not in markdown
        assert "No number" not in markdown


class TestGlobalInstance:
    """测试全局实例."""

    def test_global_instance_exists(self):
        """测试全局实例存在."""
        from app.services.web_scraper_service import web_scraper_service

        assert isinstance(web_scraper_service, WebScraperService)
        assert hasattr(web_scraper_service, 'fetch_webpage')
        assert hasattr(web_scraper_service, 'extract_links')
        assert hasattr(web_scraper_service, 'convert_to_markdown')


class TestInitialization:
    """测试初始化功能."""

    def test_initialization(self):
        """测试服务初始化."""
        service = WebScraperService()

        assert service.headers["User-Agent"].startswith("Mozilla/5.0")
        assert service.timeout == 30.0
