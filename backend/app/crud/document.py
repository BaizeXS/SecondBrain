"""Document CRUD operations."""

from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.models import Document
from app.schemas.documents import DocumentCreate, DocumentUpdate


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    """CRUD operations for Document model."""

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: DocumentCreate,
        user_id: int,
        file_path: str,
        file_hash: str,
        original_filename: str | None = None,
        **kwargs: Any
    ) -> Document:
        """Create a new document with required fields."""
        create_data = obj_in.model_dump()

        # Map schema fields to model fields
        db_data = {
            "filename": create_data["filename"],
            "content_type": create_data["content_type"],
            "file_size": create_data["size"],  # size -> file_size
            "space_id": create_data["space_id"],
            "user_id": user_id,
            "file_path": file_path,
            "file_hash": file_hash,
            "original_filename": original_filename or create_data["filename"],
            "tags": create_data.get("tags"),
            "meta_data": create_data.get("metadata")  # metadata -> meta_data
        }

        # Add any additional kwargs
        db_data.update(kwargs)

        db_obj = Document(**db_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_space(
        self,
        db: AsyncSession,
        *,
        space_id: int,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
    ) -> list[Document]:
        """Get documents in a specific space."""
        query = select(Document).where(Document.space_id == space_id)

        if status:
            query = query.where(Document.processing_status == status)

        query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_hash(
        self, db: AsyncSession, *, file_hash: str, space_id: int
    ) -> Document | None:
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
    ) -> list[Document]:
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
        return list(result.scalars().all())

    async def update_processing_status(
        self,
        db: AsyncSession,
        *,
        document_id: int,
        processing_status: str,
        extraction_status: str | None = None,
        embedding_status: str | None = None,
    ) -> Document | None:
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
    ) -> list[Document]:
        """Get child documents (e.g., translations) of a parent document."""
        result = await db.execute(
            select(Document)
            .where(Document.parent_id == parent_id)
            .order_by(Document.created_at)
        )
        return list(result.scalars().all())

    async def get_user_documents(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Document]:
        """Get all documents uploaded by a user."""
        result = await db.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


# Create single instance
crud_document = CRUDDocument(Document)
