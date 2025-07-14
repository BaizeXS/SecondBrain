"""CRUD operations for notes."""

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.models import Note
from app.schemas.note import NoteCreate, NoteUpdate


class CRUDNote(CRUDBase[Note, NoteCreate, NoteUpdate]):
    """CRUD operations for Note model."""

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: NoteCreate,
        user_id: int,
        **kwargs: Any
    ) -> Note:
        """Create a new note with user_id."""
        create_data = obj_in.model_dump()
        create_data["user_id"] = user_id

        # Handle metadata field mapping
        if "metadata" in create_data:
            create_data["meta_data"] = create_data.pop("metadata")

        # Add any additional kwargs
        create_data.update(kwargs)

        db_obj = Note(**create_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_space(
        self,
        db: AsyncSession,
        *,
        space_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[Note]:
        """获取空间内的笔记列表."""
        stmt = select(self.model).where(
            self.model.space_id == space_id,
            self.model.user_id == user_id,
        )

        # 排序
        order_column = getattr(self.model, sort_by, self.model.created_at)
        if sort_order == "desc":
            stmt = stmt.order_by(order_column.desc())
        else:
            stmt = stmt.order_by(order_column)

        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self,
        db: AsyncSession,
        *,
        query: str,
        user_id: int,
        space_ids: list[int] | None = None,
        tags: list[str] | None = None,
        content_types: list[str] | None = None,
        note_types: list[str] | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Note], int]:
        """搜索笔记."""
        # 基础查询
        stmt = select(self.model).where(self.model.user_id == user_id)
        count_stmt = select(func.count(self.model.id)).where(
            self.model.user_id == user_id
        )

        # 文本搜索
        if query:
            search_filter = or_(
                self.model.title.ilike(f"%{query}%"),
                self.model.content.ilike(f"%{query}%"),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        # Space过滤
        if space_ids:
            stmt = stmt.where(self.model.space_id.in_(space_ids))
            count_stmt = count_stmt.where(self.model.space_id.in_(space_ids))

        # 内容类型过滤
        if content_types:
            stmt = stmt.where(self.model.content_type.in_(content_types))
            count_stmt = count_stmt.where(self.model.content_type.in_(content_types))

        # 笔记类型过滤
        if note_types:
            stmt = stmt.where(self.model.note_type.in_(note_types))
            count_stmt = count_stmt.where(self.model.note_type.in_(note_types))

        # 标签过滤（暂时跳过，在Python中过滤）
        # Note: JSON filtering is handled in Python for SQLite compatibility
        tag_filter_needed = bool(tags)

        # 获取总数
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 排序和分页
        stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        # 执行查询
        result = await db.execute(stmt)
        notes = list(result.scalars().all())

        # 在Python中进行标签过滤（SQLite兼容）
        if tag_filter_needed and tags:
            filtered_notes = []
            for note in notes:
                if note.tags:
                    if any(tag in note.tags for tag in tags):
                        filtered_notes.append(note)
            notes = filtered_notes
            total = len(notes)

        return notes, total

    async def get_linked_notes(
        self,
        db: AsyncSession,
        *,
        note_id: int,
        user_id: int,
    ) -> list[Note]:
        """获取关联的笔记."""
        # 获取当前笔记
        note = await self.get(db, id=note_id)
        if not note or note.user_id != user_id:
            return []

        if not note.linked_notes:
            return []

        # 获取关联笔记
        stmt = select(self.model).where(
            self.model.id.in_(note.linked_notes),
            self.model.user_id == user_id,
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_document(
        self,
        db: AsyncSession,
        *,
        document_id: int,
        user_id: int,
    ) -> list[Note]:
        """获取与文档关联的笔记."""
        # Get all notes for the user and filter in Python for SQLite compatibility
        stmt = select(self.model).where(self.model.user_id == user_id)
        result = await db.execute(stmt)
        all_notes = result.scalars().all()

        # Filter notes that have the document_id in their linked_documents
        filtered_notes = []
        for note in all_notes:
            if note.linked_documents and document_id in note.linked_documents:
                filtered_notes.append(note)

        return filtered_notes

    async def get_recent_notes(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        limit: int = 10,
        note_type: str | None = None,
    ) -> list[Note]:
        """获取最近的笔记."""
        stmt = select(self.model).where(self.model.user_id == user_id)

        if note_type:
            stmt = stmt.where(self.model.note_type == note_type)

        stmt = stmt.order_by(self.model.updated_at.desc()).limit(limit)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def update_links(
        self,
        db: AsyncSession,
        *,
        note_id: int,
        linked_documents: list[int] | None = None,
        linked_notes: list[int] | None = None,
    ) -> Note | None:
        """更新笔记的关联."""
        note = await self.get(db, id=note_id)
        if not note:
            return None

        if linked_documents is not None:
            note.linked_documents = linked_documents

        if linked_notes is not None:
            note.linked_notes = linked_notes

        await db.commit()
        await db.refresh(note)

        return note

    async def add_tag(
        self,
        db: AsyncSession,
        *,
        note_id: int,
        tag: str,
    ) -> Note | None:
        """添加标签."""
        note = await self.get(db, id=note_id)
        if not note:
            return None

        if not note.tags:
            note.tags = []

        if tag not in note.tags:
            # Create a new list to ensure SQLAlchemy detects the change
            note.tags = note.tags + [tag]
            await db.commit()
            await db.refresh(note)

        return note

    async def remove_tag(
        self,
        db: AsyncSession,
        *,
        note_id: int,
        tag: str,
    ) -> Note | None:
        """移除标签."""
        note = await self.get(db, id=note_id)
        if not note:
            return None

        if note.tags and tag in note.tags:
            # Create a new list to ensure SQLAlchemy detects the change
            note.tags = [t for t in note.tags if t != tag]
            await db.commit()
            await db.refresh(note)

        return note

    async def get_tags(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        space_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """获取用户的所有标签及使用次数."""
        # 获取所有笔记
        stmt = select(self.model).where(self.model.user_id == user_id)

        if space_id:
            stmt = stmt.where(self.model.space_id == space_id)

        result = await db.execute(stmt)
        notes = result.scalars().all()

        # 统计标签
        tag_counts = {}
        for note in notes:
            if note.tags:
                for tag in note.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # 转换为排序的列表
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"tag": tag, "count": count} for tag, count in sorted_tags]


# 创建CRUD实例
crud_note = CRUDNote(Note)
