"""Web scraping service for URL import and webpage snapshots."""

import logging
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

logger = logging.getLogger(__name__)


class WebScraperService:
    """网页抓取服务."""

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.timeout = 30.0

    async def fetch_webpage(self, url: str) -> dict[str, Any]:
        """抓取网页内容."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    follow_redirects=True
                )
                response.raise_for_status()

                # 解析HTML
                soup = BeautifulSoup(response.text, "html.parser")

                # 提取元数据
                metadata = self._extract_metadata(soup, url)

                # 提取主要内容
                content = self._extract_content(soup)

                # 获取页面快照
                snapshot_html = str(soup)

                return {
                    "url": url,
                    "title": metadata["title"],
                    "content": content,
                    "metadata": metadata,
                    "snapshot_html": snapshot_html,
                    "fetched_at": datetime.now().isoformat(),
                    "status": "success"
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            return {
                "url": url,
                "status": "error",
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                "fetched_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return {
                "url": url,
                "status": "error",
                "error": str(e),
                "fetched_at": datetime.now().isoformat()
            }

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> dict[str, Any]:
        """提取网页元数据."""
        metadata = {
            "url": url,
            "domain": urlparse(url).netloc,
            "fetched_at": datetime.now().isoformat()
        }

        # 标题
        title_tag = soup.find("title")
        metadata["title"] = title_tag.text.strip() if title_tag else urlparse(url).netloc

        # 描述
        description_tag = soup.find("meta", attrs={"name": "description"})
        if isinstance(description_tag, Tag):
            content = description_tag.get("content")
            if content:
                metadata["description"] = str(content).strip()

        # 关键词
        keywords_tag = soup.find("meta", attrs={"name": "keywords"})
        if isinstance(keywords_tag, Tag):
            content = keywords_tag.get("content")
            if content:
                metadata["keywords"] = str(content).strip()

        # 作者
        author_tag = soup.find("meta", attrs={"name": "author"})
        if isinstance(author_tag, Tag):
            content = author_tag.get("content")
            if content:
                metadata["author"] = str(content).strip()

        # Open Graph 数据
        og_title = soup.find("meta", property="og:title")
        if isinstance(og_title, Tag):
            content = og_title.get("content")
            if content:
                metadata["og_title"] = str(content).strip()

        og_description = soup.find("meta", property="og:description")
        if isinstance(og_description, Tag):
            content = og_description.get("content")
            if content:
                metadata["og_description"] = str(content).strip()

        og_image = soup.find("meta", property="og:image")
        if isinstance(og_image, Tag):
            content = og_image.get("content")
            if content:
                metadata["og_image"] = str(content).strip()

        # 发布时间
        published_time = soup.find("meta", property="article:published_time")
        if isinstance(published_time, Tag):
            content = published_time.get("content")
            if content:
                metadata["published_time"] = str(content).strip()

        return metadata

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取网页主要内容."""
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()

        # 尝试查找主要内容区域
        content_areas = [
            soup.find("main"),
            soup.find("article"),
            soup.find("div", class_="content"),
            soup.find("div", class_="main"),
            soup.find("div", id="content"),
            soup.find("div", id="main"),
        ]

        for area in content_areas:
            if area:
                return self._clean_text(area.get_text())

        # 如果找不到特定区域，提取body内容
        body = soup.find("body")
        if body:
            return self._clean_text(body.get_text())

        # 最后尝试提取所有文本
        return self._clean_text(soup.get_text())

    def _clean_text(self, text: str) -> str:
        """清理文本内容."""
        # 移除多余的空白
        lines = [line.strip() for line in text.splitlines()]
        lines = [line for line in lines if line]

        # 合并段落
        cleaned = "\n\n".join(lines)

        # 限制长度
        max_length = 50000  # 最多50k字符
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length] + "..."

        return cleaned

    async def fetch_multiple_urls(self, urls: list[str]) -> list[dict[str, Any]]:
        """批量抓取多个URL."""
        results = []
        for url in urls:
            result = await self.fetch_webpage(url)
            results.append(result)
        return results

    def extract_links(self, html_content: str, base_url: str) -> list[str]:
        """从HTML中提取所有链接."""
        soup = BeautifulSoup(html_content, "html.parser")
        links = []

        for link in soup.find_all("a", href=True):
            if isinstance(link, Tag):
                href = link.get("href")
                if href and isinstance(href, str):
                    # 转换相对URL为绝对URL
                    if href.startswith("http"):
                        links.append(href)
                    elif href.startswith("/"):
                        parsed = urlparse(base_url)
                        links.append(f"{parsed.scheme}://{parsed.netloc}{href}")

        # 去重并过滤空字符串
        return list({link for link in links if link})

    def convert_to_markdown(self, html_content: str) -> str:
        """将HTML转换为Markdown格式."""
        soup = BeautifulSoup(html_content, "html.parser")

        # 简单的HTML到Markdown转换
        markdown_lines = []

        for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "blockquote"]):
            if isinstance(element, Tag) and element.name:
                element_name = str(element.name)
                if element_name.startswith("h") and len(element_name) > 1:
                    try:
                        level = int(element_name[1])
                        markdown_lines.append(f"{'#' * level} {element.get_text().strip()}")
                    except (ValueError, IndexError):
                        pass
                elif element_name == "p":
                    text = element.get_text().strip()
                    if text:
                        markdown_lines.append(text)
                elif element_name in ["ul", "ol"]:
                    for li in element.find_all("li"):
                        prefix = "-" if element_name == "ul" else "1."
                        markdown_lines.append(f"{prefix} {li.get_text().strip()}")
                elif element_name == "blockquote":
                    quote_text = element.get_text().strip()
                    for line in quote_text.split("\n"):
                        line = line.strip()
                        if line:
                            markdown_lines.append(f"> {line}")

                markdown_lines.append("")  # 添加空行

        return "\n".join(markdown_lines)


# 创建全局实例
web_scraper_service = WebScraperService()
