"""Document endpoints v2 - 使用服务层和CRUD层的完整版本."""

from datetime import datetime
from typing import Any, List

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core.auth import get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User
from app.schemas.documents import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUpdate,
)
from app.schemas.web_import import (
    URLImportRequest,
    BatchURLImportRequest,
    URLImportResponse,
    WebSnapshotResponse,
    URLAnalysisRequest,
    URLAnalysisResponse,
)
from app.services import document_service

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    space_id: int = Form(..., description="空间ID"),
    file: UploadFile = File(..., description="要上传的文件"),
    title: str | None = Form(None, description="文档标题"),
    tags: str | None = Form(None, description="标签，逗号分隔"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DocumentResponse:
    """上传文档到知识空间."""
    # 检查空间权限
    space = await crud.crud_space.get(db, id=space_id)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="空间不存在",
        )

    if space.user_id != current_user.id:
        # 检查协作权限
        access = await crud.crud_space.get_user_access(
            db, space_id=space_id, user_id=current_user.id
        )
        if not access or not access.can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权在此空间上传文档",
            )

    # 验证文件
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法识别文件类型",
        )

    if file.content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file.content_type}",
        )

    # 检查文件大小
    content = await file.read()
    file_size = len(content)

    if file_size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小超过限制（{settings.MAX_FILE_SIZE_MB}MB）",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件为空",
        )

    # 处理标签
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

    try:
        # 创建文档（简化版本，直接存储内容）
        document = await document_service.create_document(
            db,
            space_id=space_id,
            filename=file.filename or "未命名文档",
            content=content.decode("utf-8", errors="ignore"),
            content_type=file.content_type,
            file_size=file_size,
            user=current_user,
        )

        # 更新文档的标题和标签
        if title or tag_list:
            update_data = {}
            if title:
                update_data["title"] = title
            if tag_list:
                update_data["tags"] = tag_list

            document = await crud.crud_document.update(db, db_obj=document, obj_in=update_data)

        return DocumentResponse.model_validate(document)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传文档失败: {str(e)}",
        )


@router.get("/", response_model=DocumentListResponse)
async def get_documents(
    space_id: int | None = Query(None, description="空间ID"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    search: str | None = Query(None, description="搜索关键词"),
    status: str | None = Query(None, description="处理状态"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DocumentListResponse:
    """获取文档列表."""
    if space_id:
        # 检查空间权限
        space = await crud.crud_space.get(db, id=space_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="空间不存在",
            )

        # 检查访问权限
        if space.user_id != current_user.id and not space.is_public:
            access = await crud.crud_space.get_user_access(
                db, space_id=space_id, user_id=current_user.id
            )
            if not access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此空间",
                )

        # 获取空间文档
        if search:
            documents = await crud.crud_document.search(
                db, space_id=space_id, query=search, skip=skip, limit=limit
            )
        else:
            documents = await crud.crud_document.get_by_space(
                db, space_id=space_id, skip=skip, limit=limit, status=status
            )
    else:
        # 获取用户的所有文档
        documents = await crud.crud_document.get_user_documents(
            db, user_id=current_user.id, skip=skip, limit=limit
        )

        # 应用搜索筛选
        if search:
            documents = [
                d for d in documents
                if search.lower() in (d.title or d.filename).lower()
                or (d.content and search.lower() in d.content.lower())
            ]

        if status:
            documents = [d for d in documents if d.processing_status == status]

    # 获取总数
    total = len(documents)

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        has_next=total > skip + limit,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DocumentResponse:
    """获取文档详情."""
    document = await document_service.get_document_by_id(db, document_id, current_user)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在或无权访问",
        )

    return DocumentResponse.model_validate(document)


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_data: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DocumentResponse:
    """更新文档信息."""
    # 获取文档
    document = await document_service.get_document_by_id(db, document_id, current_user)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在或无权访问",
        )

    # 检查编辑权限
    space = await crud.space.get(db, id=document.space_id)
    if space and space.user_id != current_user.id:
        access = await crud.crud_space.get_user_access(
            db, space_id=document.space_id, user_id=current_user.id
        )
        if not access or not access.can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权编辑此文档",
            )

    # 更新文档
    try:
        updated_document = await crud.crud_document.update(
            db, db_obj=document, obj_in=document_data
        )
        return DocumentResponse.model_validate(updated_document)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新文档失败: {str(e)}",
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """删除文档."""
    # 获取文档
    document = await document_service.get_document_by_id(db, document_id, current_user)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在或无权访问",
        )

    # 检查删除权限
    space = await crud.space.get(db, id=document.space_id)
    if space and space.user_id != current_user.id:
        access = await crud.crud_space.get_user_access(
            db, space_id=document.space_id, user_id=current_user.id
        )
        if not access or not access.can_delete:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此文档",
            )

    # 删除文档
    try:
        await document_service.delete_document(db, document)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文档失败: {str(e)}",
        )


