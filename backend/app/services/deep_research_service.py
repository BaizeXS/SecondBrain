"""Deep Research Service - 集成Perplexity Deep Research API."""

import json
import logging
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.document import crud_document
from app.crud.space import crud_space
from app.models.models import User
from app.schemas.documents import DocumentCreate
from app.schemas.spaces import SpaceCreate

logger = logging.getLogger(__name__)


class DeepResearchService:
    """Deep Research服务 - 使用Perplexity API进行深度研究."""

    def __init__(self) -> None:
        # 使用 OpenRouter 而不是直接使用 Perplexity API
        from app.services.ai_service import ai_service

        self.ai_service = ai_service

    async def create_research(
        self,
        query: str,
        mode: str = "general",  # general 或 academic
        user: User | None = None,
        db: AsyncSession | None = None,
        space_id: int | None = None,
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
        # 检查 OpenRouter 是否可用
        if not self.ai_service.openrouter_client:
            logger.error("OpenRouter provider not configured")
            return {
                "error": "Deep Research功能未配置",
                "message": "请配置OPENROUTER_API_KEY环境变量",
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
                        "created_by": "deep_research",
                    },
                )
                space = await crud_space.create(db, obj_in=space_data, user_id=user.id)
                space_id = space.id
                await db.commit()

            # 使用 OpenRouter 调用 Perplexity Deep Research 模型
            messages = [
                {
                    "role": "system",
                    "content": f"You are a deep research assistant. Provide a {'academic' if mode == 'academic' else 'comprehensive'} research report on the given topic. Include relevant citations, sources, and a structured analysis.",
                },
                {"role": "user", "content": query},
            ]

            # 使用 AI Service 调用 Deep Research 模型
            try:
                # 使用非流式调用获取完整响应
                response_content = await self.ai_service.chat(
                    messages=messages,
                    model="perplexity/sonar-deep-research",  # 使用 Deep Research 专用模型
                    temperature=0.7,
                )

                # 构建响应结果
                result = {
                    "choices": [
                        {"message": {"content": response_content, "role": "assistant"}}
                    ],
                    "citations": [],  # OpenRouter 可能会在响应中包含引用信息
                }

            except Exception as e:
                logger.error(f"Deep Research API call failed: {str(e)}")
                return {"error": "API调用失败", "message": str(e)}

            # 保存研究结果到Space
            if space_id and user and db:
                await self._save_research_results(
                    db=db,
                    space_id=space_id,
                    user_id=user.id,
                    research_data=result,
                    query=query,
                )

            return {
                "space_id": space_id,
                "research_id": str(uuid4()),
                "query": query,
                "mode": mode,
                "status": "completed",
                "result": result,
            }

        except httpx.TimeoutException:
            logger.error("Deep Research API timeout")
            return {"error": "请求超时", "message": "研究任务执行时间过长，请稍后重试"}
        except Exception as e:
            logger.error(f"Deep Research error: {str(e)}")
            return {"error": "研究失败", "message": str(e)}

    async def _save_research_results(
        self,
        db: AsyncSession,
        space_id: int,
        user_id: int,
        research_data: dict[str, Any],
        query: str,
    ) -> None:
        """保存研究结果到Space."""
        try:
            # 从响应中提取报告内容
            report_content = ""
            if "choices" in research_data and len(research_data["choices"]) > 0:
                report_content = research_data["choices"][0]["message"]["content"]
            elif "report" in research_data:
                report_content = research_data["report"]
            else:
                report_content = str(research_data)

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
                    "summary": report_content[:200] + "..."
                    if len(report_content) > 200
                    else report_content,
                },
            )

            await crud_document.create(
                db=db,
                obj_in=main_report,
                user_id=user_id,
                file_path="",  # 虚拟文件，没有实际文件路径
                file_hash=str(uuid4()),  # 生成唯一哈希
                original_filename="研究报告.md",
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
                        "content": citation_content,
                    },
                )

                await crud_document.create(
                    db=db,
                    obj_in=citation_doc,
                    user_id=user_id,
                    file_path="",  # 虚拟文件
                    file_hash=str(uuid4()),  # 生成唯一哈希
                    original_filename=f"引用文献_{idx + 1}.md",
                )

            await db.commit()

        except Exception as e:
            logger.error(f"Error saving research results: {str(e)}")
            await db.rollback()

    def _format_citation(self, citation: dict[str, Any]) -> str:
        """格式化引用文献为Markdown."""
        content = f"# {citation.get('title', '未知标题')}\n\n"

        if citation.get("authors"):
            content += f"**作者**: {', '.join(citation['authors'])}\n\n"

        if citation.get("url"):
            content += f"**链接**: [{citation['url']}]({citation['url']})\n\n"

        if citation.get("published_date"):
            content += f"**发表时间**: {citation['published_date']}\n\n"

        if citation.get("snippet"):
            content += f"## 摘要\n\n{citation['snippet']}\n\n"

        if citation.get("highlights"):
            content += "## 关键内容\n\n"
            for highlight in citation["highlights"]:
                content += f"- {highlight}\n"

        return content

    async def stream_research(
        self,
        query: str,
        mode: str = "general",
        user: User | None = None,
        db: AsyncSession | None = None,
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
        # 检查 OpenRouter 是否可用
        if not self.ai_service.openrouter_client:
            yield json.dumps(
                {
                    "error": "Deep Research功能未配置",
                    "message": "请配置OPENROUTER_API_KEY环境变量",
                }
            )
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
                        "created_by": "deep_research",
                    },
                )
                space = await crud_space.create(db, obj_in=space_data, user_id=user.id)
                space_id = space.id
                await db.commit()

                yield json.dumps(
                    {
                        "type": "space_created",
                        "space_id": space_id,
                        "message": "研究空间已创建",
                    }
                )

            # 使用 OpenRouter 调用 Perplexity Deep Research 模型（流式）
            messages = [
                {
                    "role": "system",
                    "content": f"You are a deep research assistant. Provide a {'academic' if mode == 'academic' else 'comprehensive'} research report on the given topic. Include relevant citations, sources, and a structured analysis.",
                },
                {"role": "user", "content": query},
            ]

            # 使用 AI Service 的流式调用
            progress = 0
            buffer = ""

            async for chunk in self.ai_service.stream_chat(
                messages=messages,
                model="perplexity/sonar-deep-research",
                temperature=0.7,
            ):
                buffer += chunk
                progress += 1

                # 发送进度更新
                yield json.dumps(
                    {
                        "type": "update",
                        "content": chunk,
                        "progress": min(progress * 5, 95),  # 模拟进度
                    }
                )

            # 保存研究结果
            if space_id and user and db:
                result = {
                    "choices": [{"message": {"content": buffer, "role": "assistant"}}],
                    "citations": [],
                }

                await self._save_research_results(
                    db=db,
                    space_id=space_id,
                    user_id=user.id,
                    research_data=result,
                    query=query,
                )

            yield json.dumps(
                {"type": "completed", "message": "研究完成", "space_id": space_id}
            )

        except Exception as e:
            logger.error(f"Stream research error: {str(e)}")
            yield json.dumps({"error": "研究失败", "message": str(e)})


# 全局实例
deep_research_service = DeepResearchService()
