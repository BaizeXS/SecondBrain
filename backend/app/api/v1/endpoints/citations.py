"""Citation management endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.models import User
from app.schemas.citation import (
    BibTeXExportRequest,
    BibTeXImportRequest,
    BibTeXImportResponse,
    CitationCreate,
    CitationListResponse,
    CitationResponse,
    CitationSearchRequest,
    CitationStyleFormat,
    CitationUpdate,
    FormattedCitation,
)
from app.services.citation_service import citation_service

router = APIRouter()


@router.post("/import-bibtex", response_model=BibTeXImportResponse)
async def import_bibtex(
    import_data: BibTeXImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BibTeXImportResponse:
    """导入BibTeX格式的引用."""
    # 检查空间权限
    space = await crud.crud_space.get(db, id=import_data.space_id)
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
                detail="无权在此空间导入引用",
            )
    
    # 导入BibTeX
    result = await citation_service.import_bibtex(
        db,
        bibtex_content=import_data.bibtex_content,
        space_id=import_data.space_id,
        user=current_user,
        create_documents=import_data.create_documents,
        tags=import_data.tags,
    )
    
    return BibTeXImportResponse(**result)


@router.get("/", response_model=CitationListResponse)
async def get_citations(
    space_id: int | None = Query(None, description="空间ID"),
    document_id: int | None = Query(None, description="文档ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CitationListResponse:
    """获取引用列表."""
    if document_id:
        # 检查文档权限
        from app.services import DocumentService
        document = await DocumentService.get_document_by_id(db, document_id, current_user)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在或无权访问",
            )
        citations = await crud.crud_citation.get_by_document(db, document_id=document_id)
    elif space_id:
        # 检查空间权限
        space = await crud.crud_space.get(db, id=space_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="空间不存在",
            )
        
        if space.user_id != current_user.id and not space.is_public:
            access = await crud.crud_space.get_user_access(
                db, space_id=space_id, user_id=current_user.id
            )
            if not access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此空间",
                )
        
        citations = await crud.crud_citation.get_by_space(
            db, space_id=space_id, skip=skip, limit=limit
        )
    else:
        # 获取用户的所有引用
        citations = await crud.crud_citation.get_user_citations(
            db, user_id=current_user.id, skip=skip, limit=limit
        )
    
    total = len(citations)
    
    return CitationListResponse(
        citations=[CitationResponse.model_validate(c) for c in citations],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        has_next=total > skip + limit,
    )


@router.get("/{citation_id}", response_model=CitationResponse)
async def get_citation(
    citation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CitationResponse:
    """获取引用详情."""
    citation = await crud.crud_citation.get(db, id=citation_id)
    
    if not citation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="引用不存在",
        )
    
    # 检查权限
    if citation.user_id != current_user.id:
        # 检查空间权限
        space = await crud.crud_space.get(db, id=citation.space_id)
        if not space or (not space.is_public and space.user_id != current_user.id):
            access = await crud.crud_space.get_user_access(
                db, space_id=citation.space_id, user_id=current_user.id
            )
            if not access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此引用",
                )
    
    return CitationResponse.model_validate(citation)


@router.post("/", response_model=CitationResponse, status_code=status.HTTP_201_CREATED)
async def create_citation(
    space_id: int = Query(..., description="空间ID"),
    citation_data: CitationCreate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CitationResponse:
    """创建新引用."""
    # 检查空间权限
    space = await crud.space.get(db, id=space_id)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="空间不存在",
        )
    
    if space.user_id != current_user.id:
        access = await crud.crud_space.get_user_access(
            db, space_id=space_id, user_id=current_user.id
        )
        if not access or not access.can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权在此空间创建引用",
            )
    
    # 检查bibtex_key是否已存在
    existing = await crud.crud_citation.get_by_bibtex_key(
        db, bibtex_key=citation_data.bibtex_key, user_id=current_user.id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="引用键已存在",
        )
    
    # 创建引用
    citation = await crud.crud_citation.create(
        db,
        obj_in=citation_data,
        user_id=current_user.id,
        space_id=space_id,
    )
    
    return CitationResponse.model_validate(citation)


@router.put("/{citation_id}", response_model=CitationResponse)
async def update_citation(
    citation_id: int,
    citation_data: CitationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CitationResponse:
    """更新引用信息."""
    citation = await crud.crud_citation.get(db, id=citation_id)
    
    if not citation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="引用不存在",
        )
    
    # 检查权限
    if citation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权编辑此引用",
        )
    
    # 更新引用
    citation = await crud.crud_citation.update(db, db_obj=citation, obj_in=citation_data)
    
    return CitationResponse.model_validate(citation)


@router.delete("/{citation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_citation(
    citation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """删除引用."""
    citation = await crud.crud_citation.get(db, id=citation_id)
    
    if not citation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="引用不存在",
        )
    
    # 检查权限
    if citation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此引用",
        )
    
    # 删除引用
    await crud.crud_citation.remove(db, id=citation_id)


@router.post("/search", response_model=CitationListResponse)
async def search_citations(
    search_data: CitationSearchRequest,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CitationListResponse:
    """搜索引用."""
    citations = await citation_service.search_citations(
        db,
        query=search_data.query,
        user=current_user,
        space_id=search_data.space_id,
        citation_type=search_data.citation_type,
        year_from=search_data.year_from,
        year_to=search_data.year_to,
        authors=search_data.authors,
        skip=skip,
        limit=limit,
    )
    
    total = len(citations)
    
    return CitationListResponse(
        citations=[CitationResponse.model_validate(c) for c in citations],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        has_next=total > skip + limit,
    )


@router.post("/export")
async def export_citations(
    export_data: BibTeXExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """导出引用."""
    # 如果指定了空间，检查权限
    if export_data.space_id:
        space = await crud.crud_space.get(db, id=export_data.space_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="空间不存在",
            )
        
        if space.user_id != current_user.id and not space.is_public:
            access = await crud.crud_space.get_user_access(
                db, space_id=export_data.space_id, user_id=current_user.id
            )
            if not access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此空间",
                )
    
    # 导出引用
    content = await citation_service.export_citations(
        db,
        user=current_user,
        citation_ids=export_data.citation_ids,
        space_id=export_data.space_id,
        format=export_data.format,
    )
    
    # 设置响应头
    if export_data.format == "bibtex":
        media_type = "text/plain"
        filename = "references.bib"
    elif export_data.format == "json":
        media_type = "application/json"
        filename = "references.json"
    elif export_data.format == "csv":
        media_type = "text/csv"
        filename = "references.csv"
    else:
        media_type = "text/plain"
        filename = "references.txt"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.post("/format", response_model=List[FormattedCitation])
async def format_citations(
    format_data: CitationStyleFormat,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[FormattedCitation]:
    """格式化引用（APA、MLA等格式）."""
    formatted = await citation_service.format_citations(
        db,
        citation_ids=format_data.citation_ids,
        style=format_data.style,
        user=current_user,
    )
    
    return [FormattedCitation(**f) for f in formatted]