@router.post("/{document_id}/download")
async def download_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """下载文档文件."""
    # 获取文档
    document = await document_service.get_document_by_id(db, document_id, current_user)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在或无权访问",
        )

    # 注意：在简化版本中，文件内容存储在数据库中
    # 在实际应用中，应该从文件系统或对象存储中读取
    if not document.content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档内容不存在",
        )

    # 创建临时文件返回
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=f"_{document.filename}") as tmp:
        tmp.write(document.content)
        tmp_path = tmp.name

    return FileResponse(
        path=tmp_path,
        filename=document.filename,
        media_type=document.content_type,
    )


@router.get("/{document_id}/preview")
async def get_document_preview(
    document_id: int,
    page: int | None = Query(None, ge=1, description="PDF页码"),
    format: str = Query("html", description="预览格式: html/text/json"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取文档预览内容."""
    # 获取文档
    document = await crud.crud_document.get(db, id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在",
        )
    
    # 检查权限
    if document.user_id != current_user.id:
        # 检查空间权限
        if document.space_id:
            space = await crud.crud_space.get(db, id=document.space_id)
            if not space or (not space.is_public and space.user_id != current_user.id):
                # 检查协作权限
                access = await crud.crud_space.get_user_access(
                    db, space_id=document.space_id, user_id=current_user.id
                )
                if not access:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权访问此文档",
                    )
    
    # 根据文档类型返回预览
    if document.content_type and "pdf" in document.content_type.lower():
        # PDF文档
        return {
            "type": "pdf",
            "filename": document.filename,
            "title": document.title,
            "file_url": document.file_url or f"/api/v1/documents/{document_id}/download",
            "page_count": document.meta_data.get("page_count") if document.meta_data else None,
            "current_page": page,
            "content": document.content if page == 1 else None,  # 第一页返回提取的文本
        }
    elif document.content_type and any(img in document.content_type.lower() for img in ["image", "jpg", "jpeg", "png", "gif"]):
        # 图片文档
        return {
            "type": "image",
            "filename": document.filename,
            "title": document.title,
            "file_url": document.file_url or f"/api/v1/documents/{document_id}/download",
            "width": document.meta_data.get("width") if document.meta_data else None,
            "height": document.meta_data.get("height") if document.meta_data else None,
        }
    elif document.content:
        # 文本类文档
        content = document.content
        
        # 根据格式返回
        if format == "html":
            # 简单的Markdown到HTML转换
            try:
                import markdown
                html_content = markdown.markdown(content, extensions=['extra', 'codehilite'])
            except:
                html_content = f"<pre>{content}</pre>"
            
            return {
                "type": "text",
                "format": "html",
                "filename": document.filename,
                "title": document.title,
                "content": html_content,
                "language": document.language,
            }
        elif format == "json":
            return {
                "type": "text",
                "format": "json",
                "filename": document.filename,
                "title": document.title,
                "content": content,
                "summary": document.summary,
                "language": document.language,
                "metadata": document.meta_data,
            }
        else:  # text
            return {
                "type": "text",
                "format": "text",
                "filename": document.filename,
                "title": document.title,
                "content": content,
                "language": document.language,
            }
    else:
        # 二进制文件或未处理的文档
        return {
            "type": "binary",
            "filename": document.filename,
            "title": document.title,
            "file_url": document.file_url or f"/api/v1/documents/{document_id}/download",
            "content_type": document.content_type,
            "file_size": document.file_size,
            "message": "此文档类型不支持预览，请下载查看",
        }


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: int,
    start: int = Query(0, ge=0, description="起始位置"),
    length: int = Query(5000, ge=100, le=50000, description="内容长度"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取文档的文本内容（支持分页）."""
    # 获取文档
    document = await crud.crud_document.get(db, id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在",
        )
    
    # 检查权限（同上）
    if document.user_id != current_user.id:
        if document.space_id:
            space = await crud.crud_space.get(db, id=document.space_id)
            if not space or (not space.is_public and space.user_id != current_user.id):
                access = await crud.crud_space.get_user_access(
                    db, space_id=document.space_id, user_id=current_user.id
                )
                if not access:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权访问此文档",
                    )
    
    if not document.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此文档没有可用的文本内容",
        )
    
    # 获取内容片段
    total_length = len(document.content)
    end = min(start + length, total_length)
    content_slice = document.content[start:end]
    
    return {
        "document_id": document_id,
        "title": document.title,
        "content": content_slice,
        "start": start,
        "end": end,
        "total_length": total_length,
        "has_more": end < total_length,
    }


