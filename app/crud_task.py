from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import ImageTask


async def get_tasks_by_user(
    session: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
) -> Sequence[ImageTask]:
    """Return tasks for a user ordered by created_at desc with pagination."""

    stmt: Select[tuple[ImageTask]] = (
        select(ImageTask)
        .where(ImageTask.user_id == user_id)
        .order_by(ImageTask.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()

