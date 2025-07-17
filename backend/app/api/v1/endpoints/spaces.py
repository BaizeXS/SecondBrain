"""Space endpoints v2 - 使用服务层和CRUD层的完整版本."""


from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.models import User
from app.schemas.spaces import (
    SpaceCreate,
    SpaceDetail,
    SpaceListResponse,
    SpaceResponse,
    SpaceUpdate,
)
from app.services import SpaceService

router = APIRouter()


@router.post("/", response_model=SpaceResponse, status_code=status.HTTP_201_CREATED)
async def create_space(
    space_data: SpaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SpaceResponse:
    """创建新的知识空间."""
    try:
        # 检查用户空间数量限制
        space_count = await SpaceService.count_user_spaces(db, current_user)
        max_spaces = 10 if current_user.is_premium else 5

        if space_count >= max_spaces:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"已达到空间数量上限（{max_spaces}个）",
            )

        # 创建空间
        space = await SpaceService.create_space(db, space_data, current_user)
        return SpaceResponse.model_validate(space)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建空间失败: {str(e)}",
        )


@router.get("/", response_model=SpaceListResponse)
async def get_spaces(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    search: str | None = Query(None, description="搜索关键词"),
    tags: list[str] | None = Query(None, description="标签筛选"),
    is_public: bool | None = Query(None, description="是否公开"),
    include_public: bool = Query(False, description="是否包含公开空间"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SpaceListResponse:
    """获取用户的知识空间列表."""
    # 获取用户空间
    if include_public:
        spaces = await crud.crud_space.get_user_spaces(
            db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            include_public=True,
        )
    else:
        spaces = await SpaceService.get_user_spaces(db, current_user, skip, limit)

    # 应用筛选条件
    if search:
        spaces = [s for s in spaces if search.lower() in s.name.lower() or (s.description and search.lower() in s.description.lower())]

    if tags:
        spaces = [s for s in spaces if s.tags and any(tag in s.tags for tag in tags)]

    if is_public is not None:
        spaces = [s for s in spaces if s.is_public == is_public]

    # 获取总数
    total = len(spaces)

    return SpaceListResponse(
        spaces=[SpaceResponse.model_validate(space) for space in spaces],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        has_next=total > skip + limit,
    )


@router.get("/{space_id}", response_model=SpaceDetail)
async def get_space(
    space_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SpaceDetail:
    """获取知识空间详情."""
    space = await SpaceService.get_space_by_id(db, space_id, current_user)

    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="空间不存在或无权访问",
        )

    return SpaceDetail.model_validate(space)


@router.put("/{space_id}", response_model=SpaceResponse)
async def update_space(
    space_id: int,
    space_data: SpaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SpaceResponse:
    """更新知识空间信息."""
    # 获取空间
    space = await crud.crud_space.get(db, id=space_id)

    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="空间不存在",
        )

    # 检查权限
    if space.user_id != current_user.id:
        # 检查是否有编辑权限
        access = await crud.crud_space.get_user_access(
            db, space_id=space_id, user_id=current_user.id
        )
        if not access or not access.can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权编辑此空间",
            )

    # 更新空间
    try:
        updated_space = await SpaceService.update_space(db, space, space_data)
        return SpaceResponse.model_validate(updated_space)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新空间失败: {str(e)}",
        )


@router.delete("/{space_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_space(
    space_id: int,
    force: bool = Query(False, description="强制删除（包括所有关联数据）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """删除知识空间."""
    # 获取空间
    space = await crud.crud_space.get(db, id=space_id)

    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="空间不存在",
        )

    # 检查权限
    if space.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此空间",
        )

    # 检查是否有关联数据
    if not force:
        documents = await crud.crud_document.get_by_space(db, space_id=space_id, limit=1)
        if documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="空间中还有文档，请先删除文档或使用强制删除",
            )

    # 删除空间
    try:
        await SpaceService.delete_space(db, space)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除空间失败: {str(e)}",
        )
