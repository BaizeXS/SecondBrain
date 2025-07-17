"""Annotation service for handling document annotations."""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.annotation import crud_annotation
from app.crud.document import crud_document
from app.models.models import Annotation
from app.schemas.annotation import (
    AnnotationCreate,
    PDFAnnotationData,
    PDFHighlight,
)

logger = logging.getLogger(__name__)


class AnnotationService:
    """标注服务类."""

    async def create_pdf_highlight(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
        highlight: PDFHighlight,
    ) -> Annotation:
        """创建PDF高亮标注."""
        try:
            # 构建位置数据
            position_data = {
                "page": highlight.page,
                "rects": highlight.rects,
                "text": highlight.text,
            }

            # 创建标注
            annotation_data = AnnotationCreate(
                document_id=document_id,
                type="highlight",
                selected_text=highlight.text,
                content=highlight.note,
                page_number=highlight.page,
                position_data=position_data,
                color=highlight.color,
            )

            annotation = await crud_annotation.create(
                db=db,
                obj_in=annotation_data,
                user_id=user_id,
            )

            return annotation

        except Exception as e:
            logger.error(f"Error creating PDF highlight: {str(e)}")
            raise

    async def create_pdf_underline(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
        underline: PDFHighlight,
    ) -> Annotation:
        """创建PDF下划线标注."""
        try:
            # 构建位置数据
            position_data = {
                "page": underline.page,
                "rects": underline.rects,
                "text": underline.text,
            }

            # 创建标注
            annotation_data = AnnotationCreate(
                document_id=document_id,
                type="underline",
                selected_text=underline.text,
                content=underline.note,
                page_number=underline.page,
                position_data=position_data,
                color=underline.color or "#FF0000",  # 默认红色下划线
            )

            annotation = await crud_annotation.create(
                db=db,
                obj_in=annotation_data,
                user_id=user_id,
            )

            return annotation

        except Exception as e:
            logger.error(f"Error creating PDF underline: {str(e)}")
            raise

    async def batch_create_pdf_annotations(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
        pdf_data: PDFAnnotationData,
    ) -> list[Annotation]:
        """批量创建PDF标注."""
        try:
            annotations = []

            # 创建高亮
            for highlight in pdf_data.highlights:
                ann = await self.create_pdf_highlight(
                    db, document_id, user_id, highlight
                )
                annotations.append(ann)

            # 创建下划线
            for underline in pdf_data.underlines:
                ann = await self.create_pdf_underline(
                    db, document_id, user_id, underline
                )
                annotations.append(ann)

            # 创建笔记
            for note_data in pdf_data.notes:
                annotation_data = AnnotationCreate(
                    document_id=document_id,
                    type="note",
                    content=note_data.get("content", ""),
                    page_number=note_data.get("page"),
                    position_data=note_data.get("position"),
                )

                ann = await crud_annotation.create(
                    db=db,
                    obj_in=annotation_data,
                    user_id=user_id,
                )
                annotations.append(ann)

            # 创建书签
            for bookmark_data in pdf_data.bookmarks:
                annotation_data = AnnotationCreate(
                    document_id=document_id,
                    type="bookmark",
                    content=bookmark_data.get("title", ""),
                    page_number=bookmark_data.get("page"),
                    position_data={"level": bookmark_data.get("level", 0)},
                )

                ann = await crud_annotation.create(
                    db=db,
                    obj_in=annotation_data,
                    user_id=user_id,
                )
                annotations.append(ann)

            return annotations

        except Exception as e:
            logger.error(f"Error batch creating PDF annotations: {str(e)}")
            raise

    async def get_pdf_annotations_by_page(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
        page_number: int,
    ) -> PDFAnnotationData:
        """获取PDF指定页的所有标注."""
        try:
            # 获取该页的所有标注
            annotations = await crud_annotation.get_by_document(
                db=db,
                document_id=document_id,
                user_id=user_id,
                page_number=page_number,
            )

            # 整理成PDF标注数据格式
            highlights = []
            underlines = []
            notes = []
            bookmarks = []

            for ann in annotations:
                if ann.type == "highlight" and ann.position_data and ann.page_number:
                    highlights.append(PDFHighlight(
                        page=ann.page_number,
                        text=ann.selected_text or "",
                        rects=ann.position_data.get("rects", []),
                        color=ann.color or "#FFFF00",
                        note=ann.content,
                    ))
                elif ann.type == "underline" and ann.position_data and ann.page_number:
                    underlines.append(PDFHighlight(
                        page=ann.page_number,
                        text=ann.selected_text or "",
                        rects=ann.position_data.get("rects", []),
                        color=ann.color or "#FF0000",
                        note=ann.content,
                    ))
                elif ann.type == "note":
                    notes.append({
                        "content": ann.content,
                        "page": ann.page_number,
                        "position": ann.position_data,
                    })
                elif ann.type == "bookmark":
                    bookmarks.append({
                        "title": ann.content,
                        "page": ann.page_number,
                        "level": ann.position_data.get("level", 0)
                            if ann.position_data else 0,
                    })

            return PDFAnnotationData(
                highlights=highlights,
                underlines=underlines,
                notes=notes,
                bookmarks=bookmarks,
            )

        except Exception as e:
            logger.error(f"Error getting PDF annotations by page: {str(e)}")
            raise

    async def export_annotations(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
        format: str = "json",
    ) -> dict[str, Any] | str:
        """导出文档的所有标注."""
        try:
            # 获取文档信息
            document = await crud_document.get(db=db, id=document_id)
            if not document or document.user_id != user_id:
                raise ValueError("文档不存在或无权访问")

            # 获取所有标注
            annotations = await crud_annotation.get_by_document(
                db=db,
                document_id=document_id,
                user_id=user_id,
                limit=10000,  # 获取所有标注
            )

            if format == "json":
                # JSON格式导出
                export_data = {
                    "document": {
                        "id": document.id,
                        "title": document.title or document.filename,
                        "filename": document.filename,
                    },
                    "annotations": [
                        {
                            "id": ann.id,
                            "type": ann.type,
                            "content": ann.content,
                            "selected_text": ann.selected_text,
                            "page_number": ann.page_number,
                            "position_data": ann.position_data,
                            "color": ann.color,
                            "created_at": ann.created_at.isoformat(),
                        }
                        for ann in annotations
                    ],
                    "total": len(annotations),
                }
                return export_data

            elif format == "markdown":
                # Markdown格式导出
                md_lines = [
                    f"# {document.title or document.filename} - 标注汇总",
                    f"\n文件名: {document.filename}",
                    f"标注数量: {len(annotations)}",
                    "\n---\n",
                ]

                # 按页分组
                annotations_by_page: dict[int, list[Annotation]] = {}
                for ann in annotations:
                    page = ann.page_number or 0
                    if page not in annotations_by_page:
                        annotations_by_page[page] = []
                    annotations_by_page[page].append(ann)

                # 生成Markdown内容
                for page in sorted(annotations_by_page.keys()):
                    if page > 0:
                        md_lines.append(f"\n## 第 {page} 页\n")
                    else:
                        md_lines.append("\n## 通用标注\n")

                    for ann in annotations_by_page[page]:
                        if ann.type == "highlight":
                            md_lines.append(f"**高亮**: {ann.selected_text}")
                            if ann.content:
                                md_lines.append(f"  - 批注: {ann.content}")
                        elif ann.type == "underline":
                            md_lines.append(f"**下划线**: {ann.selected_text}")
                            if ann.content:
                                md_lines.append(f"  - 批注: {ann.content}")
                        elif ann.type == "note":
                            md_lines.append(f"**笔记**: {ann.content}")
                        elif ann.type == "bookmark":
                            md_lines.append(f"**书签**: {ann.content}")

                        md_lines.append("")  # 空行分隔

                return "\n".join(md_lines)

            else:
                raise ValueError(f"不支持的导出格式: {format}")

        except Exception as e:
            logger.error(f"Error exporting annotations: {str(e)}")
            raise

    async def merge_annotations(
        self,
        db: AsyncSession,
        source_document_id: int,
        target_document_id: int,
        user_id: int,
        page_offset: int = 0,
    ) -> list[Annotation]:
        """合并文档标注（用于文档合并场景）."""
        try:
            # 获取源文档的所有标注
            source_annotations = await crud_annotation.get_by_document(
                db=db,
                document_id=source_document_id,
                user_id=user_id,
                limit=10000,
            )

            # 创建新标注（调整页码）
            merged_annotations = []

            for ann in source_annotations:
                new_page = ann.page_number + page_offset if ann.page_number else None

                annotation_data = AnnotationCreate(
                    document_id=target_document_id,
                    type=ann.type,
                    content=ann.content,
                    selected_text=ann.selected_text,
                    page_number=new_page,
                    position_data=ann.position_data,
                    color=ann.color,
                )

                new_ann = await crud_annotation.create(
                    db=db,
                    obj_in=annotation_data,
                    user_id=user_id,
                )
                merged_annotations.append(new_ann)

            return merged_annotations

        except Exception as e:
            logger.error(f"Error merging annotations: {str(e)}")
            raise


# 全局标注服务实例
annotation_service = AnnotationService()
