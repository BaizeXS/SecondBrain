"""Note version CRUD operations."""

from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.models import NoteVersion
from app.schemas.note_version import NoteVersionCreate


class CRUDNoteVersion(CRUDBase[NoteVersion, NoteVersionCreate, NoteVersionCreate]):
    """Note version CRUD class."""

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: NoteVersionCreate,
        user_id: int,
        **kwargs: Any
    ) -> NoteVersion:
        """Create a new note version with user_id."""
        create_data = obj_in.model_dump()
        create_data["user_id"] = user_id

        # Add any additional kwargs
        create_data.update(kwargs)

        db_obj = NoteVersion(**create_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_note(
        self,
        db: AsyncSession,
        *,
        note_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> list[NoteVersion]:
        """获取笔记的所有版本."""
        result = await db.execute(
            select(self.model)
            .where(self.model.note_id == note_id)
            .order_by(self.model.version_number.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_version(
        self,
        db: AsyncSession,
        *,
        note_id: int,
    ) -> NoteVersion | None:
        """获取笔记的最新版本."""
        result = await db.execute(
            select(self.model)
            .where(self.model.note_id == note_id)
            .order_by(self.model.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_version_number(
        self,
        db: AsyncSession,
        *,
        note_id: int,
        version_number: int,
    ) -> NoteVersion | None:
        """通过版本号获取特定版本."""
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.note_id == note_id,
                    self.model.version_number == version_number
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_next_version_number(
        self,
        db: AsyncSession,
        *,
        note_id: int,
    ) -> int:
        """获取下一个版本号."""
        latest = await self.get_latest_version(db, note_id=note_id)
        return (latest.version_number + 1) if latest else 1

    async def create_version(
        self,
        db: AsyncSession,
        *,
        note_id: int,
        user_id: int,
        title: str,
        content: str,
        content_html: str | None = None,
        change_summary: str | None = None,
        change_type: str = "edit",
        ai_model: str | None = None,
        ai_prompt: str | None = None,
        tags: list[str] | None = None,
        word_count: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> NoteVersion:
        """创建新版本."""
        version_number = await self.get_next_version_number(db, note_id=note_id)

        db_obj = NoteVersion(
            note_id=note_id,
            user_id=user_id,
            version_number=version_number,
            title=title,
            content=content,
            content_html=content_html,
            change_summary=change_summary,
            change_type=change_type,
            ai_model=ai_model,
            ai_prompt=ai_prompt,
            tags=tags,
            word_count=word_count,
            meta_data=metadata,
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        return db_obj

    async def cleanup_old_versions(
        self,
        db: AsyncSession,
        *,
        note_id: int,
        keep_count: int = 10,
    ) -> int:
        """清理旧版本，保留最近的N个版本."""
        # 获取所有版本
        versions = await self.get_by_note(db, note_id=note_id, limit=1000)

        if len(versions) <= keep_count:
            return 0

        # 删除旧版本
        versions_to_delete = versions[keep_count:]
        deleted_count = 0

        for version in versions_to_delete:
            await db.delete(version)
            deleted_count += 1

        await db.commit()
        return deleted_count

    async def get_versions_between(
        self,
        db: AsyncSession,
        *,
        note_id: int,
        start_version: int,
        end_version: int,
    ) -> list[NoteVersion]:
        """获取版本范围内的所有版本."""
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.note_id == note_id,
                    self.model.version_number >= start_version,
                    self.model.version_number <= end_version
                )
            ).order_by(self.model.version_number)
        )
        return list(result.scalars().all())


# 创建实例
crud_note_version = CRUDNoteVersion(NoteVersion)
