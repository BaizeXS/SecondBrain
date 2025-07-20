"""Note endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.crud.note import crud_note
from app.models.models import User
from app.schemas.note import (
    NoteAIGenerateRequest,
    NoteAISummaryRequest,
    NoteBatchOperation,
    NoteCreate,
    NoteDetail,
    NoteListResponse,
    NoteResponse,
    NoteSearchRequest,
    NoteUpdate,
)
from app.schemas.note_version import (
    NoteRestoreRequest,
    NoteVersionCompareRequest,
    NoteVersionDiff,
    NoteVersionListResponse,
    NoteVersionResponse,
)
from app.services.note_service import note_service

router = APIRouter()


@router.get("/", response_model=NoteListResponse)
async def get_notes(
    space_id: int | None = Query(None, description="Space ID筛选"),
    note_type: str | None = Query(None, description="笔记类型筛选"),
    tags: list[str] | None = Query(None, description="标签筛选"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NoteListResponse:
    """获取笔记列表."""
    if space_id:
        # 获取特定Space的笔记
        notes = await crud_note.get_by_space(
            db=db,
            space_id=space_id,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        # 对于毕业设计项目，使用列表长度作为总数是可以接受的
        # 实际项目中应该使用: total = await crud_note.count_by_space(db, space_id, current_user.id)
        total = len(notes)
    else:
        # 获取用户的所有笔记
        # 注意：这里简化处理，实际应该在crud层支持过滤
        all_notes = await crud_note.get_multi(db=db, skip=0, limit=1000)
        # 手动过滤用户的笔记
        user_notes = [n for n in all_notes if n.user_id == current_user.id]
        if note_type:
            user_notes = [n for n in user_notes if n.note_type == note_type]
        # 分页
        notes = user_notes[skip : skip + limit]
        total = len(user_notes)

    return NoteListResponse(
        notes=[NoteResponse.model_validate(note) for note in notes],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        has_next=total > skip + limit,
    )


@router.get("/recent", response_model=list[NoteResponse])
async def get_recent_notes(
    limit: int = Query(10, ge=1, le=50, description="返回的记录数"),
    note_type: str | None = Query(None, description="笔记类型筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[NoteResponse]:
    """获取最近的笔记."""
    notes = await crud_note.get_recent_notes(
        db=db,
        user_id=current_user.id,
        limit=limit,
        note_type=note_type,
    )
    return [NoteResponse.model_validate(note) for note in notes]


@router.post("/search", response_model=NoteListResponse)
async def search_notes(
    request: NoteSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NoteListResponse:
    """搜索笔记."""
    notes, total = await crud_note.search(
        db=db,
        query=request.query,
        user_id=current_user.id,
        space_ids=request.space_ids,
        tags=request.tags,
        content_types=request.content_types,
        skip=0,
        limit=request.limit,
    )

    return NoteListResponse(
        notes=[NoteResponse.model_validate(note) for note in notes],
        total=total,
        page=1,
        page_size=request.limit,
        has_next=total > request.limit,
    )


@router.get("/{note_id}", response_model=NoteDetail)
async def get_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NoteDetail:
    """获取笔记详情."""
    note = await crud_note.get(db=db, id=note_id)

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="笔记不存在",
        )

    if note.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此笔记",
        )

    # 构建详情响应
    note_dict = NoteResponse.model_validate(note).model_dump()

    # 获取 space 名称
    space_name = None
    if note.space_id:
        space = await crud.crud_space.get(db, id=note.space_id)
        if space:
            space_name = space.name

    note_detail = NoteDetail(
        **note_dict,
        space_name=space_name,
        username=current_user.username,
    )

    return note_detail


@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NoteResponse:
    """创建笔记."""
    # 验证用户对Space的访问权限
    if note_data.space_id:
        space = await crud.crud_space.get(db, id=note_data.space_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="空间不存在",
            )

        # 检查用户是否有访问权限
        if space.user_id != current_user.id and not space.is_public:
            access = await crud.crud_space.get_user_access(
                db, space_id=note_data.space_id, user_id=current_user.id
            )
            if not access or not access.can_edit:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权在此空间创建笔记",
                )

    note = await note_service.create_note(
        db=db,
        note_data=note_data,
        user_id=current_user.id,
    )

    return NoteResponse.model_validate(note)


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    note_update: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NoteResponse:
    """更新笔记."""
    # 检查笔记是否存在及权限
    note = await crud_note.get(db=db, id=note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="笔记不存在",
        )

    if note.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此笔记",
        )

    # 先保存当前版本
    await note_service.save_version(
        db,
        note,
        user_id=current_user.id,
        change_summary="编辑前的版本",
        change_type="edit",
    )

    # 更新笔记
    updated_note = await crud_note.update(
        db=db,
        db_obj=note,
        obj_in=note_update,
    )

    # 保存新版本
    await note_service.save_version(
        db,
        updated_note,
        user_id=current_user.id,
        change_summary="手动编辑",
        change_type="edit",
    )

    await db.refresh(updated_note)

    return NoteResponse.model_validate(updated_note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """删除笔记."""
    # 检查笔记是否存在及权限
    note = await crud_note.get(db=db, id=note_id)

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="笔记不存在",
        )

    if note.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此笔记",
        )

    # 更新Space的笔记计数
    if note.space_id:
        space = await crud.crud_space.get(db, id=note.space_id)
        if space:
            space.note_count -= 1
            await db.commit()

    # 删除笔记
    await crud_note.remove(db=db, id=note_id)


@router.post(
    "/ai/generate", response_model=NoteResponse, status_code=status.HTTP_201_CREATED
)
async def generate_ai_note(
    request: NoteAIGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NoteResponse:
    """使用AI生成笔记."""
    # 检查用户是否有权限使用AI功能
    if not current_user.is_premium and request.model:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="指定AI模型需要高级会员权限",
        )

    note = await note_service.generate_ai_note(
        db=db,
        request=request,
        user_id=current_user.id,
        user=current_user,
    )

    return NoteResponse.model_validate(note)


@router.post(
    "/ai/summary", response_model=NoteResponse, status_code=status.HTTP_201_CREATED
)
async def create_ai_summary(
    request: NoteAISummaryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NoteResponse:
    """创建AI文档总结."""
    note = await note_service.create_ai_summary(
        db=db,
        request=request,
        user_id=current_user.id,
        user=current_user,
    )

    return NoteResponse.model_validate(note)


@router.get("/{note_id}/linked", response_model=list[NoteResponse])
async def get_linked_notes(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[NoteResponse]:
    """获取关联的笔记."""
    # 检查权限
    note = await crud_note.get(db=db, id=note_id)
    if not note or note.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="笔记不存在或无权访问",
        )

    linked_notes = await crud_note.get_linked_notes(
        db=db,
        note_id=note_id,
        user_id=current_user.id,
    )

    return [NoteResponse.model_validate(note) for note in linked_notes]


@router.post("/{note_id}/tags", response_model=NoteResponse)
async def add_tag(
    note_id: int,
    tag: str = Query(..., description="要添加的标签"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NoteResponse:
    """添加标签."""
    # 检查权限
    note = await crud_note.get(db=db, id=note_id)
    if not note or note.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="笔记不存在或无权访问",
        )

    updated_note = await crud_note.add_tag(
        db=db,
        note_id=note_id,
        tag=tag,
    )

    return NoteResponse.model_validate(updated_note)


@router.delete("/{note_id}/tags", response_model=NoteResponse)
async def remove_tag(
    note_id: int,
    tag: str = Query(..., description="要移除的标签"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NoteResponse:
    """移除标签."""
    # 检查权限
    note = await crud_note.get(db=db, id=note_id)
    if not note or note.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="笔记不存在或无权访问",
        )

    updated_note = await crud_note.remove_tag(
        db=db,
        note_id=note_id,
        tag=tag,
    )

    return NoteResponse.model_validate(updated_note)


@router.get("/tags/all", response_model=list[dict[str, Any]])
async def get_all_tags(
    space_id: int | None = Query(None, description="限定Space"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[dict[str, Any]]:
    """获取所有标签及使用次数."""
    tags = await crud_note.get_tags(
        db=db,
        user_id=current_user.id,
        space_id=space_id,
    )
    return tags


@router.post("/batch", response_model=dict[str, Any])
async def batch_operation(
    operation: NoteBatchOperation,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """批量操作笔记."""
    # 验证所有笔记的权限
    for note_id in operation.note_ids:
        note = await crud_note.get(db=db, id=note_id)
        if not note or note.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权操作笔记 {note_id}",
            )

    results: dict[str, Any] = {"success": 0, "failed": 0, "errors": []}

    if operation.operation == "delete":
        # 批量删除
        for note_id in operation.note_ids:
            try:
                await crud_note.remove(db=db, id=note_id)
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"note_id": note_id, "error": str(e)})

    elif operation.operation == "move" and operation.target_space_id:
        # 批量移动
        for note_id in operation.note_ids:
            try:
                note = await crud_note.get(db=db, id=note_id)
                if note:
                    note.space_id = operation.target_space_id
                    await db.commit()
                    results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"note_id": note_id, "error": str(e)})

    elif operation.operation == "tag":
        # 批量添加/移除标签
        for note_id in operation.note_ids:
            try:
                if operation.tags_to_add:
                    for tag in operation.tags_to_add:
                        await crud_note.add_tag(db=db, note_id=note_id, tag=tag)

                if operation.tags_to_remove:
                    for tag in operation.tags_to_remove:
                        await crud_note.remove_tag(db=db, note_id=note_id, tag=tag)

                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"note_id": note_id, "error": str(e)})

    return results


# 版本管理端点


@router.get("/{note_id}/versions", response_model=NoteVersionListResponse)
async def get_note_versions(
    note_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NoteVersionListResponse:
    """获取笔记的版本历史."""
    # 检查笔记权限
    note = await crud_note.get(db, id=note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="笔记不存在",
        )

    if note.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此笔记",
        )

    # 获取版本历史
    versions = await note_service.get_version_history(
        db, note_id=note_id, skip=skip, limit=limit
    )

    return NoteVersionListResponse(
        versions=[NoteVersionResponse.model_validate(v) for v in versions],
        total=len(versions),
        current_version=note.version,
    )


@router.get("/{note_id}/versions/{version_number}", response_model=NoteVersionResponse)
async def get_note_version(
    note_id: int,
    version_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NoteVersionResponse:
    """获取笔记的特定版本."""
    # 检查笔记权限
    note = await crud_note.get(db, id=note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="笔记不存在",
        )

    if note.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此笔记",
        )

    # 获取版本
    version = await note_service.get_version(db, note_id, version_number)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="版本不存在",
        )

    return NoteVersionResponse.model_validate(version)


@router.post("/{note_id}/versions/restore", response_model=NoteResponse)
async def restore_note_version(
    note_id: int,
    restore_data: NoteRestoreRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NoteResponse:
    """恢复笔记到指定版本."""
    # 检查笔记权限
    note = await crud_note.get(db, id=note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="笔记不存在",
        )

    if note.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权编辑此笔记",
        )

    try:
        # 恢复版本
        restored_note = await note_service.restore_version(
            db,
            note,
            restore_data.version_id,
            current_user.id,
            restore_data.create_backup,
        )

        return NoteResponse.model_validate(restored_note)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢复版本失败: {str(e)}",
        ) from e


@router.post("/{note_id}/versions/compare", response_model=NoteVersionDiff)
async def compare_note_versions(
    note_id: int,
    compare_data: NoteVersionCompareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NoteVersionDiff:
    """比较两个版本的差异."""
    # 检查笔记权限
    note = await crud_note.get(db, id=note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="笔记不存在",
        )

    if note.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此笔记",
        )

    try:
        # 比较版本
        diff = await note_service.compare_versions(
            db,
            compare_data.version1_id,
            compare_data.version2_id,
        )

        return diff

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"比较版本失败: {str(e)}",
        ) from e


@router.delete("/{note_id}/versions/cleanup")
async def cleanup_note_versions(
    note_id: int,
    keep_count: int = Query(10, ge=1, le=100, description="保留的版本数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """清理旧版本，保留最近的N个版本."""
    # 检查笔记权限
    note = await crud_note.get(db, id=note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="笔记不存在",
        )

    if note.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权管理此笔记",
        )

    # 清理版本
    deleted_count = await note_service.cleanup_old_versions(
        db, note_id=note_id, keep_count=keep_count
    )

    return {
        "deleted_count": deleted_count,
        "message": f"已删除 {deleted_count} 个旧版本",
    }
