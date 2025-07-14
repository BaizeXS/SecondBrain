"""Citation CRUD operations."""

from typing import Any

from sqlalchemy import String, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.models import Citation
from app.schemas.citation import CitationCreate, CitationUpdate


class CRUDCitation(CRUDBase[Citation, CitationCreate, CitationUpdate]):
    """Citation CRUD class."""

    async def create(self, db: AsyncSession, *, obj_in: CitationCreate, user_id: int, space_id: int, **kwargs: Any) -> Citation:
        """Create a new citation with user_id and space_id."""
        create_data = obj_in.model_dump(by_alias=True)
        create_data["user_id"] = user_id
        create_data["space_id"] = space_id
        db_obj = self.model(**create_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_bibtex_key(
        self,
        db: AsyncSession,
        *,
        bibtex_key: str,
        user_id: int,
    ) -> Citation | None:
        """通过BibTeX键获取引用."""
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.bibtex_key == bibtex_key,
                    self.model.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_space(
        self,
        db: AsyncSession,
        *,
        space_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Citation]:
        """获取空间的所有引用."""
        result = await db.execute(
            select(self.model)
            .where(self.model.space_id == space_id)
            .order_by(self.model.year.desc(), self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_document(
        self,
        db: AsyncSession,
        *,
        document_id: int,
    ) -> list[Citation]:
        """获取文档的所有引用."""
        result = await db.execute(
            select(self.model)
            .where(self.model.document_id == document_id)
            .order_by(self.model.created_at.desc())
        )
        return list(result.scalars().all())

    async def search(
        self,
        db: AsyncSession,
        *,
        query: str,
        user_id: int,
        space_id: int | None = None,
        citation_type: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        authors: list[str] | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Citation]:
        """搜索引用."""
        stmt = select(self.model).where(self.model.user_id == user_id)

        # 关键词搜索
        if query:
            search_filter = or_(
                self.model.title.ilike(f"%{query}%"),
                self.model.abstract.ilike(f"%{query}%"),
                self.model.bibtex_key.ilike(f"%{query}%"),
                self.model.journal.ilike(f"%{query}%"),
            )
            stmt = stmt.where(search_filter)

        # 空间筛选
        if space_id:
            stmt = stmt.where(self.model.space_id == space_id)

        # 类型筛选
        if citation_type:
            stmt = stmt.where(self.model.citation_type == citation_type)

        # 年份范围
        if year_from:
            stmt = stmt.where(self.model.year >= year_from)
        if year_to:
            stmt = stmt.where(self.model.year <= year_to)

        # 作者筛选（简化版，检查JSON数组）
        if authors:
            for author in authors:
                stmt = stmt.where(
                    self.model.authors.cast(String).ilike(f"%{author}%")
                )

        stmt = stmt.order_by(self.model.year.desc(), self.model.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_citations(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Citation]:
        """获取用户的所有引用."""
        result = await db.execute(
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_ids(
        self,
        db: AsyncSession,
        *,
        ids: list[int],
        user_id: int,
    ) -> list[Citation]:
        """通过ID列表获取引用."""
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.id.in_(ids),
                    self.model.user_id == user_id
                )
            )
        )
        return list(result.scalars().all())

    async def count_by_space(
        self,
        db: AsyncSession,
        *,
        space_id: int,
    ) -> int:
        """统计空间中的引用数量."""
        result = await db.execute(
            select(func.count(self.model.id)).where(self.model.space_id == space_id)
        )
        return result.scalar() or 0

    async def create_batch(
        self,
        db: AsyncSession,
        *,
        citations: list[CitationCreate],
        user_id: int,
        space_id: int,
    ) -> list[Citation]:
        """批量创建引用."""
        db_objs = []

        for citation_data in citations:
            db_obj = Citation(
                **citation_data.model_dump(),
                user_id=user_id,
                space_id=space_id,
            )
            db.add(db_obj)
            db_objs.append(db_obj)

        await db.commit()

        # 刷新所有对象
        for db_obj in db_objs:
            await db.refresh(db_obj)

        return db_objs


# 创建实例
crud_citation = CRUDCitation(Citation)
