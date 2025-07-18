"""Annotation endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.crud.annotation import crud_annotation
from app.crud.document import crud_document
from app.models.models import User
from app.schemas.annotation import (
    AnnotationBatchCreate,
    AnnotationCreate,
    AnnotationDetail,
    AnnotationExportRequest,
    AnnotationListResponse,
    AnnotationResponse,
    AnnotationStatistics,
    AnnotationUpdate,
    PDFAnnotationData,
)
from app.services.annotation_service import annotation_service

router = APIRouter()


@router.get("/document/{document_id}", response_model=AnnotationListResponse)
async def get_document_annotations(
    document_id: int,
    page_number: int | None = Query(None, description="页码筛选"),
    annotation_type: str | None = Query(None, description="标注类型筛选"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=200, description="返回的记录数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AnnotationListResponse:
    """获取文档的标注列表."""
    # 验证文档访问权限
    document = await crud_document.get(db=db, id=document_id)
    if not document or document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在或无权访问",
        )

    annotations = await crud_annotation.get_by_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
        page_number=page_number,
        annotation_type=annotation_type,
        skip=skip,
        limit=limit,
    )

    # 简化总数计算
    total = len(annotations)

    return AnnotationListResponse(
        annotations=[AnnotationResponse.model_validate(ann) for ann in annotations],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        has_next=total > skip + limit,
    )


@router.get("/document/{document_id}/pages", response_model=list[AnnotationResponse])
async def get_annotations_by_pages(
    document_id: int,
    start_page: int = Query(..., ge=1, description="起始页码"),
    end_page: int = Query(..., ge=1, description="结束页码"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[AnnotationResponse]:
    """获取文档指定页码范围的标注."""
    # 验证文档访问权限
    document = await crud_document.get(db=db, id=document_id)
    if not document or document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在或无权访问",
        )

    if start_page > end_page:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="起始页码不能大于结束页码",
        )

    annotations = await crud_annotation.get_by_document_pages(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
        start_page=start_page,
        end_page=end_page,
    )

    return [AnnotationResponse.model_validate(ann) for ann in annotations]


@router.get(
    "/document/{document_id}/pdf/{page_number}", response_model=PDFAnnotationData
)
async def get_pdf_page_annotations(
    document_id: int,
    page_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PDFAnnotationData:
    """获取PDF指定页的标注数据."""
    # 验证文档访问权限
    document = await crud_document.get(db=db, id=document_id)
    if not document or document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在或无权访问",
        )

    pdf_data = await annotation_service.get_pdf_annotations_by_page(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
        page_number=page_number,
    )

    return pdf_data


@router.get("/my", response_model=AnnotationListResponse)
async def get_my_annotations(
    annotation_type: str | None = Query(None, description="标注类型筛选"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AnnotationListResponse:
    """获取我的所有标注."""
    annotations, total = await crud_annotation.get_user_annotations(
        db=db,
        user_id=current_user.id,
        annotation_type=annotation_type,
        skip=skip,
        limit=limit,
    )

    return AnnotationListResponse(
        annotations=[AnnotationResponse.model_validate(ann) for ann in annotations],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        has_next=total > skip + limit,
    )


@router.get("/statistics", response_model=AnnotationStatistics)
async def get_annotation_statistics(
    document_id: int | None = Query(None, description="文档ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AnnotationStatistics:
    """获取标注统计信息."""
    # 如果指定了文档，验证访问权限
    if document_id:
        document = await crud_document.get(db=db, id=document_id)
        if not document or document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在或无权访问",
            )

    stats = await crud_annotation.get_statistics(
        db=db,
        user_id=current_user.id,
        document_id=document_id,
    )

    return AnnotationStatistics(**stats)


@router.get("/{annotation_id}", response_model=AnnotationDetail)
async def get_annotation(
    annotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AnnotationDetail:
    """获取标注详情."""
    annotation = await crud_annotation.get(db=db, id=annotation_id)
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标注不存在",
        )

    if annotation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此标注",
        )

    # 构建详情响应
    ann_dict = AnnotationResponse.model_validate(annotation).model_dump()
    detail = AnnotationDetail(
        **ann_dict,
        document_title=annotation.document.title if annotation.document else None,
        document_filename=annotation.document.filename if annotation.document else None,
        username=current_user.username,
    )

    return detail


@router.post(
    "/", response_model=AnnotationResponse, status_code=status.HTTP_201_CREATED
)
async def create_annotation(
    annotation_data: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AnnotationResponse:
    """创建标注."""
    # 验证文档访问权限
    document = await crud_document.get(db=db, id=annotation_data.document_id)
    if not document or document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在或无权访问",
        )

    annotation = await crud_annotation.create(
        db=db,
        obj_in=annotation_data,
        user_id=current_user.id,
    )

    return AnnotationResponse.model_validate(annotation)


@router.post(
    "/batch",
    response_model=list[AnnotationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def batch_create_annotations(
    batch_data: AnnotationBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[AnnotationResponse]:
    """批量创建标注."""
    # 验证文档访问权限
    document = await crud_document.get(db=db, id=batch_data.document_id)
    if not document or document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在或无权访问",
        )

    annotations = await crud_annotation.batch_create(
        db=db,
        document_id=batch_data.document_id,
        user_id=current_user.id,
        annotations_data=[
            AnnotationCreate(**ann.model_dump(), document_id=batch_data.document_id)
            for ann in batch_data.annotations
        ],
    )

    return [AnnotationResponse.model_validate(ann) for ann in annotations]


@router.post(
    "/pdf/batch",
    response_model=list[AnnotationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def batch_create_pdf_annotations(
    document_id: int,
    pdf_data: PDFAnnotationData,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[AnnotationResponse]:
    """批量创建PDF标注."""
    # 验证文档访问权限
    document = await crud_document.get(db=db, id=document_id)
    if not document or document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在或无权访问",
        )

    if not document.content_type or "pdf" not in document.content_type.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此文档不是PDF格式",
        )

    annotations = await annotation_service.batch_create_pdf_annotations(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
        pdf_data=pdf_data,
    )

    return [AnnotationResponse.model_validate(ann) for ann in annotations]


@router.put("/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    annotation_id: int,
    annotation_update: AnnotationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AnnotationResponse:
    """更新标注."""
    # 检查标注是否存在及权限
    annotation = await crud_annotation.get(db=db, id=annotation_id)
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标注不存在",
        )

    if annotation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此标注",
        )

    # 更新标注
    updated_annotation = await crud_annotation.update(
        db=db,
        db_obj=annotation,
        obj_in=annotation_update,
    )

    return AnnotationResponse.model_validate(updated_annotation)


@router.delete("/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_annotation(
    annotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """删除标注."""
    # 检查标注是否存在及权限
    annotation = await crud_annotation.get(db=db, id=annotation_id)
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标注不存在",
        )

    if annotation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此标注",
        )

    # 删除标注
    await crud_annotation.remove(db=db, id=annotation_id)


@router.post("/export", response_model=dict[str, Any])
async def export_annotations(
    request: AnnotationExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """导出标注."""
    # 验证所有文档的访问权限
    for doc_id in request.document_ids:
        document = await crud_document.get(db=db, id=doc_id)
        if not document or document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权访问文档 {doc_id}",
            )

    # 目前只支持单文档导出
    if len(request.document_ids) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="暂不支持多文档批量导出",
        )

    export_data = await annotation_service.export_annotations(
        db=db,
        document_id=request.document_ids[0],
        user_id=current_user.id,
        format=request.format,
    )

    if request.format == "markdown":
        return {"format": "markdown", "content": export_data}
    else:
        return {"format": request.format, "data": export_data}


@router.post("/copy", response_model=list[AnnotationResponse])
async def copy_annotations(
    source_document_id: int = Query(..., description="源文档ID"),
    target_document_id: int = Query(..., description="目标文档ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[AnnotationResponse]:
    """复制标注到另一个文档."""
    # 验证两个文档的访问权限
    source_doc = await crud_document.get(db=db, id=source_document_id)
    target_doc = await crud_document.get(db=db, id=target_document_id)

    if not source_doc or source_doc.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="源文档不存在或无权访问",
        )

    if not target_doc or target_doc.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标文档不存在或无权访问",
        )

    # 复制标注
    new_annotations = await crud_annotation.copy_annotations(
        db=db,
        source_document_id=source_document_id,
        target_document_id=target_document_id,
        user_id=current_user.id,
    )

    return [AnnotationResponse.model_validate(ann) for ann in new_annotations]
