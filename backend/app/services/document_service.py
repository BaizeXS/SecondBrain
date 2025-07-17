"""Complete document management service with content processing and CRUD operations."""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.models.models import Document, User
from app.schemas.documents import DocumentCreate
from app.services.document_content_service import DocumentContentService
from app.services.web_scraper_service import web_scraper_service


class DocumentService:
    """完整的文档管理服务 - 包含内容处理和数据库操作."""

    def __init__(self) -> None:
        """初始化文档服务."""
        self.content_service = DocumentContentService()

    async def create_document(
        self,
        db: AsyncSession,
        space_id: int,
        filename: str,
        content: str,
        content_type: str,
        file_size: int,
        user: User,
    ) -> Document:
        """创建文档记录."""
        # 生成文件hash
        file_hash = hashlib.sha256(content.encode()).hexdigest()

        # 检查文档是否已存在
        existing = await crud.crud_document.get_by_hash(
            db, file_hash=file_hash, space_id=space_id
        )
        if existing:
            return existing

        # 创建文档schema
        document_in = DocumentCreate(
            filename=filename,
            content_type=content_type,
            size=file_size,
            space_id=space_id,
        )

        # 创建文档
        document = await crud.crud_document.create(
            db,
            obj_in=document_in,
            user_id=user.id,
            file_path=f"spaces/{space_id}/documents/{file_hash}",
            file_hash=file_hash,
            original_filename=filename,
            content=content[:1000],  # 存储前1000字符作为预览
            processing_status="completed",
            extraction_status="completed",
            embedding_status="pending",
        )

        # 更新空间统计
        await crud.crud_space.update_stats(
            db, space_id=space_id, document_delta=1, size_delta=file_size
        )

        return document

    async def get_space_documents(
        self,
        db: AsyncSession, space_id: int, skip: int = 0, limit: int = 20
    ) -> list[Document]:
        """获取空间内的文档列表."""
        return await crud.crud_document.get_by_space(
            db, space_id=space_id, skip=skip, limit=limit
        )

    async def get_document_by_id(
        self,
        db: AsyncSession, document_id: int, user: User
    ) -> Document | None:
        """根据ID获取文档."""
        document = await crud.crud_document.get(db, id=document_id)

        if not document:
            return None

        # 检查权限
        space = await crud.crud_space.get(db, id=document.space_id)
        if space and (space.user_id == user.id or space.is_public):
            return document

        # 检查协作权限
        access = await crud.crud_space.get_user_access(
            db, space_id=document.space_id, user_id=user.id
        )
        if access:
            return document

        return None

    async def delete_document(
        self,
        db: AsyncSession, document: Document
    ) -> bool:
        """删除文档."""
        # 更新空间统计
        await crud.crud_space.update_stats(
            db,
            space_id=document.space_id,
            document_delta=-1,
            size_delta=-document.file_size,
        )

        # 删除文档
        await crud.crud_document.remove(db, id=document.id)
        return True

    async def search_documents(
        self,
        db: AsyncSession,
        space_id: int,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Document]:
        """搜索文档."""
        return await crud.crud_document.search(
            db, space_id=space_id, query=query, skip=skip, limit=limit
        )

    async def update_processing_status(
        self,
        db: AsyncSession,
        document_id: int,
        processing_status: str,
        extraction_status: str | None = None,
        embedding_status: str | None = None,
    ) -> Document | None:
        """更新文档处理状态."""
        return await crud.crud_document.update_processing_status(
            db,
            document_id=document_id,
            processing_status=processing_status,
            extraction_status=extraction_status,
            embedding_status=embedding_status,
        )

    async def import_from_url(
        self,
        db: AsyncSession,
        url: str,
        space_id: int,
        user: User,
        title: str | None = None,
        tags: list[str] | None = None,
        save_snapshot: bool = True,
    ) -> dict[str, Any]:
        """从URL导入网页内容."""
        try:
            # 抓取网页
            web_data = await web_scraper_service.fetch_webpage(url)

            if web_data["status"] != "success":
                return {
                    "status": "error",
                    "error": web_data.get("error", "网页抓取失败"),
                    "url": url
                }

            # 准备文档数据
            content = web_data["content"]
            metadata = web_data["metadata"]
            snapshot_html = web_data.get("snapshot_html", "") if save_snapshot else None

            # 使用提供的标题或从网页获取的标题
            doc_title = title or metadata.get("title", url)

            # 生成文件名
            filename = f"web_{hashlib.md5(url.encode()).hexdigest()[:8]}.html"

            # 生成文件hash
            file_hash = hashlib.sha256(content.encode()).hexdigest()
            file_path = f"spaces/{space_id}/web/{file_hash}"

            # 准备元数据
            meta_data = {
                **metadata,
                "source_url": url,
                "imported_at": datetime.now().isoformat(),
                "has_snapshot": save_snapshot
            }

            # 如果保存快照，将其存储在meta_data中
            if snapshot_html:
                meta_data["snapshot_html"] = snapshot_html

            # 创建文档schema
            document_in = DocumentCreate(
                filename=filename,
                content_type="text/html",
                size=len(content.encode()),
                space_id=space_id,
                tags=tags,
                meta_data=meta_data,
            )

            # 创建文档记录
            document = await crud.crud_document.create(
                db,
                obj_in=document_in,
                user_id=user.id,
                file_path=file_path,
                file_hash=file_hash,
                original_filename=doc_title,
                title=doc_title,
                content=content,
                processing_status="completed",
                extraction_status="completed",
                url=url,  # 保存原始URL
            )

            # 更新空间统计
            await crud.crud_space.update_stats(
                db,
                space_id=space_id,
                document_delta=1,
                size_delta=document.file_size,
            )

            return {
                "status": "success",
                "document_id": document.id,
                "url": url,
                "title": document.title,
                "metadata": metadata
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "url": url
            }

    async def batch_import_urls(
        self,
        db: AsyncSession,
        urls: list[str],
        space_id: int,
        user: User,
        tags: list[str] | None = None,
        save_snapshot: bool = True,
    ) -> list[dict[str, Any]]:
        """批量导入多个URL."""
        results = []

        for url in urls:
            result = await self.import_from_url(
                db, url, space_id, user, tags=tags, save_snapshot=save_snapshot
            )
            results.append(result)

        return results

    async def get_web_snapshot(
        self,
        db: AsyncSession,
        document_id: int,
        user: User,
    ) -> dict[str, Any] | None:
        """获取网页快照."""
        document = await self.get_document_by_id(db, document_id, user)

        if not document:
            return None

        # 检查是否是网页文档
        if not document.meta_data or "source_url" not in document.meta_data:
            return None

        snapshot_data = {
            "document_id": document.id,
            "url": document.meta_data["source_url"],
            "title": document.title,
            "metadata": document.meta_data,
            "created_at": document.created_at,
        }

        # 获取快照HTML
        if "snapshot_html" in document.meta_data:
            snapshot_data["snapshot_html"] = document.meta_data["snapshot_html"]
            # 转换为Markdown
            snapshot_data["snapshot_markdown"] = web_scraper_service.convert_to_markdown(
                document.meta_data["snapshot_html"]
            )

        return snapshot_data

    async def analyze_url(
        self,
        url: str,
    ) -> dict[str, Any]:
        """分析URL内容（不保存）."""
        try:
            # 抓取网页
            web_data = await web_scraper_service.fetch_webpage(url)

            if web_data["status"] != "success":
                return {
                    "url": url,
                    "can_import": False,
                    "error": web_data.get("error", "无法访问该网页")
                }

            content = web_data["content"]
            metadata = web_data["metadata"]

            # 分析内容
            word_count = len(content.split())

            # 提取链接
            links = web_scraper_service.extract_links(
                web_data.get("snapshot_html", ""), url
            )

            # 简单的标签建议（基于标题和描述）
            suggested_tags = []
            title = metadata.get("title", "").lower()
            description = metadata.get("description", "").lower()

            # 基于关键词的简单标签建议
            tech_keywords = ["python", "javascript", "ai", "machine learning", "programming", "code", "software"]
            for keyword in tech_keywords:
                if keyword in title or keyword in description:
                    suggested_tags.append(keyword)

            return {
                "url": url,
                "title": metadata.get("title", ""),
                "description": metadata.get("description"),
                "content_preview": content[:500] + "..." if len(content) > 500 else content,
                "metadata": metadata,
                "word_count": word_count,
                "links_count": len(links),
                "images_count": 0,  # 简化版不统计图片
                "can_import": True,
                "suggested_tags": suggested_tags[:5]  # 最多5个标签
            }

        except Exception as e:
            return {
                "url": url,
                "can_import": False,
                "error": str(e)
            }

    async def create_document_from_file(
        self,
        db: AsyncSession,
        space_id: int,
        file_path: Path,
        user: User,
        title: str | None = None,
    ) -> Document:
        """从文件创建文档记录，包含内容提取."""
        try:
            # 获取文件信息
            file_ext = file_path.suffix.lower()
            file_size = file_path.stat().st_size
            filename = file_path.name

            # 使用增强的内容提取
            extraction_result = await self.content_service.extract_content_enhanced(file_path, file_ext)
            content = extraction_result["text"]
            metadata = extraction_result["metadata"]

            # 添加提取信息到元数据
            metadata["extraction_method"] = extraction_result["extraction_method"]
            metadata["content_format"] = extraction_result["format"]
            metadata["has_tables"] = extraction_result["has_tables"]
            metadata["has_images"] = extraction_result["has_images"]
            metadata["has_formulas"] = extraction_result["has_formulas"]

            # 生成文件hash
            file_hash = hashlib.sha256(content.encode()).hexdigest()

            # 检查文档是否已存在
            existing = await crud.crud_document.get_by_hash(
                db, file_hash=file_hash, space_id=space_id
            )
            if existing:
                return existing

            # 创建文档schema
            document_in = DocumentCreate(
                filename=filename,
                content_type=self._get_content_type(file_ext),
                size=file_size,
                space_id=space_id,
                meta_data=metadata,
            )

            # 创建文档
            document = await crud.crud_document.create(
                db,
                obj_in=document_in,
                user_id=user.id,
                file_path=f"spaces/{space_id}/documents/{file_hash}",
                file_hash=file_hash,
                original_filename=filename,
                title=title or metadata.get("title", filename),
                content=content[:1000],  # 存储前1000字符作为预览
                processing_status="completed",
                extraction_status="completed",
                embedding_status="pending",
            )

            # 更新空间统计
            await crud.crud_space.update_stats(
                db, space_id=space_id, document_delta=1, size_delta=file_size
            )

            return document

        except Exception as e:
            raise Exception(f"创建文档失败: {str(e)}") from e

    async def extract_document_content(
        self,
        file_path: Path,
        file_ext: str | None = None,
    ) -> str:
        """提取文档内容."""
        if not file_ext:
            file_ext = file_path.suffix.lower()

        return await self.content_service.extract_content(file_path, file_ext)

    async def get_document_metadata(
        self,
        file_path: Path,
    ) -> dict[str, Any]:
        """获取文档元数据."""
        return await self.content_service.get_document_metadata(file_path)

    async def split_document_content(
        self,
        content: str,
        chunk_size: int = 1000,
        overlap: int = 100,
    ) -> list[str]:
        """将文档内容分割成块."""
        return await self.content_service.split_document(content, chunk_size, overlap)

    async def extract_keywords(
        self,
        content: str,
        max_keywords: int = 10,
    ) -> list[str]:
        """提取关键词."""
        return await self.content_service.extract_keywords(content, max_keywords)

    async def summarize_content(
        self,
        content: str,
        max_length: int = 200,
    ) -> str:
        """生成内容摘要."""
        return await self.content_service.summarize_content(content, max_length)

    def _get_content_type(self, file_ext: str) -> str:
        """根据文件扩展名获取MIME类型."""
        content_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".ppt": "application/vnd.ms-powerpoint",
        }
        return content_types.get(file_ext.lower(), "application/octet-stream")


# 创建全局实例
document_service = DocumentService()
