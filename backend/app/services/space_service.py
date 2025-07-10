"""Space management service."""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.models.models import Space, User
from app.schemas.spaces import SpaceCreate, SpaceUpdate


class SpaceService:
    """空间管理服务."""

    @staticmethod
    async def create_space(
        db: AsyncSession, space_data: SpaceCreate, user: User
    ) -> Space:
        """创建新空间."""
        # 检查是否已存在同名空间
        existing = await crud.space.get_by_name(
            db, name=space_data.name, user_id=user.id
        )
        if existing:
            raise ValueError(f"空间名称 '{space_data.name}' 已存在")
        
        # 创建空间
        return await crud.space.create(db, obj_in=space_data, user_id=user.id)

    @staticmethod
    async def get_user_spaces(
        db: AsyncSession, user: User, skip: int = 0, limit: int = 20
    ) -> List[Space]:
        """获取用户的空间列表."""
        return await crud.space.get_user_spaces(
            db, user_id=user.id, skip=skip, limit=limit
        )

    @staticmethod
    async def get_space_by_id(
        db: AsyncSession, space_id: int, user: User
    ) -> Optional[Space]:
        """根据ID获取空间."""
        space = await crud.space.get(db, id=space_id)
        
        # 检查权限
        if space and space.user_id == user.id:
            return space
        
        # 检查是否是公开空间或有协作权限
        if space and space.is_public:
            return space
        
        # 检查协作权限
        if space:
            access = await crud.space.get_user_access(
                db, space_id=space_id, user_id=user.id
            )
            if access:
                return space
        
        return None

    @staticmethod
    async def update_space(
        db: AsyncSession, space: Space, space_data: SpaceUpdate
    ) -> Space:
        """更新空间信息."""
        return await crud.space.update(db, db_obj=space, obj_in=space_data)

    @staticmethod
    async def delete_space(db: AsyncSession, space: Space) -> bool:
        """删除空间."""
        await crud.space.remove(db, id=space.id)
        return True

    @staticmethod
    async def count_user_spaces(db: AsyncSession, user: User) -> int:
        """统计用户空间数量."""
        from sqlalchemy import select, func
        from app.models.models import Space
        
        query = select(Space).where(Space.user_id == user.id)
        return await crud.space.get_count(db, query=query)

    @staticmethod
    async def update_space_stats(
        db: AsyncSession,
        space_id: int,
        document_delta: int = 0,
        note_delta: int = 0,
        size_delta: int = 0,
    ) -> Optional[Space]:
        """更新空间统计信息."""
        return await crud.space.update_stats(
            db,
            space_id=space_id,
            document_delta=document_delta,
            note_delta=note_delta,
            size_delta=size_delta,
        )