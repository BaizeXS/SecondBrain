"""Simplified document management service using CRUD layer."""

import hashlib
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.models.models import Document, User


class DocumentService:
    """文档管理服务 - 使用CRUD层的版本."""

    @staticmethod
    async def create_document(
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
        existing = await crud.document.get_by_hash(
            db, file_hash=file_hash, space_id=space_id
        )
        if existing:
            return existing

        # 创建文档数据
        document_data = {
            "space_id": space_id,
            "user_id": user.id,
            "filename": filename,
            "original_filename": filename,
            "file_path": f"spaces/{space_id}/documents/{file_hash}",
            "content_type": content_type,
            "file_size": file_size,
            "file_hash": file_hash,
            "content": content[:1000],  # 存储前1000字符作为预览
            "processing_status": "completed",
            "extraction_status": "completed",
            "embedding_status": "pending",
        }

        # 创建文档
        document = await crud.document.create(db, obj_in=document_data)

        # 更新空间统计
        await crud.space.update_stats(
            db, space_id=space_id, document_delta=1, size_delta=file_size
        )

        return document

    @staticmethod
    async def get_space_documents(
        db: AsyncSession, space_id: int, skip: int = 0, limit: int = 20
    ) -> List[Document]:
        """获取空间内的文档列表."""
        return await crud.document.get_by_space(
            db, space_id=space_id, skip=skip, limit=limit
        )

    @staticmethod
    async def get_document_by_id(
        db: AsyncSession, document_id: int, user: User
    ) -> Optional[Document]:
        """根据ID获取文档."""
        document = await crud.document.get(db, id=document_id)
        
        if not document:
            return None
        
        # 检查权限
        space = await crud.space.get(db, id=document.space_id)
        if space and (space.user_id == user.id or space.is_public):
            return document
        
        # 检查协作权限
        access = await crud.space.get_user_access(
            db, space_id=document.space_id, user_id=user.id
        )
        if access:
            return document
        
        return None

    @staticmethod
    async def delete_document(
        db: AsyncSession, document: Document
    ) -> bool:
        """删除文档."""
        # 更新空间统计
        await crud.space.update_stats(
            db,
            space_id=document.space_id,
            document_delta=-1,
            size_delta=-document.file_size,
        )

        # 删除文档
        await crud.document.remove(db, id=document.id)
        return True

    @staticmethod
    async def search_documents(
        db: AsyncSession,
        space_id: int,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Document]:
        """搜索文档."""
        return await crud.document.search(
            db, space_id=space_id, query=query, skip=skip, limit=limit
        )

    @staticmethod
    async def update_processing_status(
        db: AsyncSession,
        document_id: int,
        processing_status: str,
        extraction_status: Optional[str] = None,
        embedding_status: Optional[str] = None,
    ) -> Optional[Document]:
        """更新文档处理状态."""
        return await crud.document.update_processing_status(
            db,
            document_id=document_id,
            processing_status=processing_status,
            extraction_status=extraction_status,
            embedding_status=embedding_status,
        )