"""Deep Research Service - 集成Perplexity Deep Research API."""

import json
import logging
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.document import crud_document
from app.crud.space import crud_space
from app.models.models import User
from app.schemas.documents import DocumentCreate
from app.schemas.spaces import SpaceCreate

logger = logging.getLogger(__name__)


class DeepResearchService:
    """Deep Research服务 - 使用Perplexity API进行深度研究."""

    def __init__(self) -> None:
        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = settings.PERPLEXITY_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def create_research(
        self,
        query: str,
        mode: str = "general",  # general 或 academic
        user: User | None = None,
        db: AsyncSession | None = None,
        space_id: int | None = None
    ) -> dict[str, Any]:
        """
        创建深度研究任务.

        Args:
            query: 研究查询
            mode: 研究模式 (general/academic)
            user: 当前用户
            db: 数据库会话
            space_id: 如果提供，将研究结果保存到指定Space；否则创建新Space

        Returns:
            研究结果
        """
        if not self.api_key:
            logger.error("Perplexity API key not configured")
            return {
                "error": "Deep Research功能未配置",
                "message": "请配置PERPLEXITY_API_KEY环境变量"
            }

        try:
            # 创建或获取Space
            if not space_id and user and db:
                # 创建新的研究主题Space
                space_data = SpaceCreate(
                    name=f"研究: {query[:50]}...",
                    description=f"Deep Research自动创建的研究空间 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    is_public=False,
                    icon="🔬" if mode == "academic" else "🔍",
                    color=None,
                    tags=None,
                    meta_data={
                        "research_query": query,
                        "research_mode": mode,
                        "created_by": "deep_research"
                    }
                )
                space = await crud_space.create(db, obj_in=space_data, user_id=user.id)
                space_id = space.id
                await db.commit()

            # 调用Perplexity Deep Research API
            async with httpx.AsyncClient(timeout=300.0) as client:
                request_data = {
                    "query": query,
                    "mode": mode,
                    "return_citations": True,
                    "return_images": False,
                    "search_domain_filter": ["academic"] if mode == "academic" else None,
                    "stream": False
                }

                # 过滤掉None值
                request_data = {k: v for k, v in request_data.items() if v is not None}

                # 使用Perplexity的chat端点进行深度研究
                chat_request = {
                    "model": "sonar",  # 使用在线搜索模型
                    "messages": [
                        {
                            "role": "system",
                            "content": f"You are a research assistant. Provide a {'academic' if mode == 'academic' else 'comprehensive'} research report on the given topic. Include relevant citations and sources."
                        },
                        {
                            "role": "user",
                            "content": query
                        }
                    ],
                    "temperature": 0.7,
                    "return_citations": True
                }

                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=chat_request
                )

                if response.status_code != 200:
                    logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
                    return {
                        "error": "API调用失败",
                        "message": f"状态码: {response.status_code}",
                        "details": response.text
                    }

                result = response.json()

                # 保存研究结果到Space
                if space_id and user and db:
                    await self._save_research_results(
                        db=db,
                        space_id=space_id,
                        user_id=user.id,
                        research_data=result,
                        query=query
                    )

                return {
                    "space_id": space_id,
                    "research_id": str(uuid4()),
                    "query": query,
                    "mode": mode,
                    "status": "completed",
                    "result": result
                }

        except httpx.TimeoutException:
            logger.error("Deep Research API timeout")
            return {
                "error": "请求超时",
                "message": "研究任务执行时间过长，请稍后重试"
            }
        except Exception as e:
            logger.error(f"Deep Research error: {str(e)}")
            return {
                "error": "研究失败",
                "message": str(e)
            }

    async def _save_research_results(
        self,
        db: AsyncSession,
        space_id: int,
        user_id: int,
        research_data: dict[str, Any],
        query: str
    ) -> None:
        """保存研究结果到Space."""
        try:
            # 保存主要研究报告
            report_content = research_data.get("report", "")
            main_report = DocumentCreate(
                filename="研究报告.md",
                content_type="text/markdown",
                size=len(report_content.encode()),
                space_id=space_id,
                description=f"深度研究报告: {query}",
                meta_data={
                    "document_type": "research_report",
                    "research_query": query,
                    "created_by": "deep_research",
                    "title": f"深度研究报告: {query}",
                    "content": report_content,
                    "summary": research_data.get("summary", "")
                }
            )

            await crud_document.create(
                db=db,
                obj_in=main_report,
                user_id=user_id,
                file_path="",  # 虚拟文件，没有实际文件路径
                file_hash=str(uuid4()),  # 生成唯一哈希
                original_filename="研究报告.md"
            )

            # 保存引用文献
            citations = research_data.get("citations", [])
            for idx, citation in enumerate(citations):
                citation_content = self._format_citation(citation)
                citation_doc = DocumentCreate(
                    filename=f"引用文献_{idx + 1}.md",
                    content_type="text/markdown",
                    size=len(citation_content.encode()),
                    space_id=space_id,
                    description=citation.get("title", f"引用文献 {idx + 1}"),
                    meta_data={
                        "document_type": "citation",
                        "citation_data": citation,
                        "created_by": "deep_research",
                        "title": citation.get("title", f"引用文献 {idx + 1}"),
                        "content": citation_content
                    }
                )

                await crud_document.create(
                    db=db,
                    obj_in=citation_doc,
                    user_id=user_id,
                    file_path="",  # 虚拟文件
                    file_hash=str(uuid4()),  # 生成唯一哈希
                    original_filename=f"引用文献_{idx + 1}.md"
                )

            await db.commit()

        except Exception as e:
            logger.error(f"Error saving research results: {str(e)}")
            await db.rollback()

    def _format_citation(self, citation: dict[str, Any]) -> str:
        """格式化引用文献为Markdown."""
        content = f"# {citation.get('title', '未知标题')}\n\n"

        if citation.get('authors'):
            content += f"**作者**: {', '.join(citation['authors'])}\n\n"

        if citation.get('url'):
            content += f"**链接**: [{citation['url']}]({citation['url']})\n\n"

        if citation.get('published_date'):
            content += f"**发表时间**: {citation['published_date']}\n\n"

        if citation.get('snippet'):
            content += f"## 摘要\n\n{citation['snippet']}\n\n"

        if citation.get('highlights'):
            content += "## 关键内容\n\n"
            for highlight in citation['highlights']:
                content += f"- {highlight}\n"

        return content

    async def stream_research(
        self,
        query: str,
        mode: str = "general",
        user: User | None = None,
        db: AsyncSession | None = None
    ) -> AsyncGenerator[str, None]:
        """
        流式创建深度研究任务.

        Args:
            query: 研究查询
            mode: 研究模式
            user: 当前用户
            db: 数据库会话

        Yields:
            研究进度更新
        """
        if not self.api_key:
            yield json.dumps({
                "error": "Deep Research功能未配置",
                "message": "请配置PERPLEXITY_API_KEY环境变量"
            })
            return

        try:
            # 创建研究Space
            space_id = None
            if user and db:
                space_data = SpaceCreate(
                    name=f"研究: {query[:50]}...",
                    description=f"Deep Research自动创建 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    is_public=False,
                    icon="🔬" if mode == "academic" else "🔍",
                    color=None,
                    tags=None,
                    meta_data={
                        "research_query": query,
                        "research_mode": mode,
                        "created_by": "deep_research"
                    }
                )
                space = await crud_space.create(db, obj_in=space_data, user_id=user.id)
                space_id = space.id
                await db.commit()

                yield json.dumps({
                    "type": "space_created",
                    "space_id": space_id,
                    "message": "研究空间已创建"
                })

            # 调用Perplexity API（流式）
            async with httpx.AsyncClient(timeout=300.0) as client:
                request_data = {
                    "query": query,
                    "mode": mode,
                    "return_citations": True,
                    "stream": True
                }

                async with client.stream(
                    "POST",
                    f"{self.base_url}/deep-research",
                    headers=self.headers,
                    json=request_data
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                yield json.dumps({
                                    "type": "completed",
                                    "message": "研究完成"
                                })
                                break

                            try:
                                event_data = json.loads(data)
                                yield json.dumps({
                                    "type": event_data.get("type", "update"),
                                    "content": event_data.get("content", ""),
                                    "progress": event_data.get("progress", 0)
                                })
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            logger.error(f"Stream research error: {str(e)}")
            yield json.dumps({
                "error": "研究失败",
                "message": str(e)
            })


# 全局实例
deep_research_service = DeepResearchService()
