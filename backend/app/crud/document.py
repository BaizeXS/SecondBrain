"""Document CRUD operations."""

from typing import List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.models import Document
from app.schemas.documents import DocumentCreate, DocumentUpdate


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    """CRUD operations for Document model."""

    async def get_by_space(
        self,
        db: AsyncSession,
        *,
        space_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[Document]:
        """Get documents in a specific space."""
        query = select(Document).where(Document.space_id == space_id)
        
        if status:
            query = query.where(Document.processing_status == status)
        
        query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_hash(
        self, db: AsyncSession, *, file_hash: str, space_id: int
    ) -> Optional[Document]:
        """Get document by file hash in a specific space."""
        result = await db.execute(
            select(Document).where(
                and_(
                    Document.file_hash == file_hash,
                    Document.space_id == space_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        db: AsyncSession,
        *,
        space_id: int,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Document]:
        """Search documents by title or content."""
        search_filter = or_(
            Document.title.ilike(f"%{query}%"),
            Document.content.ilike(f"%{query}%"),
            Document.filename.ilike(f"%{query}%"),
        )
        
        stmt = (
            select(Document)
            .where(and_(Document.space_id == space_id, search_filter))
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        return result.scalars().all()

    async def update_processing_status(
        self,
        db: AsyncSession,
        *,
        document_id: int,
        processing_status: str,
        extraction_status: Optional[str] = None,
        embedding_status: Optional[str] = None,
    ) -> Optional[Document]:
        """Update document processing status."""
        document = await self.get(db, document_id)
        if document:
            document.processing_status = processing_status
            if extraction_status:
                document.extraction_status = extraction_status
            if embedding_status:
                document.embedding_status = embedding_status
            await db.commit()
            await db.refresh(document)
        return document

    async def get_by_parent(
        self, db: AsyncSession, *, parent_id: int
    ) -> List[Document]:
        """Get child documents (e.g., translations) of a parent document."""
        result = await db.execute(
            select(Document)
            .where(Document.parent_id == parent_id)
            .order_by(Document.created_at)
        )
        return result.scalars().all()

    async def get_user_documents(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Document]:
        """Get all documents uploaded by a user."""
        result = await db.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


# Create single instance
document = CRUDDocument(Document)