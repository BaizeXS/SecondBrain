"""Export endpoints."""

import io
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.crud.conversation import crud_conversation
from app.crud.document import crud_document
from app.crud.note import crud_note
from app.crud.space import crud_space
from app.models.models import User
from app.schemas.export import (
    ConversationExportRequest,
    DocumentExportRequest,
    ExportResponse,
    NoteExportRequest,
    SpaceExportRequest,
)
from app.services.export_service import export_service
from app.services.note_service import note_service

router = APIRouter()


@router.post("/notes", response_model=ExportResponse)
async def export_notes(
    request: NoteExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """导出笔记."""
    # 验证所有笔记的访问权限
    notes = []
    for note_id in request.note_ids:
        note = await crud_note.get(db, id=note_id)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"笔记 {note_id} 不存在",
            )
        if note.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权访问笔记 {note_id}",
            )
        notes.append(note)

    # 根据格式导出
    if request.format == "pdf":
        # 导出为PDF
        if request.merge_into_one and len(notes) > 1:
            # TODO: 实现多个笔记合并为一个PDF
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="暂不支持多个笔记合并为一个PDF",
            )
        else:
            # 导出单个笔记
            note = notes[0]
            versions = []
            if request.include_versions:
                versions = await note_service.get_version_history(
                    db, note_id=note.id, limit=10
                )

            # 转换为字典格式
            note_dict = {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "created_at": note.created_at.isoformat(),
                "updated_at": note.updated_at.isoformat(),
                "version": note.version,
                "tags": note.tags or [],
            }

            versions_list = []
            for v in versions:
                versions_list.append(
                    {
                        "version_number": v.version_number,
                        "created_at": v.created_at.isoformat(),
                        "change_summary": v.change_summary,
                    }
                )

            content = await export_service.export_note_to_pdf(
                note_dict,
                include_metadata=request.include_metadata,
                include_versions=request.include_versions,
                versions=versions_list,
            )

            filename = f"{note.title.replace(' ', '_')}.pdf"
            return StreamingResponse(
                io.BytesIO(content),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(len(content)),
                },
            )

    elif request.format == "docx":
        # 导出为DOCX
        if request.merge_into_one and len(notes) > 1:
            # TODO: 实现多个笔记合并为一个DOCX
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="暂不支持多个笔记合并为一个DOCX",
            )
        else:
            # 导出单个笔记
            note = notes[0]
            versions = []
            if request.include_versions:
                versions = await note_service.get_version_history(
                    db, note_id=note.id, limit=10
                )

            # 转换为字典格式
            note_dict = {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "created_at": note.created_at.isoformat(),
                "updated_at": note.updated_at.isoformat(),
                "version": note.version,
                "tags": note.tags or [],
                "author": current_user.username,
            }

            versions_list = []
            for v in versions:
                versions_list.append(
                    {
                        "version_number": v.version_number,
                        "created_at": v.created_at.isoformat(),
                        "change_summary": v.change_summary,
                    }
                )

            content = await export_service.export_note_to_docx(
                note_dict,
                include_metadata=request.include_metadata,
                include_versions=request.include_versions,
                versions=versions_list,
            )

            filename = f"{note.title.replace(' ', '_')}.docx"
            return StreamingResponse(
                io.BytesIO(content),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(len(content)),
                },
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的导出格式: {request.format}",
        )


@router.post("/documents", response_model=ExportResponse)
async def export_documents(
    request: DocumentExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """导出文档."""
    # 验证所有文档的访问权限
    documents = []
    for doc_id in request.document_ids:
        doc = await crud_document.get(db, id=doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文档 {doc_id} 不存在",
            )
        if doc.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权访问文档 {doc_id}",
            )
        documents.append(doc)

    # 根据格式导出
    if request.format == "pdf":
        # 导出为PDF
        if request.merge_into_one and len(documents) > 1:
            # TODO: 实现多个文档合并为一个PDF
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="暂不支持多个文档合并为一个PDF",
            )
        else:
            # 导出单个文档
            doc = documents[0]

            # 获取标注
            annotations: list[dict[str, Any]] = []
            if request.include_annotations:
                # TODO: 获取文档标注
                pass

            # 转换为字典格式
            doc_dict = {
                "id": doc.id,
                "title": doc.title,
                "filename": doc.filename,
                "content": doc.content,
                "created_at": doc.created_at.isoformat(),
                "file_size": doc.file_size,
            }

            content = await export_service.export_document_to_pdf(
                doc_dict,
                include_annotations=request.include_annotations,
                annotations=annotations,
            )

            filename = f"{doc.title or doc.filename.split('.')[0]}.pdf"
            return StreamingResponse(
                io.BytesIO(content),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(len(content)),
                },
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的导出格式: {request.format}",
        )


@router.post("/space", response_model=ExportResponse)
async def export_space(
    request: SpaceExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """导出空间."""
    # 验证空间访问权限
    space = await crud_space.get(db, id=request.space_id)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="空间不存在",
        )

    # 检查用户权限
    if space.user_id != current_user.id:
        # TODO: 检查协作者权限
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此空间",
        )

    # 获取空间内的文档和笔记
    documents = []
    notes = []

    if request.include_documents:
        documents = await crud_document.get_by_space(
            db, space_id=request.space_id
        )

    if request.include_notes:
        notes = await crud_note.get_by_space(
            db, space_id=request.space_id, user_id=current_user.id
        )

    # 根据格式导出
    if request.format == "pdf":
        # 转换为字典格式
        space_dict = {
            "id": space.id,
            "name": space.name,
            "description": space.description,
            "created_at": space.created_at.isoformat(),
        }

        docs_list = []
        for doc in documents:
            docs_list.append(
                {
                    "id": doc.id,
                    "title": doc.title,
                    "filename": doc.filename,
                    "summary": doc.summary,
                    "content": doc.content if request.include_content else None,
                }
            )

        notes_list = []
        for note in notes:
            notes_list.append(
                {
                    "id": note.id,
                    "title": note.title,
                    "content": note.content if request.include_content else None,
                }
            )

        content = await export_service.export_space_to_pdf(
            space_dict,
            docs_list,
            notes_list,
            include_content=request.include_content,
        )

        filename = f"{space.name.replace(' ', '_')}_export.pdf"
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(content)),
            },
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的导出格式: {request.format}",
        )


@router.post("/conversations", response_model=ExportResponse)
async def export_conversations(
    request: ConversationExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """导出对话."""
    # 验证所有对话的访问权限
    conversations = []
    for conv_id in request.conversation_ids:
        conv = await crud_conversation.get(db, id=conv_id)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"对话 {conv_id} 不存在",
            )
        if conv.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权访问对话 {conv_id}",
            )
        conversations.append(conv)

    # TODO: 实现对话导出
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="对话导出功能正在开发中",
    )