@router.post("/import-url", response_model=URLImportResponse, status_code=status.HTTP_201_CREATED)
async def import_url(
    import_data: URLImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> URLImportResponse:
    """从URL导入网页内容到知识空间."""
    # 检查空间权限
    space = await crud.space.get(db, id=import_data.space_id)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="空间不存在",
        )
    
    if space.user_id != current_user.id:
        # 检查协作权限
        access = await crud.crud_space.get_user_access(
            db, space_id=import_data.space_id, user_id=current_user.id
        )
        if not access or not access.can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权在此空间导入文档",
            )
    
    # 导入网页
    result = await document_service.import_from_url(
        db,
        url=str(import_data.url),
        space_id=import_data.space_id,
        user=current_user,
        title=import_data.title,
        tags=import_data.tags,
        save_snapshot=import_data.save_snapshot,
    )
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "导入失败"),
        )
    
    # 获取文档详情
    document = await crud.crud_document.get(db, id=result["document_id"])
    
    return URLImportResponse(
        document_id=document.id,
        url=str(import_data.url),
        title=document.title,
        status="success",
        metadata=result.get("metadata"),
        created_at=document.created_at,
    )


@router.post("/batch-import-urls", response_model=List[URLImportResponse])
async def batch_import_urls(
    import_data: BatchURLImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[URLImportResponse]:
    """批量从URL导入网页内容."""
    # 检查空间权限（同上）
    space = await crud.space.get(db, id=import_data.space_id)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="空间不存在",
        )
    
    if space.user_id != current_user.id:
        access = await crud.crud_space.get_user_access(
            db, space_id=import_data.space_id, user_id=current_user.id
        )
        if not access or not access.can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权在此空间导入文档",
            )
    
    # 批量导入
    results = await document_service.batch_import_urls(
        db,
        urls=[str(url) for url in import_data.urls],
        space_id=import_data.space_id,
        user=current_user,
        tags=import_data.tags,
        save_snapshot=import_data.save_snapshot,
    )
    
    # 构建响应
    responses = []
    for result in results:
        if result["status"] == "success":
            document = await crud.crud_document.get(db, id=result["document_id"])
            responses.append(URLImportResponse(
                document_id=document.id,
                url=result["url"],
                title=document.title,
                status="success",
                metadata=result.get("metadata"),
                created_at=document.created_at,
            ))
        else:
            responses.append(URLImportResponse(
                document_id=0,
                url=result["url"],
                title="",
                status="error",
                error=result.get("error"),
                created_at=datetime.now(),
            ))
    
    return responses


@router.get("/{document_id}/snapshot", response_model=WebSnapshotResponse)
async def get_web_snapshot(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WebSnapshotResponse:
    """获取网页文档的快照."""
    snapshot = await document_service.get_web_snapshot(db, document_id, current_user)
    
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="快照不存在或该文档不是网页文档",
        )
    
    return WebSnapshotResponse(**snapshot)


@router.post("/analyze-url", response_model=URLAnalysisResponse)
async def analyze_url(
    analysis_data: URLAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
) -> URLAnalysisResponse:
    """分析URL内容（不保存）."""
    analysis = await document_service.analyze_url(str(analysis_data.url))
    
    if not analysis.get("can_import"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=analysis.get("error", "无法分析该URL"),
        )
    
    return URLAnalysisResponse(**analysis)
