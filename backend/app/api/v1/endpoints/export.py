"""Export endpoints."""

import io
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.crud.conversation import crud_conversation
from app.crud.document import crud_document
from app.crud.message import crud_message
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
            # 合并多个笔记为一个PDF
            notes_data = []
            for note in notes:
                note_dict = {
                    "id": note.id,
                    "title": note.title,
                    "content": note.content,
                    "created_at": note.created_at.isoformat(),
                    "updated_at": note.updated_at.isoformat(),
                    "version": note.version,
                    "tags": note.tags or [],
                }
                notes_data.append(note_dict)

            content = await export_service.export_notes_to_pdf(
                notes_data,
                title=f"{notes[0].space.name if notes[0].space else 'SecondBrain'} 笔记合集",
                include_metadata=request.include_metadata,
            )

            filename = "notes_collection.pdf"
            return StreamingResponse(
                io.BytesIO(content),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(len(content)),
                },
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
            # 合并多个笔记为一个DOCX
            notes_data = []
            for note in notes:
                note_dict = {
                    "id": note.id,
                    "title": note.title,
                    "content": note.content,
                    "created_at": note.created_at.isoformat(),
                    "updated_at": note.updated_at.isoformat(),
                    "version": note.version,
                    "tags": note.tags or [],
                }
                notes_data.append(note_dict)

            content = await export_service.export_notes_to_docx(
                notes_data,
                title=f"{notes[0].space.name if notes[0].space else 'SecondBrain'} 笔记合集",
                include_metadata=request.include_metadata,
            )

            filename = "notes_collection.docx"
            return StreamingResponse(
                io.BytesIO(content),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(len(content)),
                },
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
            # 合并多个文档为一个PDF
            docs_data = []
            for doc in documents:
                doc_dict = {
                    "id": doc.id,
                    "filename": doc.filename,
                    "title": doc.title or doc.filename,
                    "mime_type": doc.content_type,
                    "file_size": doc.file_size,
                    "created_at": doc.created_at.isoformat(),
                    "tags": doc.tags or [],
                    "extracted_text": getattr(doc, "extracted_text", doc.content) or "",
                }
                docs_data.append(doc_dict)

            content = await export_service.export_documents_to_pdf(
                docs_data,
                title=f"{documents[0].space.name if documents[0].space else 'SecondBrain'} 文档合集",
                include_content=True,
            )

            filename = "documents_collection.pdf"
            return StreamingResponse(
                io.BytesIO(content),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(len(content)),
                },
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
        documents = await crud_document.get_by_space(db, space_id=request.space_id)

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

    # 实现对话导出
    if request.format == "json":
        export_data = []

        for conv in conversations:
            # 获取对话消息
            messages = await crud_message.get_by_conversation(
                db, conversation_id=conv.id, limit=1000
            )

            # 转换数据格式
            conv_dict = {
                "id": conv.id,
                "title": conv.title,
                "space_id": conv.space_id,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "agent_id": conv.agent_id,
                "model": conv.model,
                "search_enabled": conv.search_enabled,
            }

            messages_list = []
            for msg in messages:
                msg_dict = {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "model": msg.model,
                    "parent_message_id": msg.parent_message_id,
                    "branch_name": msg.branch_name,
                }
                messages_list.append(msg_dict)

            # 导出单个对话
            if request.merge_into_one:
                export_item = await export_service.export_conversation_to_json(
                    conv_dict,
                    messages_list,
                    include_branches=request.include_branches,
                )
                export_data.append(export_item)
            else:
                # 单独导出
                export_item = await export_service.export_conversation_to_json(
                    conv_dict,
                    messages_list,
                    include_branches=request.include_branches,
                )

                filename = f"conversation_{conv.id}.json"
                content = json.dumps(export_item, ensure_ascii=False, indent=2)

                return StreamingResponse(
                    io.BytesIO(content.encode("utf-8")),
                    media_type="application/json",
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}",
                        "Content-Length": str(len(content.encode("utf-8"))),
                    },
                )

        # 合并导出
        if request.merge_into_one and len(conversations) > 1:
            filename = "conversations_export.json"
            content = json.dumps(export_data, ensure_ascii=False, indent=2)

            return StreamingResponse(
                io.BytesIO(content.encode("utf-8")),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(len(content.encode("utf-8"))),
                },
            )

    elif request.format == "markdown":
        # 导出为Markdown格式
        content_lines = []

        for conv in conversations:
            # 获取对话消息
            messages = await crud_message.get_by_conversation(
                db, conversation_id=conv.id, limit=1000
            )

            # 添加对话标题
            content_lines.append(f"# {conv.title}")
            content_lines.append("")
            content_lines.append(f"**创建时间**: {conv.created_at.isoformat()}")
            content_lines.append(f"**模型**: {conv.model or 'N/A'}")
            content_lines.append("")

            # 添加消息
            for msg in messages:
                role_label = "用户" if msg.role == "user" else "助手"
                content_lines.append(f"## {role_label}")
                content_lines.append("")
                content_lines.append(msg.content)
                content_lines.append("")
                content_lines.append("---")
                content_lines.append("")

        content = "\n".join(content_lines)
        filename = f"conversation_export_{int(datetime.now().timestamp())}.md"

        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(content.encode("utf-8"))),
            },
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的导出格式: {request.format}",
        )
