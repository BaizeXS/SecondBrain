"""CRUD operations for annotations."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.models import Annotation, Document
from app.schemas.annotation import AnnotationCreate, AnnotationUpdate


class CRUDAnnotation(CRUDBase[Annotation, AnnotationCreate, AnnotationUpdate]):
    """CRUD operations for Annotation model."""

    async def create(self, db: AsyncSession, *, obj_in: AnnotationCreate, user_id: int, **kwargs: Any) -> Annotation:
        """Create a new annotation with user_id."""
        create_data = obj_in.model_dump()
        create_data["user_id"] = user_id
        db_obj = self.model(**create_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_document(
        self,
        db: AsyncSession,
        *,
        document_id: int,
        user_id: int,
        page_number: int | None = None,
        annotation_type: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Annotation]:
        """获取文档的标注列表."""
        stmt = select(self.model).where(
            self.model.document_id == document_id,
            self.model.user_id == user_id,
        )

        # 页码过滤
        if page_number is not None:
            stmt = stmt.where(self.model.page_number == page_number)

        # 类型过滤
        if annotation_type:
            stmt = stmt.where(self.model.type == annotation_type)

        # 按创建时间排序
        stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_document_pages(
        self,
        db: AsyncSession,
        *,
        document_id: int,
        user_id: int,
        start_page: int,
        end_page: int,
    ) -> list[Annotation]:
        """获取文档指定页码范围的标注."""
        stmt = select(self.model).where(
            self.model.document_id == document_id,
            self.model.user_id == user_id,
            self.model.page_number >= start_page,
            self.model.page_number <= end_page,
        )

        stmt = stmt.order_by(self.model.page_number, self.model.created_at)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_annotations(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        annotation_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Annotation], int]:
        """获取用户的所有标注."""
        # 基础查询
        stmt = select(self.model).where(self.model.user_id == user_id)
        count_stmt = select(func.count(self.model.id)).where(
            self.model.user_id == user_id
        )

        # 类型过滤
        if annotation_type:
            stmt = stmt.where(self.model.type == annotation_type)
            count_stmt = count_stmt.where(self.model.type == annotation_type)

        # 获取总数
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 排序和分页
        stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        # 执行查询
        result = await db.execute(stmt)
        annotations = list(result.scalars().all())

        return annotations, total

    async def batch_create(
        self,
        db: AsyncSession,
        *,
        document_id: int,
        user_id: int,
        annotations_data: list[AnnotationCreate],
    ) -> list[Annotation]:
        """批量创建标注."""
        annotations = []

        for data in annotations_data:
            obj_data = data.model_dump(exclude={"document_id"})
            db_obj = self.model(
                document_id=document_id,
                user_id=user_id,
                **obj_data
            )
            db.add(db_obj)
            annotations.append(db_obj)

        await db.commit()

        # 刷新所有对象
        for annotation in annotations:
            await db.refresh(annotation)

        return annotations

    async def search_annotations(
        self,
        db: AsyncSession,
        *,
        query: str,
        user_id: int,
        document_ids: list[int] | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Annotation], int]:
        """搜索标注内容."""
        # 联合查询以获取文档信息
        stmt = select(self.model).join(Document).where(
            self.model.user_id == user_id
        )
        count_stmt = select(func.count(self.model.id)).join(Document).where(
            self.model.user_id == user_id
        )

        # 文本搜索
        if query:
            search_filter = self.model.content.ilike(f"%{query}%") | \
                          self.model.selected_text.ilike(f"%{query}%")
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        # 文档过滤
        if document_ids:
            stmt = stmt.where(self.model.document_id.in_(document_ids))
            count_stmt = count_stmt.where(self.model.document_id.in_(document_ids))

        # 获取总数
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 排序和分页
        stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        # 执行查询
        result = await db.execute(stmt)
        annotations = list(result.scalars().all())

        return annotations, total

    async def get_statistics(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        document_id: int | None = None,
    ) -> dict[str, Any]:
        """获取标注统计信息."""
        # 基础查询条件
        base_condition = [self.model.user_id == user_id]
        if document_id:
            base_condition.append(self.model.document_id == document_id)

        # 总数统计
        total_stmt = select(func.count(self.model.id)).where(*base_condition)
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0

        # 按类型统计
        type_stmt = select(
            self.model.type,
            func.count(self.model.id).label("count")
        ).where(*base_condition).group_by(self.model.type)

        type_result = await db.execute(type_stmt)
        by_type = {row.type: row.count for row in type_result}

        # 按颜色统计（仅高亮和下划线）
        color_stmt = select(
            self.model.color,
            func.count(self.model.id).label("count")
        ).where(
            *base_condition,
            self.model.type.in_(["highlight", "underline"]),
            self.model.color.isnot(None)
        ).group_by(self.model.color)

        color_result = await db.execute(color_stmt)
        by_color = {row.color: row.count for row in color_result}

        # 最近活动
        recent_stmt = select(self.model).where(*base_condition)\
            .order_by(self.model.created_at.desc()).limit(10)

        recent_result = await db.execute(recent_stmt)
        recent_annotations = list(recent_result.scalars().all())

        recent_activity = [
            {
                "id": ann.id,
                "type": ann.type,
                "document_id": ann.document_id,
                "created_at": ann.created_at,
                "content_preview": ann.content[:50] if ann.content else None,
            }
            for ann in recent_annotations
        ]

        return {
            "total_annotations": total,
            "by_type": by_type,
            "by_color": by_color,
            "recent_activity": recent_activity,
        }

    async def copy_annotations(
        self,
        db: AsyncSession,
        *,
        source_document_id: int,
        target_document_id: int,
        user_id: int,
    ) -> list[Annotation]:
        """复制标注到另一个文档."""
        # 获取源文档的所有标注
        source_annotations = await self.get_by_document(
            db=db,
            document_id=source_document_id,
            user_id=user_id,
            limit=1000,  # 设置较大限制
        )

        # 创建新标注
        new_annotations = []
        for ann in source_annotations:
            new_ann = self.model(
                document_id=target_document_id,
                user_id=user_id,
                type=ann.type,
                content=ann.content,
                selected_text=ann.selected_text,
                page_number=ann.page_number,
                position_data=ann.position_data,
                color=ann.color,
                is_private=ann.is_private,
                tags=ann.tags,
            )
            db.add(new_ann)
            new_annotations.append(new_ann)

        await db.commit()

        # 刷新所有对象
        for ann in new_annotations:
            await db.refresh(ann)

        return new_annotations


# 创建CRUD实例
crud_annotation = CRUDAnnotation(Annotation)
