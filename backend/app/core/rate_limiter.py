"""Rate limiter for API usage control."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import UsageLog, User

logger = logging.getLogger(__name__)


class RateLimiter:
    """速率限制器."""

    def __init__(self) -> None:
        self.free_user_limit = settings.RATE_LIMIT_FREE_USER
        self.premium_user_limit = settings.RATE_LIMIT_PREMIUM_USER

    async def check_user_limit(
        self,
        user_id: int,
        action: str,
        db: AsyncSession,
    ) -> None:
        """检查用户使用限制."""
        # 获取用户信息
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )

        # 检查每日使用限制
        today = datetime.now(UTC).date()

        # 获取今日使用量
        usage_query = select(func.count(UsageLog.id)).where(
            and_(
                UsageLog.user_id == user_id,
                UsageLog.action == action,
                func.date(UsageLog.created_at) == today,
            )
        )
        usage_result = await db.execute(usage_query)
        daily_usage = usage_result.scalar() or 0

        # 确定用户限制
        user_limit = (
            self.premium_user_limit if user.is_premium else self.free_user_limit
        )

        if daily_usage >= user_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"今日{action}使用次数已达上限({user_limit}次)，请明天再试或升级会员",
            )

    async def increment_usage(
        self,
        user_id: int,
        action: str,
        db: AsyncSession,
        resource_type: str | None = None,
        resource_id: int | None = None,
        model: str | None = None,
        provider: str | None = None,
        token_count: int | None = None,
        cost: float | None = None,
    ) -> None:
        """增加使用量记录."""
        try:
            usage_log = UsageLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                model=model,
                provider=provider,
                token_count=token_count,
                cost=cost,
            )

            db.add(usage_log)
            await db.commit()

            # 更新用户的每日使用量
            await self._update_user_daily_usage(user_id, db)

        except Exception as e:
            await db.rollback()
            # 记录日志但不抛出异常，避免影响主要功能
            logger.error(f"Failed to record usage: {e}")

    async def _update_user_daily_usage(
        self,
        user_id: int,
        db: AsyncSession,
    ) -> None:
        """更新用户每日使用量."""
        try:
            # 获取用户
            user_query = select(User).where(User.id == user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if not user:
                return

            today = datetime.now(UTC).date()

            # 检查是否需要重置每日使用量
            if not user.last_reset_date or user.last_reset_date != today:
                user.daily_usage = 0
                user.last_reset_date = datetime.combine(
                    today, datetime.min.time()
                ).replace(tzinfo=UTC)

            # 获取今日总使用量
            usage_query = select(func.count(UsageLog.id)).where(
                and_(
                    UsageLog.user_id == user_id, func.date(UsageLog.created_at) == today
                )
            )
            usage_result = await db.execute(usage_query)
            daily_usage = usage_result.scalar() or 0

            user.daily_usage = daily_usage
            await db.commit()

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update daily usage: {e}")

    async def get_user_usage_stats(
        self,
        user_id: int,
        db: AsyncSession,
        days: int = 30,
    ) -> dict[str, Any]:
        """获取用户使用统计."""
        try:
            start_date = datetime.now(UTC) - timedelta(days=days)

            # 获取使用记录
            usage_query = (
                select(UsageLog)
                .where(
                    and_(UsageLog.user_id == user_id, UsageLog.created_at >= start_date)
                )
                .order_by(UsageLog.created_at.desc())
            )

            usage_result = await db.execute(usage_query)
            usage_logs = usage_result.scalars().all()

            # 统计数据
            stats = {
                "total_requests": len(usage_logs),
                "total_tokens": sum(log.token_count or 0 for log in usage_logs),
                "total_cost": sum(log.cost or 0 for log in usage_logs),
                "actions": {},
                "models": {},
                "providers": {},
                "daily_usage": {},
            }

            # 按行为分类
            for log in usage_logs:
                # 行为统计
                if log.action not in stats["actions"]:
                    stats["actions"][log.action] = 0
                stats["actions"][log.action] += 1

                # 模型统计
                if log.model and log.model not in stats["models"]:
                    stats["models"][log.model] = 0
                if log.model:
                    stats["models"][log.model] += 1

                # 提供商统计
                if log.provider and log.provider not in stats["providers"]:
                    stats["providers"][log.provider] = 0
                if log.provider:
                    stats["providers"][log.provider] += 1

                # 每日使用量
                day_key = log.created_at.date().isoformat()
                if day_key not in stats["daily_usage"]:
                    stats["daily_usage"][day_key] = 0
                stats["daily_usage"][day_key] += 1

            return stats

        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "actions": {},
                "models": {},
                "providers": {},
                "daily_usage": {},
            }

    async def reset_user_daily_usage(
        self,
        user_id: int,
        db: AsyncSession,
    ) -> None:
        """重置用户每日使用量（管理员功能）."""
        try:
            user_query = select(User).where(User.id == user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if user:
                user.daily_usage = 0
                user.last_reset_date = datetime.now(UTC).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                await db.commit()

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"重置使用量失败: {str(e)}",
            ) from e


# 全局实例
rate_limiter = RateLimiter()
