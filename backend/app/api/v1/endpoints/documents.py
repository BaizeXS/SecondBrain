"""Document endpoints v2 - 使用服务层和CRUD层的完整版本."""


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
from app.services import DocumentService

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
    space = await crud.space.get(db, id=space_id)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="空间不存在",
        )

    if space.user_id != current_user.id:
        # 检查协作权限
        access = await crud.space.get_user_access(
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
        document = await DocumentService.create_document(
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

            document = await crud.document.update(db, db_obj=document, obj_in=update_data)

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
        space = await crud.space.get(db, id=space_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="空间不存在",
            )

        # 检查访问权限
        if space.user_id != current_user.id and not space.is_public:
            access = await crud.space.get_user_access(
                db, space_id=space_id, user_id=current_user.id
            )
            if not access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此空间",
                )

        # 获取空间文档
        if search:
            documents = await crud.document.search(
                db, space_id=space_id, query=search, skip=skip, limit=limit
            )
        else:
            documents = await crud.document.get_by_space(
                db, space_id=space_id, skip=skip, limit=limit, status=status
            )
    else:
        # 获取用户的所有文档
        documents = await crud.document.get_user_documents(
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
    document = await DocumentService.get_document_by_id(db, document_id, current_user)

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
    document = await DocumentService.get_document_by_id(db, document_id, current_user)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在或无权访问",
        )

    # 检查编辑权限
    space = await crud.space.get(db, id=document.space_id)
    if space and space.user_id != current_user.id:
        access = await crud.space.get_user_access(
            db, space_id=document.space_id, user_id=current_user.id
        )
        if not access or not access.can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权编辑此文档",
            )

    # 更新文档
    try:
        updated_document = await crud.document.update(
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
    document = await DocumentService.get_document_by_id(db, document_id, current_user)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在或无权访问",
        )

    # 检查删除权限
    space = await crud.space.get(db, id=document.space_id)
    if space and space.user_id != current_user.id:
        access = await crud.space.get_user_access(
            db, space_id=document.space_id, user_id=current_user.id
        )
        if not access or not access.can_delete:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此文档",
            )

    # 删除文档
    try:
        await DocumentService.delete_document(db, document)
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
    document = await DocumentService.get_document_by_id(db, document_id, current_user)

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
