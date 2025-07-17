"""Search service."""

import time
from datetime import datetime
from typing import Any

import httpx

from app.core.config import settings
from app.models.models import User
from app.schemas.conversations import SearchResponse, SearchResult


class SearchService:
    """搜索服务."""

    def __init__(self) -> None:
        self.perplexity_api_key = settings.PERPLEXITY_API_KEY
        self.perplexity_url = "https://api.perplexity.ai/chat/completions"

    async def search(
        self,
        query: str,
        search_scope: str = "web",
        max_results: int = 10,
        include_summary: bool = True,
        user: User | None = None,  # 保留以备将来使用（如用户级别的搜索历史）
    ) -> SearchResponse:
        """执行搜索."""
        _ = user  # 暂时未使用，保留以备将来功能
        start_time = time.time()

        try:
            # 使用Perplexity进行搜索
            results = await self._perplexity_search(
                query=query,
                search_scope=search_scope,
                max_results=max_results,
            )

            # 生成AI总结
            summary = None
            if include_summary and results:
                summary = await self._generate_summary(query, results)

            search_time = time.time() - start_time

            return SearchResponse(
                query=query,
                results=results,
                summary=summary,
                total_results=len(results),
                search_time=search_time,
                sources=[result.source for result in results],
            )

        except Exception as e:
            # 返回空结果而不是抛出异常
            return SearchResponse(
                query=query,
                results=[],
                summary=f"搜索失败: {str(e)}",
                total_results=0,
                search_time=time.time() - start_time,
                sources=[],
            )

    async def _perplexity_search(
        self,
        query: str,
        search_scope: str,
        max_results: int,
    ) -> list[SearchResult]:
        """使用Perplexity API进行搜索."""
        if not self.perplexity_api_key:
            # 模拟搜索结果
            return self._mock_search_results(query, max_results)

        try:
            # 根据搜索范围选择模型
            model_map = {
                "web": "llama-3.1-sonar-small-128k-online",
                "academic": "llama-3.1-sonar-small-128k-online",
                "news": "llama-3.1-sonar-small-128k-online",
            }

            model = model_map.get(search_scope, "llama-3.1-sonar-small-128k-online")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.perplexity_url,
                    headers={
                        "Authorization": f"Bearer {self.perplexity_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": f"You are a helpful search assistant. Please search for information about: {query}. Return structured results with sources.",
                            },
                            {"role": "user", "content": query},
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.1,
                        "return_citations": True,
                        "return_images": False,
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_perplexity_response(data, query)
                else:
                    # 如果API调用失败，返回模拟结果
                    return self._mock_search_results(query, max_results)

        except Exception:
            # 如果出错，返回模拟结果
            return self._mock_search_results(query, max_results)

    def _parse_perplexity_response(
        self, data: dict[str, Any], query: str
    ) -> list[SearchResult]:
        """解析Perplexity API响应."""
        results = []

        try:
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = data.get("citations", [])

            # 基于citations创建搜索结果
            for i, citation in enumerate(citations[:10]):  # 限制最多10个结果
                result = SearchResult(
                    title=citation.get("title", f"搜索结果 {i + 1}"),
                    url=citation.get("url", ""),
                    snippet=citation.get("snippet", ""),
                    content=content if i == 0 else "",  # 只给第一个结果完整内容
                    score=1.0 - i * 0.1,  # 简单的评分机制
                    source="perplexity",
                    published_date=None,
                )
                results.append(result)

        except Exception:
            # 如果解析失败，返回基本结果
            results = [
                SearchResult(
                    title=f"关于'{query}'的搜索结果",
                    url="",
                    snippet=data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")[:200],
                    score=1.0,
                    source="perplexity",
                )
            ]

        return results

    def _mock_search_results(self, query: str, max_results: int) -> list[SearchResult]:
        """生成模拟搜索结果."""
        results = []

        for i in range(min(max_results, 5)):  # 最多5个模拟结果
            result = SearchResult(
                title=f"关于'{query}'的搜索结果 {i + 1}",
                url=f"https://example.com/result{i + 1}",
                snippet=f"这是关于'{query}'的搜索结果片段 {i + 1}。包含相关信息和详细描述。",
                content=f"这是关于'{query}'的详细内容 {i + 1}。" if i == 0 else None,
                score=1.0 - i * 0.2,
                source="mock",
                published_date=datetime.now(),
            )
            results.append(result)

        return results

    async def _generate_summary(self, query: str, results: list[SearchResult]) -> str:
        """生成搜索结果摘要."""
        if not results:
            return f"没有找到关于'{query}'的相关信息。"

        # 简单的摘要生成
        summary_parts = [f"根据搜索结果，关于'{query}'的信息如下："]

        for i, result in enumerate(results[:3]):  # 只总结前3个结果
            if result.snippet:
                summary_parts.append(f"{i + 1}. {result.snippet}")

        summary_parts.append(f"共找到 {len(results)} 个相关结果。")

        return " ".join(summary_parts)
